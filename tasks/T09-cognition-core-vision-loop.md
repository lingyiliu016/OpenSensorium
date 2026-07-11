# T09 · 认知核回路骨架：总线↔Adapter↔意图，视觉路径 E2E（M0 收口）

- 里程碑：M0（收口）
- 依赖：T03、T04、T05、T08
- PRD 对应：FR-2.1 持续感知回路、FR-2.5 意图输出、§3.2
- 状态：⬜ 未开始

## 目标
把前面的部件串成**最小可运行闭环**：屏幕流稳定进模型（两款均可）、不自我回环、UI 可见其所见、能一句话切到摄像头。这是 M0 的 Demo 收口——**视觉路径**跑通（语音随 M1，键鼠随 M2）。

## 交付物
- [ ] `src/opensensorium/core/loop.py`：持续感知回路——订阅总线 → 经当前 Adapter 推理 → 产出 `Intent`（此阶段先支持 say/silent，act/delegate 占位）。
- [ ] `src/opensensorium/core/working_memory.py`：滚动工作记忆（当前屏幕/源/最近结论）。
- [ ] `src/opensensorium/app.py`：装配入口——起 Endpoint 采集 + 总线 + Adapter + Core loop + UI。
- [ ] 端到端集成测试 `tests/test_vision_loop_e2e.py`（用 mock Adapter 免依赖 4090）。

## 实现要点
- 回路**常开、非阻塞**：单次推理不阻塞采集（NFR）。
- 通过 T03 registry 支持在 MiniCPM-o / JoyAI 间切换，验证"两款视觉路径均跑通并可切换"。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现回路、工作记忆、装配入口 + E2E 测试（mock Adapter，不占用 4090）。
- **人（M0 Demo 验收）**：4090 两款服务在线时，实机走一遍——稳定进模型、不回环、可见其所见、能切源、两款可切换。

## 验收标准（可验证）
- [ ] `tests/test_vision_loop_e2e.py`（mock Adapter）：帧进 → 推理 → 产出 `Intent` → UI 状态更新，全链无阻塞。
- [ ] 集成（4090 在线）：**MiniCPM-o 与 JoyAI 两款**分别作为底座，屏幕流均能稳定进模型并拿到输出。
- [ ] 运行时不自我回环（复用 T06；开/关排除对照，开时模型输出稳定不发散）。
- [ ] 一句话/一热键从屏幕切到摄像头（复用 T07），回路继续正常产出。
- [ ] 两款模型间可切换，Core 代码不变。

> ⚠️ 需人工验证：M0 Demo（稳定进模型、不回环、可见其所见、能切源、两款可切）由你实机走一遍确认。

## Git
- 分支：`feat/t09-vision-loop`
- 提交：`git commit -m "T09: 认知核视觉回路 E2E（M0 收口）"`
- 完成后改状态 ✅，并在 tasks/README.md 勾选"M0 完成"验收。
