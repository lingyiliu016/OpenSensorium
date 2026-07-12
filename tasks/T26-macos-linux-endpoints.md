# T26 · macOS / Linux 桌面 Endpoint（采集 + 防回音 + 输入注入）

- 里程碑：v1.x（桌面三平台目标，紧随 Windows 之后）
- 依赖：T05、T06、T07、T13（Windows Endpoint 接口成型后照搬到 mac/Linux）
- PRD 对应：§6.4 平台兼容矩阵、§3.6 Endpoint/Core 拆分、NFR 跨平台
- 状态：⬜ 未开始

## 目标
把 Windows 上验证过的 Endpoint 接口落到 **macOS 与 Linux**：采集（屏幕/摄像头/麦克风）+ 防回音 + 键鼠注入。Core 一份代码不变，差异全部收敛在各平台 Endpoint（§3.6）。这是"兼容 Win/mac/Linux/Android/iOS"里桌面那三块的后两块。

## 交付物
- [ ] `src/opensensorium/endpoint/macos/`：
  - 屏幕采集 ScreenCaptureKit（12.3+）；摄像头/麦克风 AVFoundation。
  - 防回音：`SCContentFilter` 排除自身窗口（原生按窗口，等价 Windows 的 `WDA_EXCLUDEFROMCAPTURE`）。
  - 输入注入 `CGEventPost`（需**辅助功能**授权）。
  - 帧/音频输出与 §6.6 基线一致（JPEG ~1fps ≤180万像素 / 16kHz mono PCM16 ~1s）。
- [ ] `src/opensensorium/endpoint/linux/`：
  - 屏幕采集 PipeWire + xdg-portal（Wayland）/ X11(XShm)；摄像头 V4L2/PipeWire。
  - 防回音：**无原生按窗口排除** → 退化到源隔离 / 虚拟显示器（Xvfb），复用 §3.1 分级。
  - 输入注入 Wayland libei/RemoteDesktop portal；X11 XTEST；底层 uinput。
- [ ] 端能力协商：各端声明可用采集源、防回音手段、可注入原语、权限状态（Core 据此裁剪，§6.3）。
- [ ] 测试：`tests/test_endpoint_macos.py`、`tests/test_endpoint_linux.py`（可跑部分做单元；采集/注入实机做集成）。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现两平台 Endpoint（Python 为主，覆盖不到处再评估原生壳）、能力协商、可离线单测。
- **人**：分别在一台 macOS 与一台 Linux 上实测——授予屏幕录制/辅助功能/portal 权限、验证采集帧、防回音（mac 排除 / Linux 退化）、键鼠注入。**这两块必须在真机上由你验收。**

## 实现要点
- 接口照搬 Windows Endpoint（T05/T06/T07/T13），只换平台实现——验证"Core 零改动、差异只在 Endpoint"。
- 防回音按平台退化：mac 原生排除；Linux 无 → 源隔离/虚拟显示器（与 §6.4 矩阵一致）。
- 优先 Python；仅当 Python 覆盖不到某平台采集/注入时才用原生语言薄壳（与 [[primary-language-python]] 一致）。

## 验收标准（可验证）
- [ ] macOS 实机：屏幕/摄像头/麦克风采集出 §6.6 基线流；`SCContentFilter` 使呈现面对采集隐形；`CGEventPost` 键鼠注入生效（授权后）。
- [ ] Linux 实机：采集出基线流；防回音退化方案生效（源隔离或 Xvfb）；键鼠注入生效。
- [ ] **同一 Core + 同一任务**分别接 Windows / macOS / Linux Endpoint 均能跑通（证明 Core 零改动）。
- [ ] 各端能力协商正确上报本平台差异（如 Linux 无按窗口排除）。

> ⚠️ 需人工验证：两平台的采集/防回音/注入/权限都需你在真机确认。

## Git
- 分支：`feat/t26-macos-linux-endpoints`
- 提交：`git commit -m "T26: macOS/Linux 桌面 Endpoint（采集/防回音/注入）"`
- 完成后改状态 ✅。
