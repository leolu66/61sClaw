/**
 * 全局常量
 * 统一管理散落在各模块中的 Magic Numbers
 */

// ─── Token 截断阈值 ──────────────────────────────

/** 单个搜索结果内容的最大 token 数 */
export const SEARCH_RESULT_MAX_TOKENS = 25_000;

/** Legacy 模式下所有 learnings 的最大 token 数 */
export const ALL_LEARNINGS_MAX_TOKENS = 150_000;

/** 报告逐章生成时，单章 learnings 的最大 token 数 */
export const CHAPTER_LEARNINGS_MAX_TOKENS = 80_000;

/** 素材收集模块中，所有素材内容的最大 token 数 */
export const SOURCE_MATERIALS_MAX_TOKENS = 120_000;

// ─── AI 生成默认数量 ──────────────────────────────

/** 单次搜索后提取的最大 learnings 数 */
export const DEFAULT_NUM_LEARNINGS = 3;

/** 单次搜索后生成的最大后续问题数 */
export const DEFAULT_NUM_FOLLOW_UP_QUESTIONS = 3;

/** 单次生成的 SERP 查询数 */
export const DEFAULT_NUM_SERP_QUERIES = 3;

// ─── 搜索监控 ─────────────────────────────────────

/** 搜索成功率告警阈值（百分比），低于此值时输出告警 */
export const SEARCH_SUCCESS_RATE_WARN_THRESHOLD = 50;

/** 搜索成功率统计的最小样本数（避免少量请求就告警） */
export const SEARCH_MONITOR_MIN_SAMPLES = 5;

// ─── 并发与超时 ───────────────────────────────────

/** 默认搜索并发数 */
export const DEFAULT_CONCURRENCY = 3;

/** 最大搜索并发数 */
export const MAX_CONCURRENCY = 10;

/** AI 调用默认超时（毫秒）—— 轻量任务 */
export const AI_TIMEOUT_LIGHT_MS = 60_000;

/** AI 调用默认超时（毫秒）—— 标准任务 */
export const AI_TIMEOUT_STANDARD_MS = 120_000;

/** AI 调用默认超时（毫秒）—— 报告生成等重任务 */
export const AI_TIMEOUT_HEAVY_MS = 180_000;

// ─── 缓存 ─────────────────────────────────────────

/** 默认搜索缓存 TTL（秒），24 小时 */
export const DEFAULT_CACHE_TTL_SECONDS = 86400;
