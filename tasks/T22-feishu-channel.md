# T22 · 飞书 Channel + Channel 抽象（收发文/图/语音、身份权限）

- 里程碑：M4
- 依赖：T09、T14
- PRD 对应：FR-4、§10、§4.2 场景 3
- 状态：⬜ 未开始

## 目标
飞书为入口的交互 Agent：人在飞书上让它**在电脑上干活**并拿到语音/文字回复。重点是远程让它"动手"，而非只远程问答。Channel 与本地实时交互并列，共享同一认知核。

## 交付物
- [ ] `src/opensensorium/channel/base.py`：`Channel` 接口——`receive()`（文/图/语音）、`send()`（文/语音）、`identity/permission`。
- [ ] `src/opensensorium/channel/feishu.py`：飞书（Lark）收发文本/语音/图片。
- [ ] 会话与身份：区分用户/群；权限（谁能让它操作，FR-4.2）——接 T14 Safety。
- [ ] Channel 事件进 T04 总线（事件触发源之一，§3.7）。
- [ ] 微信等预留：新增 Channel 不改认知核（FR-4.3）。
- [ ] 测试：`tests/test_channel.py`（收发、权限、抽象可插拔）。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 Channel 抽象 + 飞书实现 + 权限接入 + 测试（可用飞书沙盒/mock）。
- **人**：在飞书开放平台创建应用、配置回调/凭证（App ID/Secret 放 `config.local.yaml`，勿入库），真机对话验证。

## 验收标准（可验证）
- [ ] `tests/test_channel.py`：收发链路通；无权限用户不能触发操作；换 Channel 实现认知核零改动。
- [ ] 集成：从飞书发一条指令让它在电脑上完成一个操作，并收到语音/文字回复。

> ⚠️ 需人工验证：飞书应用配置与真机端到端由你完成。凭证不入库。

## Git
- 分支：`feat/t22-feishu`
- 提交：`git commit -m "T22: 飞书 Channel + Channel 抽象"`
- 完成后改状态 ✅，勾选"M4 完成"验收。
