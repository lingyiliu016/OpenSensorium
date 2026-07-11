# T13 · KeyboardMouseEffector + Effector 能力协商

- 里程碑：M2
- 依赖：T09
- PRD 对应：FR-3.1、FR-3.4、§9.1–9.2
- 状态：⬜ 未开始

## 目标
让它能真正**动手**操作本地电脑：键鼠执行器 + 统一 Effector 抽象（能力协商）。认知核只发"意图"，行动层匹配可用执行器——为未来云端/手机/物理世界执行器预留同一接口。

## 交付物
- [ ] `src/opensensorium/effector/base.py`：`Effector` 接口——`capabilities()`（动作原语集合）、`execute(action)`、`constraints()`（作用域/速率/危险级别）。
- [ ] `src/opensensorium/effector/keyboard_mouse.py`：`KeyboardMouseEffector`（Windows `SendInput`）——绝对/相对坐标移动、左右键点击、双击、拖拽、滚轮、键盘输入、组合键（FR-3.1 全集）。
- [ ] `src/opensensorium/effector/registry.py`：注册/能力协商；Core 发意图，registry 选执行器。
- [ ] 动作原语词汇表按 §9.1（`pointer.move/click`、`key.type`…，触屏 `touch.*` 先占位，随 T24）。
- [ ] 测试：`tests/test_effector.py`（能力协商、动作分发；实际注入用受控窗口做集成）。

## 实现要点
- 意图—执行器解耦（§9.5）：同一"点击那个按钮"意图，键鼠落成鼠标点击，未来手机落成 tap，接口不变。
- **所有动作必须先过 Safety 层**——本任务预留调用点，Safety 实现见 T14（合并前不放开危险动作）。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 Effector 抽象、KeyboardMouseEffector、registry + 测试。
- **人**：在受控测试窗口实测真实键鼠注入效果（务必先接 T14 安全门再放开）。

## 验收标准（可验证）
- [ ] `tests/test_effector.py`：`capabilities()` 返回完整键鼠原语；registry 按意图正确选中执行器；非法动作被拒。
- [ ] 集成：在一个受控测试窗口里，执行"移动+点击+键入+拖拽"可观测生效。
- [ ] 意图—执行器解耦：mock 一个第二执行器，同一意图能路由到不同执行器。

> ⚠️ 需人工验证：真实键鼠注入效果由你在受控窗口确认（注意先接 T14 安全门）。

## Git
- 分支：`feat/t13-km-effector`
- 提交：`git commit -m "T13: KeyboardMouseEffector + Effector 能力协商"`
- 完成后改状态 ✅。
