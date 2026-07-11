# T24 · 走进物理世界（愿景占位，非 v1 承诺）

- 里程碑：M6+
- 依赖：待底座模型/硬件具备
- PRD 对应：§1.3 终极愿景、§9.3/§9.4 演进路径、§5.2/§5.3、§6.4 其它平台端
- 状态：⬜ 未开始（愿景占位，不在 v1 实现）

## 目标
记录并预留通往物理世界的后续任务簇。**屏幕操作只是第一步，绝非最终产品**——最终是操纵汽车、机器人、智能家居，彻底走进物理世界。本文件是占位与预留，不在 v1 开发，认知核对这些执行器的接口保持开放（零改动引入）。

## 子任务簇（未来各自拆成独立任务文件）
- [ ] **触屏执行器 / PhoneEffector**（FR-3.1T、§9.4.1）：`touch.tap/long_press/long_press_drag/swipe(上下左右)/drag/pinch`、`key.back/home`、文本输入；落地通道 ADB（安卓）/ iOS 自动化 / 云手机。手机屏作为一路视频源（单路+可切源）。
- [ ] **多路视频流**（§5.2、M6+）：屏幕+摄像头等同时——**待底座模型支持后**启动；架构已以 source_id+时间戳预留。
- [ ] **物理世界执行器**：`VehicleEffector`（智能驾驶/座舱）、`RobotEffector`（工业/家庭）、`HomeEffector`（智能家居 IoT）——引入时认知核零改动 + Safety 层加分级授权（物理动作授权尤严）。
- [ ] **其它平台 Endpoint**：macOS（ScreenCaptureKit + `SCContentFilter` + `CGEventPost`）、Linux（PipeWire/portal + libei/uinput）、Android（MediaProjection + AccessibilityService，Kotlin/Java 薄壳）、iOS（ReplayKit + WebDriverAgent/云真机，最受限）——经统一实时流接回 Python Core。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：到各子任务启动时，实现相应 Effector/Endpoint + 测试；保持接口一般性。
- **人**：提供目标硬件（手机/车/机器人/家居/其它系统机器）、判定"何时模型/硬件已具备"、把关物理动作安全授权。

## 验收标准（可验证）
- [ ] 本文件作为路线锚点存在，接口预留在 §9.4（`CloudPCEffector/PhoneEffector/VehicleEffector/RobotEffector/HomeEffector` 占位）已就绪。
- [ ] 每个子任务启动时拆成独立 `Tnn` 文件并遵循同样的可验收 + 分工规范。

## Git
- 分支：按各子任务单独开。
- 本占位文件随 M5 之后按需拆分推进。
