# T05 · Windows 屏幕采集 Endpoint（JPEG ~1fps、下采样、窗口/显示器/全屏）

- 里程碑：M0
- 依赖：T04
- PRD 对应：FR-1.1、§6.4 平台矩阵（Windows 首平台）
- 状态：⬜ 未开始

## 目标
在 Windows 上把屏幕采成符合 §6.6 基线的视频帧流，推进感知总线。三种源：全屏 / 指定显示器 / 指定窗口；可配采样率与分辨率下采样。

## 交付物
- [ ] `src/opensensorium/endpoint/windows/screen_capture.py`：Windows.Graphics.Capture 或 DXGI Desktop Duplication（`mss` 起步亦可）。
- [ ] 输出：**JPEG 静止帧、默认 ~1fps（可配上探 10fps）、下采样至 ≤~180万像素**，封装成 `PerceptionEvent(modality=video)` 发上总线。
- [ ] 支持三种源选择（全屏/显示器/窗口）。
- [ ] 采样率/分辨率可配。
- [ ] 测试：`tests/test_screen_capture.py`（帧尺寸≤180万像素、JPEG 可解码、帧率近似目标值）。

## 实现要点
- 窗口级采集为 T06 防回音（`WDA_EXCLUDEFROMCAPTURE`）与 §3.1 源隔离铺路。
- 帧格式必须与 T03 两款 Adapter 期望一致（公约数），避免每模型各转一次。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现采集器（三种源、下采样、JPEG）+ 单元/集成测试。
- **人**：在你的 Windows 笔记本上实测帧率/CPU 占用、三种源切换效果。

## 验收标准（可验证）
- [ ] `tests/test_screen_capture.py` 全绿：抓到的帧可被 Pillow 解码、像素数 ≤~180万、为 JPEG。
- [ ] 手动/自动测：切换全屏/指定显示器/指定窗口三种源均出帧。
- [ ] 连续采集 30s，实测帧率与配置值偏差在可接受范围，CPU 占用记录在案。
- [ ] 帧作为 `PerceptionEvent` 正确进入 T04 总线（集成测试）。

## Git
- 分支：`feat/t05-screen-capture`
- 提交：`git commit -m "T05: Windows 屏幕采集 Endpoint（JPEG ~1fps 基线）"`
- 完成后改状态 ✅。
