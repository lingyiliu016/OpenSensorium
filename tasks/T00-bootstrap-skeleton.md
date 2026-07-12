# T00 · 仓库骨架 / 配置 / 日志 / 事件与意图数据模型

- 里程碑：阶段 0（地基）
- 依赖：—
- PRD 对应：§6.1 分层职责、NFR 可观测、§6.2 数据面
- 状态：🟡 进行中（代码+单测全绿，待人验收核心数据模型后转 ✅）

## 目标
搭好可持续开发的 Python 骨架：包结构、配置加载、结构化日志、以及贯穿全系统的**核心数据模型**（感知事件、意图、能力剖面）。让后续每个任务都能直接复用，不各写各的。

## 交付物
- [ ] `src/opensensorium/` 各子包目录 + `__init__.py`（bus/core/inference/endpoint/effector/delegate/memory/scheduler/skills/channel/safety）。
- [ ] `src/opensensorium/config.py`：从 `config.yaml` + 环境变量加载（含推理服务地址等）。
- [ ] `src/opensensorium/logging.py`：loguru 结构化日志（含 run id、时间戳）。
- [ ] `src/opensensorium/schemas.py`：pydantic 模型——
  - `PerceptionEvent`（source_id、modality、timestamp、payload、seq）
  - `Intent`（type: say/act/delegate/silent，payload）
  - `CapabilityProfile`（模型/执行器/端的能力协商通用结构）
- [ ] `config.example.yaml`：可复制的配置样例（推理 base_url、采样率等）。
- [ ] `tests/test_schemas.py`。

## 实现要点
- 统一时间戳用单调时钟 + 挂钟对照，方便跨模态对齐（FR-1.5）。
- `CapabilityProfile` 设计成模型/执行器/端**共用**同一协商机制（PRD 强调三处能力协商同构）。
- 配置分层：`config.yaml`（提交）→ `config.local.yaml`（gitignore）→ 环境变量覆盖。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现全部骨架代码 + 单元测试，跑通 lint/pytest。
- **人**：审核核心数据模型（`PerceptionEvent/Intent/CapabilityProfile`）是否够用——后续所有任务都依赖它，这里定得好省很多返工。

## 验收标准（可验证）
- [ ] `conda run -n ai_frontiers_env pip install -e ".[dev]"` 成功。
- [ ] `conda run -n ai_frontiers_env python -c "import opensensorium; print(opensensorium.__version__)"` 输出 `0.0.1`。
- [ ] `conda run -n ai_frontiers_env pytest tests/test_schemas.py` 全绿：构造/序列化 `PerceptionEvent`、`Intent`、`CapabilityProfile` 通过。
- [ ] `conda run -n ai_frontiers_env ruff check src tests` 无错误。
- [ ] 日志能输出一条带 run id 的结构化记录。

## Git
- 分支：`feat/t00-bootstrap`
- 提交：`git commit -m "T00: 项目骨架、配置、日志、核心数据模型"`
- 完成后把本文件与 `tasks/README.md` 状态改 ✅。
