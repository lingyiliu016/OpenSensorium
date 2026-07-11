# T03 · Model Adapter 框架 + 能力协商 + 两款视觉路径 Adapter

- 里程碑：阶段 0（地基）
- 依赖：T01、T02
- PRD 对应：FR-2M（全）、§6.3、§6.6
- 状态：⬜ 未开始

## 目标
在 Core 与两款推理服务之间建一层 **Model Adapter**：把各自的接口/流式协议/token 化封装到**统一接口**后面，Core 逻辑不随模型变；并通过**能力协商**声明各模型支持的实时能力（尤其 `native-speech` vs `external-asr-tts`）。

## 交付物
- [ ] `src/opensensorium/inference/base.py`：`ModelAdapter` 抽象接口——
  - `capabilities() -> CapabilityProfile`（视觉流/语音输入/语音双工·TTS/可打断/上下文长度/单多路…）
  - `open_session()` / `send_frame()` / `send_audio()` / `stream_outputs()`（归一成 Core 的 `Intent` 流：say/act/delegate/silent）/ `close()`
- [ ] `src/opensensorium/inference/minicpm_adapter.py`：连 T01 服务，语音架构 = `native-speech`。
- [ ] `src/opensensorium/inference/joyai_adapter.py`：连 T02 服务，语音架构 = `external-asr-tts`，封装 ASR/TTS/bg-agent；把 `</silence>/</response>/</delegate>` 归一为统一意图。
- [ ] `src/opensensorium/inference/registry.py`：按配置选/切 Adapter（FR-2M.4 运行时可切换）。
- [ ] 测试：`tests/test_adapter_contract.py`（两款跑同一套契约测试）。

## 实现要点
- **契约测试同构**：同一组输入（帧+音频）喂两个 Adapter，断言都产出合法 `Intent` 流——这是"完全兼容两款"的核心保证（FR-2M.1）。
- 能力协商差异要真实反映：MiniCPM-o `native-speech=true`；JoyAI `external-asr-tts=true` 且 `requires: [asr, tts, bg-agent]`。
- 新增模型只实现新 Adapter，Core/上层零改动（FR-2M.5）——用契约测试守住这一点。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 Adapter 抽象、两款 Adapter、registry、契约测试（用 mock 服务离线跑，不必占用 4090）。
- **人**：4090 两款服务在线时跑一次真实集成，确认归一后的 `Intent` 正确；确认运行时切换生效。

## 验收标准（可验证）
- [ ] `tests/test_adapter_contract.py` 对**两款 Adapter 均通过**同一套契约（可用 mock 服务离线跑，避免依赖 4090 常开）。
- [ ] 集成测试（4090 在线时）：两款各自 `open_session` → 送一帧一句 → 拿到归一后的 `Intent`。
- [ ] `registry` 能按配置在 MiniCPM-o / JoyAI 间切换，且切换后 Core 调用代码不变。
- [ ] `capabilities()` 正确反映两款的语音架构分歧。

## Git
- 分支：`feat/t03-model-adapter`
- 提交：`git commit -m "T03: Model Adapter 框架、能力协商、MiniCPM-o/JoyAI 双适配器"`
- 完成后改状态 ✅。
