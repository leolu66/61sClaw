# FunASR 模型参考

## 推荐模型

### SenseVoiceSmall（默认）
- **ModelScope**: `iic/SenseVoiceSmall`
- **参数量**: 234M
- **语言**: 中文、英文、日文、韩文、粤语
- **功能**: ASR + 情感检测 + 音频事件检测
- **速度**: GPU 170x 实时 / CPU 17x 实时
- **显存**: ~500MB
- **适用**: 日常语音转录，短音频

### Fun-ASR-Nano
- **HuggingFace**: `FunAudioLLM/Fun-ASR-Nano-2512`
- **参数量**: 800M
- **语言**: 31种语言（含中文方言）
- **功能**: ASR + 时间戳，LLM 解码精度最高
- **速度**: GPU 17x 实时 / CPU 3.6x 实时
- **适用**: 高精度需求，多语言场景

## 辅助模型（自动加载）

| 模型 | 用途 | 大小 |
|------|------|------|
| fsmn-vad | 语音活动检测（VAD分段） | 1.6M |
| cam++ | 说话人分离（Speaker Diarization） | 27M |
