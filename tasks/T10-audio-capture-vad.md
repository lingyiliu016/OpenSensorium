# T10 · 麦克风采集 + VAD（16kHz mono PCM16 ~1s 分块）

- 里程碑：M1
- 依赖：T04
- PRD 对应：FR-1.3、§6.6 音频基线
- 状态：⬜ 未开始

## 目标
把麦克风音频采成 §6.6 基线格式并做 VAD，产出"语音片段"感知事件，兼容 MiniCPM-o 原生音频与 JoyAI 的外部 ASR。

## 交付物
- [ ] `src/opensensorium/endpoint/windows/audio_capture.py`：`sounddevice` 采集，**16kHz 单声道 PCM16、~1s 分块**（16000 采样）、带时间戳。
- [ ] VAD（webrtcvad 或 silero-vad）：切出语音段，输出 `PerceptionEvent(modality=audio, is_speech=...)`。
- [ ] 上总线，时间戳与视频统一（供跨模态对齐）。
- [ ] 测试：`tests/test_audio_capture.py`（分块大小=16000、采样率、VAD 对静音/语音判定）。

## 实现要点
- 分块严格 1s / 16000 采样，直接满足 MiniCPM-o `MIN_AUDIO_SAMPLES`；JoyAI 侧由 Adapter 送 ASR。
- 时间戳走 T00 时钟，保证与视频帧对齐。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现麦克风采集、分块、VAD + 测试。
- **人**：实测说话/静音下 VAD 表现、麦克风设备选择。

## 验收标准（可验证）
- [ ] `tests/test_audio_capture.py` 全绿：分块为 16kHz/mono/PCM16/16000 采样；VAD 对含语音/纯静音片段判定正确。
- [ ] 集成：音频事件与视频事件在总线上时间戳可对齐（同一时钟）。
- [ ] 手动：说话时产出 is_speech 段，安静时不误触发。

## Git
- 分支：`feat/t10-audio-vad`
- 提交：`git commit -m "T10: 麦克风采集 + VAD（16kHz mono PCM16 基线）"`
- 完成后改状态 ✅。
