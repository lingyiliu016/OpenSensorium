# T01 · 部署 MiniCPM-o 推理服务（4090，局域网可达）

- 里程碑：阶段 0（地基）
- 依赖：T00
- PRD 对应：§1.4 底座模型、§6.3 部署形态、FR-2M.1、§6.6 流格式、§12.1 算力档位
- 状态：⬜ 未开始

## 目标
在 **RTX4090 台式机**上把 MiniCPM-o 跑成一个**常驻推理服务**，笔记本上的 Core 经**局域网** API 即可访问（Core 硬件无关，§3.6）。这是"先把模型部署成服务"的第一款。

## 交付物
- [ ] `services/minicpm_o/` 部署目录：环境说明、启动脚本、`README.md`。
- [ ] 独立 conda/venv 环境（**不要**混进 `ai_frontiers_env`，模型栈依赖重）；记录 requirements/torch+cuda 版本。
- [ ] 一个 HTTP/WebSocket 服务封装：接受 §6.6 基线流（JPEG 帧 + 16kHz mono PCM16）与会话控制，返回模型输出（文本/音频 + 是否发声决策）。
- [ ] 健康检查端点 `GET /health`。
- [ ] `services/minicpm_o/smoke_test.py`：从笔记本对局域网地址发一帧+一句话，拿到响应。

## 实现要点（在 4090 上执行）
- 取权重：HF `openbmb/MiniCPM-o-4_5`（BF16；显存不足可用 gguf 量化版）。9B ≈ SigLip2+Whisper-medium+CosyVoice2+Qwen3-8B。
- 复用官方 demo（github.com/OpenBMB/MiniCPM-o-Demo）的 `streaming_prefill`/`streaming_generate` 全双工路径；用它的 gateway→worker WebSocket 形态，或自己薄封装成 HTTP+WS。
- 视频：PIL 图 ≤~180万像素、≤10fps、`stack_frames`；音频：16kHz mono PCM，1s/块（`MIN_AUDIO_SAMPLES=16000`）。原生语音进/出（native TTS，ref_audio 16kHz mono）。
- **绑定 0.0.0.0** 并放行 Windows 防火墙端口，笔记本才能连；记录 `http://<4090-ip>:<port>` 到 Core 的 `config.local.yaml`。
- 记录**显存占用与常开 ~1Hz 决策的算力**，回填 PRD §12.1。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：写服务封装（HTTP/WS）、启动脚本、`smoke_test.py`、`services/minicpm_o/README.md` 部署文档。
- **人（在 4090 台式机操作）**：
  1. 建独立环境：`conda create -n minicpm_o python=3.10 && conda activate minicpm_o`，装 torch+cuda 与 demo 依赖。
  2. 取权重：`huggingface-cli download openbmb/MiniCPM-o-4_5 --local-dir ./weights/minicpm-o`（显存不足用 gguf 量化版）。
  3. 启动服务（绑 `0.0.0.0`），Windows 放行端口：`New-NetFirewallRule -DisplayName "minicpm-o" -Direction Inbound -LocalPort <port> -Protocol TCP -Action Allow`。
  4. 记录 `http://<4090-ip>:<port>` 到笔记本 Core 的 `config.local.yaml`。
  5. **从笔记本**跑 `smoke_test.py` 验证跨机连通；记录显存/延迟回填 PRD §12.1。

## 验收标准（可验证）
- [ ] 4090 上服务启动，`GET /health` 返回 200。
- [ ] **从笔记本**（不同机器）跑 `smoke_test.py`：发送一张截图 JPEG + 一段 1s PCM，收到模型文本（和/或音频）响应，端到端无异常。
- [ ] 连续送 30s 视频帧流（~1fps）不崩、显存不泄漏；记录一次典型延迟与显存数字进 `services/minicpm_o/README.md`。
- [ ] 服务地址、端口、启动命令、依赖版本在 `README.md` 中可复现。

> ⚠️ 需人工验证：显存/延迟数字与"局域网跨机连通"由你在 4090+笔记本上实测确认。

## Git
- 分支：`feat/t01-minicpm-service`
- 提交：`git commit -m "T01: MiniCPM-o 推理服务部署与局域网连通"`（权重不入库，见 .gitignore）
- 完成并实测通过后改状态 ✅。
