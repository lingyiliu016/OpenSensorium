# T06 · 防回音：呈现面 `WDA_EXCLUDEFROMCAPTURE`

- 里程碑：M0
- 依赖：T05
- PRD 对应：FR-1.2、§3.1 感知面/呈现面解耦
- 状态：⬜ 未开始

## 目标
解决"视觉回音"：OpenSensorium 自己的 UI（呈现面）**对人眼可见、对采集隐形**，避免模型看到自己的输出形成正反馈发散。近期落地 Windows 最优雅方案。

## 交付物
- [ ] `src/opensensorium/endpoint/windows/capture_exclusion.py`：对呈现面窗口 hwnd 调 `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`。
- [ ] 分级退化接口：不支持排除时退到"源隔离"（采某窗口/显示器而非合成屏）→ 再退到虚拟显示器（占位，§3.1 第 3 招）。
- [ ] 与 §3.1 一般准则一致的判定：仅"屏幕自采集"这一路需处理；摄像头源无回环，跳过。
- [ ] 测试/验证脚本：`scripts/verify_anti_echo.py`。

## 实现要点
- 回音判定准则（§3.1）：**呈现面可能出现在被采集观察面之内 ⟺ 需处理**。判定逻辑要显式实现，不要一刀切。
- 排除能力按平台差异（§6.4）：Windows/mac 原生按窗口；Linux/Android/iOS 无 → 走退化（本任务只做 Windows，退化留接口）。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现采集排除 + 退化接口 + `verify_anti_echo.py` 截图比对。
- **人**：肉眼确认"浮层人可见、采集帧里不可见"——这条只能人验。

## 验收标准（可验证）
- [ ] 打开呈现面浮层并对其启用排除后，用 T05 采集**同屏**：采到的帧中**不含**该浮层，但人眼仍能看到它（`verify_anti_echo.py` 截图比对 + 人工确认）。
- [ ] 关闭排除对照：帧中能看到浮层（证明机制生效而非窗口本就不可见）。
- [ ] 摄像头源场景下判定逻辑正确跳过防回音处理。

> ⚠️ 需人工验证："人眼可见、采集隐形"最终由你肉眼 + 采集帧确认。

## Git
- 分支：`feat/t06-anti-echo`
- 提交：`git commit -m "T06: 防回音呈现面采集排除（WDA_EXCLUDEFROMCAPTURE）"`
- 完成后改状态 ✅。
