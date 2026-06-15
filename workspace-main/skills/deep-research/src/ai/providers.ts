import { createOpenAI } from '@ai-sdk/openai';
import { generateObject as aiGenerateObject } from 'ai';
import { getEncoding } from 'js-tiktoken';
import { z } from 'zod';

import { RecursiveCharacterTextSplitter } from './text-splitter';
import { AI_TIMEOUT_HEAVY_MS } from '../constants';

// Providers

const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL,
});

// Models - 使用鲸云可用模型 (OpenAI 兼容接口)
// 默认 deepseek-v4-pro，可通过环境变量 DEEP_RESEARCH_MODEL 指定其他模型
const modelName = process.env.DEEP_RESEARCH_MODEL || 'deepseek-v4-pro';
export const primaryModel = openai(modelName, { structuredOutputs: false });
/** @deprecated Use primaryModel instead */
export const o3MiniModel = primaryModel;

const MinChunkSize = 140;
const encoder = getEncoding('o200k_base');

/**
 * 容错包装器：对 generateObject 增加自动重试 + 降级解析
 *
 * 问题：GLM-5.1 等模型有时通过 tool calls 返回而非纯文本 JSON，
 * 导致 NoObjectGeneratedError / TypeValidationError。
 *
 * 策略：
 * 1. 首次失败时，尝试从 error.text 提取 JSON 并手动校验
 * 2. 若提取失败或校验失败，重试（最多 3 次），重试时增加强制指令
 * 3. 重试间隔指数退避
 */
export async function generateObjectWithRetry<T>(params: {
  model: any;
  system?: string;
  prompt: string;
  schema: z.ZodSchema<T>;
  retries?: number;
  timeoutMs?: number;
  // NOTE: abortSignal 不穿透到底层 generateObject，因为它是单次消费的。
  // 重试包装器自身提供超时保护，见 timeoutMs。
}): Promise<{ object: T; usage?: any }> {
  const maxRetries = params.retries ?? 3;
  const perCallTimeoutMs = params.timeoutMs ?? AI_TIMEOUT_HEAVY_MS;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await aiGenerateObject({
        model: params.model,
        system: params.system,
        prompt:
          attempt > 0
            ? `${params.prompt}\n\n[RETRY ${attempt + 1}/${maxRetries}] CRITICAL: You MUST respond with a VALID JSON object ONLY. Do NOT use tool calls. Do NOT include any text outside the JSON.`
            : params.prompt,
        schema: params.schema,
        abortSignal: AbortSignal.timeout(perCallTimeoutMs),
      });
      return { object: res.object as T, usage: res.usage };
    } catch (err: any) {
      if (err.name === 'AbortError' || err.message?.includes('abort')) {
        console.warn(`[generateObject] Attempt ${attempt + 1} timed out after ${perCallTimeoutMs / 1000}s`);
        lastError = err;
        if (attempt < maxRetries - 1) {
          const delay = [1000, 3000, 5000][attempt] || 5000;
          await new Promise(r => setTimeout(r, delay));
          continue;
        }
        throw new Error(`generateObjectWithRetry: all ${maxRetries} attempts timed out`);
      }
      lastError = err;

      // 检查 error.text / response 消息中是否包含可恢复的 JSON
      const text = err?.text || err?.response?.text;
      // 也尝试从 response.choices[0].message.content 获取
      const responseContent =
        err?.response?.choices?.[0]?.message?.content ||
        err?.response?.messages?.[err?.response?.messages?.length - 1]?.content;
      const recoverableText = text || (
        Array.isArray(responseContent)
          ? responseContent.map((p: any) => p?.text || '').join('')
          : typeof responseContent === 'string' ? responseContent : null
      );
      if (recoverableText) {
        try {
          const jsonMatch = recoverableText.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            const validated = params.schema.parse(parsed);
            console.warn(`[generateObject] Attempt ${attempt + 1}: recovered from error (text fallback)`);
            return { object: validated as T };
          }
        } catch {
          // JSON 提取或校验失败，继续重试
        }
      }

      // TypeValidationError 可能有 value 属性，尝试回退解析
      const typeErr = err as any;
      if (typeErr?.value && typeof typeErr.value === 'object') {
        try {
          const validated = params.schema.parse(typeErr.value);
          console.warn(`[generateObject] Attempt ${attempt + 1}: recovered from TypeValidationError`);
          return { object: validated as T };
        } catch {
          // 校验仍然失败，继续重试
        }
      }

      if (attempt < maxRetries - 1) {
        const delay = [1000, 3000, 5000][attempt] || 5000;
        console.warn(`[generateObject] Attempt ${attempt + 1} failed (${err.name || 'error'}), retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }

  throw lastError || new Error('generateObjectWithRetry: all retries exhausted');
}

// trim prompt to maximum context size
export function trimPrompt(prompt: string, contextSize = 120_000) {
  if (!prompt) {
    return '';
  }

  const length = encoder.encode(prompt).length;
  if (length <= contextSize) {
    return prompt;
  }

  const overflowTokens = length - contextSize;
  // on average it's 3 characters per token, so multiply by 3 to get a rough estimate of the number of characters
  const chunkSize = prompt.length - overflowTokens * 3;
  if (chunkSize < MinChunkSize) {
    return prompt.slice(0, MinChunkSize);
  }

  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize,
    chunkOverlap: 0,
  });
  const trimmedPrompt = splitter.splitText(prompt)[0] ?? '';

  // last catch, there's a chance that the trimmed prompt is same length as the original prompt, due to how tokens are split & innerworkings of the splitter, handle this case by just doing a hard cut
  if (trimmedPrompt.length === prompt.length) {
    return trimPrompt(prompt.slice(0, chunkSize), contextSize);
  }

  // recursively trim until the prompt is within the context size
  return trimPrompt(trimmedPrompt, contextSize);
}
