# T11 · 语音输出（TTS）+ barge-in 可打断

- 里程碑：M1
- 依赖：T09、T10
- PRD 对应：FR-3.2、FR-2.4
- 状态：⬜ 未开始

## 目标
让它能开口说话（流式 TTS），且**用户一开口就立刻停下听**（barge-in）。TTS 具体实现由 Adapter 决定：MiniCPM-o 原生出音频；JoyAI 经外部 Qwen3-TTS。

## 交付物
- [ ] `src/opensensorium/effector/voice.py`：`VoiceEffector`，流式播放 TTS 音频。
- [ ] TTS 来源分流：`native-speech`（MiniCPM-o 直接出音频）vs `external-asr-tts`（JoyAI→Qwen3-TTS）——统一在 Effector 后面（对应 T03 能力协商）。
- [ ] barge-in：订阅 T10 的 is_speech 事件，检测到用户开口 → **中止当前 TTS 播放与生成**，转倾听。
- [ ] 测试：`tests/test_barge_in.py`（注入语音事件时播放/生成被中止，中止延迟 <300ms）。

## 实现要点
- barge-in 中止延迟 < 300ms（NFR）。中止要同时停"播放"与"上游生成"。
- 两款语音架构差异对上层透明（Effector 统一）。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 VoiceEffector、两款 TTS 分流、barge-in 中止 + 测试。
- **人**：真人边听边打断，确认自然度与 <300ms 中止体感（两款各一次）。

## 验收标准（可验证）
- [ ] `tests/test_barge_in.py`：模拟用户开口 → TTS 播放与生成在 <300ms 内中止，状态转倾听。
- [ ] 集成（两款各一次）：能流式说出一段话；说话中打断能立即停。
- [ ] 手动：真人边听边打断，体验自然。

> ⚠️ 需人工验证：真实语音打断的自然度由你实测。

## Git
- 分支：`feat/t11-tts-barge-in`
- 提交：`git commit -m "T11: 流式 TTS 输出 + barge-in 可打断"`
- 完成后改状态 ✅。
