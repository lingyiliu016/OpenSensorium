# T25 · CI + 共享 mock 推理服务 / 测试夹具

- 里程碑：阶段 0（地基，贯穿全程）
- 依赖：T00、T03（接口成型后落地；可先建骨架）
- PRD 对应：NFR 可观测、FR-2M（契约测试）、贯穿所有任务的"自带测试"要求
- 状态：⬜ 未开始

## 目标
支撑"每个任务自带单元/集成/回归测试"这条硬约定：提供一个**不依赖 4090、不加载真权重**的**假模型推理服务**与共享测试夹具，让绝大多数任务的自动化测试可离线跑；并搭好 **CI**，每次提交自动跑全量测试 + lint，防回归。

## 交付物
- [ ] `tests/fakes/mock_inference.py`：假推理服务，实现与 T03 `ModelAdapter` 对接的两种能力剖面——
  - `native-speech`（模拟 MiniCPM-o：直接出音频/文本 + ~1Hz 发声决策）
  - `external-asr-tts`（模拟 JoyAI：`</silence>/</response>/</delegate>` 信号 + 假 ASR/TTS）
  - 可脚本化返回（给定输入→预置输出），供确定性断言。
- [ ] `tests/fakes/mock_endpoint.py`：假采集源（可注入预置帧/音频）、假执行器（记录收到的动作，供断言）。
- [ ] `tests/conftest.py`：pytest 共享夹具（事件总线、mock adapter/endpoint、临时存储目录）。
- [ ] `pytest` 分层标记：`unit` / `integration`（需 4090）/ `regression`；默认只跑不依赖硬件的。
- [ ] CI：`.github/workflows/ci.yml`——在 push/PR 上装依赖、`ruff check`、`mypy`（可选）、`pytest -m "not integration"`。
- [ ] `tests/test_mock_inference.py`：mock 服务自身的自测。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 mock 服务/端/夹具、pytest 标记、CI 工作流 + 自测；保证 `pytest -m "not integration"` 在本机与 CI 均绿。
- **人**：确认 CI 在 GitHub Actions 上跑通（首次可能需在仓库设置里允许 Actions）；决定是否加 `integration`（连 4090）的自托管 runner。

## 实现要点
- mock 服务要**紧贴 T03 契约**：真 Adapter 与 mock 走同一 `ModelAdapter` 接口，测试才有意义（新增真模型时也能先对 mock 写测试）。
- 确定性优先：mock 输出可预置，避免 flaky 测试（回归测试的基础）。
- CI 不碰权重、不连 4090；`integration` 类测试标记出来、本地或自托管 runner 手动跑。

## 验收标准（可验证）
- [ ] `conda run -n ai_frontiers_env pytest -m "not integration"` 全绿，且**不需要** 4090 或真权重。
- [ ] `tests/test_mock_inference.py`：mock 的两种能力剖面都能被 T03 契约测试消费并通过。
- [ ] CI 在 GitHub 上对一次 push 自动跑并通过（lint + 单元/回归测试）。
- [ ] 任一后续任务的测试都能复用 `conftest.py` 夹具，无需各自造假件。

## Git
- 分支：`feat/t25-ci-harness`
- 提交：`git commit -m "T25: CI + 共享 mock 推理服务/测试夹具"`
- 完成后改状态 ✅。
