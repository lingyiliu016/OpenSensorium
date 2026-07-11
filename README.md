# OpenSensorium

> 一个以**视觉为主、多模态并行**的「**持续感知 — 主动行动**」通用智能体。
> 近期以操纵电脑为最低成本验证场，**最终归宿是走进物理世界——操纵汽车、机器人、智能家居**。

完整设计见 [`PRD.md`](./PRD.md)。开发清单（每个需求一个文件、逐条可验收）见 [`tasks/`](./tasks/README.md)。

---

## 核心理念（一句话）

不是「给大模型接几个工具的回合制问答」，而是**给模型一套持续在线的感官与神经系统**——它一直在看、在听，自己决定何时说话、何时动手：
**传入（afferent，感知）→ 中枢（认知）→ 传出（efferent，行动）** 的不间断闭环。

底座模型：**MiniCPM-o** 与 **JoyAI-VL-Interaction** 两者完全兼容（经 Model Adapter），未来加模型只加 Adapter。

## 部署拓扑（当前家庭环境）

同一路由器下两台机器：

```
┌─ 笔记本 (本机) ────────────┐        局域网         ┌─ 台式机 RTX4090 ─────────┐
│  Core (认知核, 硬件无关)     │  ── HTTP/WS/WebRTC ──▶ │  Model Inference 服务     │
│  Endpoint (Windows 采集/键鼠) │ ◀──  推理 API   ──     │  MiniCPM-o / JoyAI-VL     │
│  本地呈现面 UI               │                        │  (+Qwen3-ASR/TTS for JoyAI)│
└──────────────────────────┘                        └──────────────────────────┘
```

- **Core 与 Endpoint** 跑在本笔记本；**模型推理**跑在 4090 台式机，经局域网 API 访问（Core 硬件无关，见 PRD §3.6）。
- 开发 Python 环境：**conda env `ai_frontiers_env`（Python 3.12）**。conda 在 PowerShell 可用。

## 快速开始（骨架期）

```powershell
conda activate ai_frontiers_env
pip install -e ".[dev,endpoint-windows]"
pytest        # 运行现有测试
ruff check src tests
```

模型推理服务部署（在 4090 台式机执行）见 `tasks/T01-*.md`、`tasks/T02-*.md`。

## 目录结构（目标布局）

```
opensensorium/
├─ PRD.md                     # 产品需求文档（唯一事实源）
├─ tasks/                     # 开发清单：每个需求一个文件，逐条可验收
├─ src/opensensorium/
│  ├─ bus/                    # 感知事件总线（统一时间戳）
│  ├─ core/                   # 认知核：工作记忆·注意力·意图（硬件无关）
│  ├─ inference/              # Model Adapter + 推理客户端（能力协商）
│  ├─ endpoint/               # 各平台端（采集+执行+权限）
│  │  └─ windows/             # v1 首平台
│  ├─ effector/              # 执行器（键鼠 → 未来云端/手机/物理世界）
│  ├─ delegate/              # 认知委派（Codex / Claude Code）
│  ├─ memory/                # 分层记忆 + 巩固 + 检索
│  ├─ scheduler/             # 定时/cron/条件触发
│  ├─ skills/                # 技能（符号工具 + 感知-运动）
│  ├─ channel/               # 通道（飞书优先）
│  └─ safety/                # 确认门·急停·审计·作用域·记忆隐私
├─ services/                  # 推理服务部署（在 4090 运行）
│  ├─ minicpm_o/
│  └─ joyai_vl/
├─ tests/
└─ scripts/
```

> 目录随任务推进逐步落地，不必一次建全。以 `tasks/` 为准，一个任务一个可验收单元。

## 开发工作流

1. 从 `tasks/README.md` 选一个**未开始**且依赖已满足的任务。
2. 开分支 `feat/tNN-<slug>`，按任务文件的「实现要点」实现。
3. 逐条对照「验收标准」自测通过。
4. 提交（见任务文件 Git 段），把该任务与 `tasks/README.md` 索引状态改为 ✅。

许可：Apache-2.0（与两款底座模型一致，商用前复核见 PRD §12.13）。
