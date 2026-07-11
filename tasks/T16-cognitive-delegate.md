# T16 · 认知委派框架 + CodexDelegate / ClaudeCodeDelegate（结构化、异步）

- 里程碑：M2.5
- 依赖：T09、T14
- PRD 对应：FR-3D、§3.5、§9.6
- 状态：⬜ 未开始

## 目标
弥补感知核在文本空间的短板：把写/改代码、长程符号推理**结构化外包**给文本智能体（Codex、Claude Code），**异步非阻塞**——派出任务后感知回路继续跑，结果回流作为感知事件。

## 交付物
- [ ] `src/opensensorium/delegate/base.py`：`Delegate` 接口——`capabilities()`（`code.write/code.fix/repo.refactor/longform.reason`）、`dispatch(task, context)->handle`（异步、立即返回句柄）、`poll(handle)/onResult(handle)`（结构化结果 patch/日志/成败）。
- [ ] `src/opensensorium/delegate/codex.py`、`claude_code.py`：经各自 CLI/API/MCP 结构化调用。
- [ ] `src/opensensorium/delegate/registry.py`：可插拔注册（FR-3D.4）。
- [ ] Delegate 产生的实际动作（改文件/跑命令）同样过 T14 Safety 层（FR-3D.5）。
- [ ] 测试：`tests/test_delegate.py`（异步派发不阻塞、结果回流、安全门）。

## 实现要点（务必守住术语/路径区分——用户两次澄清）
- **术语**：委派(Delegate)**只指结构化这一种**（sub-agent/API/CLI/MCP）。Delegate 接口**不含 `gui` 模式**。
- **路径**：达成"用外部编码工具"有**两条一等路径，都保留**：① 本任务的结构化委派（异步/非阻塞）；② **屏幕操作该工具**（走 Effector/FR-3.1，像人一样开窗操作 ClaudeCode/Codex/Cursor）——那条属 §9 原生 GUI 操作，**不在本任务**，不叫委派。
- 何时走屏幕操作：工具无可用 API；或工具本质是 GUI（如 Cursor 这类 IDE）像人一样用更自然。
- **不要把 GUI 路径写成"仅无 API 的兜底"**——它是一等路径。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 Delegate 抽象、CodexDelegate、ClaudeCodeDelegate、registry + 异步/安全测试。
- **人**：配置 Codex/Claude Code 的 CLI/API 凭证（放 `config.local.yaml`，勿入库）；确认异步不阻塞、结果回流。

## 验收标准（可验证）
- [ ] `tests/test_delegate.py`：`dispatch` 立即返回句柄且**不阻塞**感知回路（并发断言）；结果作为感知事件回流；Delegate 动作过 Safety。
- [ ] 集成：把"改这段代码"结构化委派给 Codex/Claude Code，期间感知继续，结果回来后 Core 继续。
- [ ] 换/加一个 Delegate 无需改认知核（注册即用）。

## Git
- 分支：`feat/t16-delegate`
- 提交：`git commit -m "T16: 认知委派框架 + Codex/ClaudeCode 结构化委派"`
- 完成后改状态 ✅，勾选"M2.5 完成"验收。
