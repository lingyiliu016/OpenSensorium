# T02 · 部署 JoyAI-VL 推理服务（+Qwen3-ASR/TTS/background-agent）

- 里程碑：阶段 0（地基）
- 依赖：T00
- PRD 对应：§1.4、§6.6 流格式与语音分歧、§12.11、FR-2M.1
- 状态：⬜ 未开始

## 目标
在 **RTX4090 台式机**上把 JoyAI-VL-Interaction 跑成局域网推理服务。与 MiniCPM-o 的关键差异：**语音要外挂**（Qwen3-ASR + Qwen3-TTS + background-agent），需一并部署。

## 交付物
- [ ] `services/joyai_vl/` 部署目录：环境、启动脚本、`README.md`。
- [ ] 独立环境（vLLM 部署）。取权重 HF `jdopensource/JoyAI-VL-Interaction-Preview`（8B 标准 Qwen3-VL）。
- [ ] VL 主服务：**OpenAI 兼容 HTTP API**（webinfer，参考 :8070）+ WebRTC 收视频帧（JPEG ~1fps）。
- [ ] 外挂语音栈：**Qwen3-ASR**（PCM16→文本）、**Qwen3-TTS**（文本→PCM16，vLLM-Omni）；WebSocket 承载。
- [ ] background-agent 通道：接收模型 `</delegate>` 信号的下游（先留最小实现/占位，真正委派在 T16）。
- [ ] 健康检查 + `services/joyai_vl/smoke_test.py`（从笔记本发一帧 + 一句话，走 ASR→VL→TTS 全链）。

## 实现要点（在 4090 上执行）
- 决策信号：模型每帧输出 `</silence>`（不响应）/ `</response> 文本`（发声）/ `</delegate> 任务`。这三者要在响应里透传给 Core（T03 Adapter 归一）。
- 传输：WebRTC（视频）+ WebSocket（ASR/TTS）+ HTTP（推理），与官方 demo 一致；有 AdaCodec 预测编码可选。
- 视频基线：JPEG ~1fps ≤~180万像素，与 MiniCPM-o 取公约数一致（§6.6）。
- **绑定 0.0.0.0** + 防火墙放行；记录各服务端口到 Core 配置。
- 记录额外部署 ASR/TTS 的**显存/资源预算**，回填 PRD §12.11。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：写 VL/ASR/TTS 三服务的编排封装、启动脚本、`smoke_test.py`、`services/joyai_vl/README.md`。
- **人（在 4090 台式机操作）**：
  1. 建独立环境（vLLM）：`conda create -n joyai_vl python=3.10 && conda activate joyai_vl`，装 vLLM 与 JoyAI demo 依赖。
  2. 取权重：`huggingface-cli download jdopensource/JoyAI-VL-Interaction-Preview --local-dir ./weights/joyai-vl`；另备 Qwen3-ASR / Qwen3-TTS。
  3. 起三服务：VL 主服务（OpenAI 兼容 HTTP，参考 :8070）+ Qwen3-ASR + Qwen3-TTS(vLLM-Omni)，均绑 `0.0.0.0`，防火墙放行各端口。
  4. 端口写入笔记本 Core 的 `config.local.yaml`。
  5. **从笔记本**跑 `smoke_test.py` 验证 ASR→VL→TTS 全链；记录三服务显存回填 PRD §12.11。

## 验收标准（可验证）
- [ ] 4090 上 VL + ASR + TTS 三服务均起，健康检查通过。
- [ ] **从笔记本**跑 `smoke_test.py`：一段 1s PCM → ASR 得文本 → 连同一帧截图入 VL → 得 `</response>` 文本 → TTS 合成回 PCM，全链走通。
- [ ] 构造一个应触发委派的输入，观察到模型输出 `</delegate>` 信号并被透传（不要求真正执行）。
- [ ] 连续 30s ~1fps 帧流稳定；典型延迟与三服务显存占用记入 `README.md`。

> ⚠️ 需人工验证：多服务编排、跨机连通、资源占用由你实测确认。JoyAI 为 `Preview` 权重且依赖 Qwen3-ASR/TTS，商用许可复核见 PRD §12.13。

## Git
- 分支：`feat/t02-joyai-service`
- 提交：`git commit -m "T02: JoyAI-VL 推理服务 + Qwen3-ASR/TTS 外挂栈部署"`
- 完成并实测通过后改状态 ✅。
