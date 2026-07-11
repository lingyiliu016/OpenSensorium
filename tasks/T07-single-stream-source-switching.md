# T07 · 单路视频流 + 运行时热切源（屏/前/后摄，独立控制面）

- 里程碑：M0
- 依赖：T05
- PRD 对应：FR-1.6、§5.1、§6.2
- 状态：⬜ 未开始

## 目标
当前一次只接**单路**视频流，但绑定的源可**运行时热切换**：屏幕 ↔ 前置 ↔ 后置摄像头。切源由**控制指令**触发，走 T04 的独立控制面。语义是"单路+可切源"，非多路同时（多路待模型具备，§5.2）。

## 交付物
- [ ] `src/opensensorium/endpoint/windows/camera_capture.py`：摄像头采集（Media Foundation / OpenCV），同样产出 §6.6 基线帧。
- [ ] `src/opensensorium/endpoint/source_manager.py`：当前活动源单例；`switch_source(target)` 停旧源起新源。
- [ ] 切源在工作记忆里打标注"视觉源已从 X 切到 Y"，避免混为同一场景。
- [ ] 控制指令入口（先接文本/热键；语音触发随 M1）。
- [ ] 测试：`tests/test_source_switching.py`。

## 实现要点
- 切源经**控制面**，不与行动意图混（§6.2）。
- 摄像头源无回音，跳过 T06 处理（与判定准则一致）。
- 架构以 `source_id` + 时间戳为未来多路预留，但当前强制只有一个活动源。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现摄像头采集、source_manager、切源控制入口 + 测试。
- **人**：实测一条指令从屏幕切到前/后摄像头、切换无缝。

## 验收标准（可验证）
- [ ] `tests/test_source_switching.py`：`switch_source` 后旧源停止出帧、新源开始出帧，同一时刻只有一个活动源。
- [ ] 切源事件在工作记忆/日志中留下"X→Y"标注。
- [ ] 手动：一条控制指令从屏幕切到摄像头，总线上帧的 `source_id` 随之改变。

## Git
- 分支：`feat/t07-source-switching`
- 提交：`git commit -m "T07: 单路视频流 + 运行时热切源"`
- 完成后改状态 ✅。
