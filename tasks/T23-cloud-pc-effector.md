# T23 · CloudPCEffector（复用键鼠+屏幕原语走远程通道，防回音判定）

- 里程碑：M5
- 依赖：T13、T15
- PRD 对应：§9.3、§9.4、§3.1 回音范围
- 状态：⬜ 未开始

## 目标
本地电脑之外的第一站：把同一套键鼠+屏幕动作原语走**远程通道**（RDP/VNC/云桌面流）操作云端电脑。验证"同一意图跨不同执行身体"——同一套决策既操本地也操云端。

## 交付物
- [ ] `src/opensensorium/effector/cloud_pc.py`：`CloudPCEffector`，复用 §9.1 键鼠原语，动作走远程通道。
- [ ] 云端桌面作为一路视频源接入（受单路+可切源约束）。
- [ ] **防回音判定**（§3.1 准则）：云端桌面渲染到本地屏 → 需防回音；云端侧直接抓帧/无头 → 不在回音范围。判定要显式实现。
- [ ] 测试：`tests/test_cloud_pc_effector.py`。

## 分工（Agent 做什么 / 人做什么）
- **Agent**：实现 CloudPCEffector、远程通道封装、防回音判定、测试。
- **人**：准备一台云端/远程电脑与通道凭证，实测远程操作与回音判定。

## 验收标准（可验证）
- [ ] `tests/test_cloud_pc_effector.py`：同一意图路由到 CloudPCEffector 与本地 KeyboardMouseEffector 均可执行；防回音判定按渲染位置正确开关。
- [ ] 集成：同一套决策既操本地电脑也操云端电脑。

> ⚠️ 需人工验证：真实远程通道与跨身体操作由你实测。

## Git
- 分支：`feat/t23-cloud-pc`
- 提交：`git commit -m "T23: CloudPCEffector（远程通道 + 防回音判定）"`
- 完成后改状态 ✅，勾选"M5 完成"验收。
