"""核心数据模型：贯穿全系统的感知事件、意图、能力协商结构。

设计原则（对应 PRD）：
- 统一时间戳（单调时钟 + 挂钟对照），便于跨模态对齐（FR-1.5）。
- `CapabilityProfile` 为**模型 / 执行器 / 端**三处共用同一协商机制
  （PRD 强调三处能力协商同构）——新增模型/执行器/端时只填能力，不改 Core。

后续任务（T03 Adapter、T04 事件总线、T13 Effector 等）直接复用这里的类型。
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# 时间戳：单调时钟用于排序/对齐，挂钟用于人读/日志
# --------------------------------------------------------------------------- #


class Timestamp(BaseModel):
    """统一时间戳。

    - `monotonic`：`time.monotonic()` 秒数，单调不回拨，用于**跨模态排序与对齐**。
    - `wall`：Unix 纪元秒（`time.time()`），用于人读、日志、落盘。

    两者成对采集，既能稳定对齐，又能还原真实时刻（FR-1.5）。
    """

    monotonic: float = Field(description="单调时钟秒数，用于排序/对齐")
    wall: float = Field(description="Unix 纪元秒，用于人读/日志")

    @classmethod
    def now(cls) -> "Timestamp":
        return cls(monotonic=time.monotonic(), wall=time.time())


# --------------------------------------------------------------------------- #
# 感知事件
# --------------------------------------------------------------------------- #


class Modality(str, Enum):
    """感知模态。视觉为主、音频并行；预留可扩展。

    实时流与离散文件分开建模：
    - `SCREEN`/`CAMERA`/`AUDIO` 是连续采样的**实时流**（有 fps、有 seq）。
    - `IMAGE`/`VIDEO` 是**离散文件**（如 Channel 收到的图片/视频附件、给定的媒体文件），
      区别于 camera/screen 的实时帧。
    """

    SCREEN = "screen"  # 屏幕实时流
    CAMERA = "camera"  # 摄像头实时流
    IMAGE = "image"  # 离散图片文件/附件（非实时帧）
    VIDEO = "video"  # 离散视频文件片段（非实时流）
    AUDIO = "audio"  # 麦克风实时流
    TEXT = "text"  # 来自 Channel（如飞书）的文本输入
    EVENT = "event"  # 系统/调度等非采集事件源


class PerceptionEvent(BaseModel):
    """一条感知事件（一帧图像、一段音频、一条文本……）。

    `payload` 不放大二进制原文本身的强类型，保持通用；具体载荷约定由各模态在
    实现处（T05 采集、T10 音频等）细化，Core 只依赖这里的通用字段路由/对齐。
    """

    source_id: str = Field(description="流/源标识，如 'screen:0'、'camera:front'、'feishu:uid'")
    modality: Modality
    seq: int = Field(description="同一 source_id 内单调递增的序号，用于丢帧检测/排序")
    timestamp: Timestamp = Field(default_factory=Timestamp.now)
    payload: dict[str, Any] = Field(default_factory=dict, description="模态相关载荷（帧引用/PCM/文本等）")


# --------------------------------------------------------------------------- #
# 意图（认知核的输出）
# --------------------------------------------------------------------------- #


class IntentType(str, Enum):
    """认知核每个决策周期产出的意图类别（对齐 PRD 决策空间）。"""

    SAY = "say"  # 发声/回话（文本或 TTS）
    ACT = "act"  # 操作（键鼠/执行器动作）
    DELEGATE = "delegate"  # 认知委派给文本专家（Codex/ClaudeCode）
    SILENT = "silent"  # 保持沉默/不动作（显式的"什么都不做"也是一种决策）


class Intent(BaseModel):
    """认知核输出的一个意图。`payload` 承载类别相关细节。

    例：
    - SAY  → {"text": "...", "spoken": true}   # 走 TTS 朗读
             {"text": "...", "spoken": false}  # 只输出文本，不朗读
             {"text": "..."}                    # 不指定 → 由当前活跃通道决定（语音模式→TTS，飞书→文本）
    - ACT  → {"effector": "keyboard_mouse", "action": "click", "x": 100, "y": 200}
    - DELEGATE → {"delegate": "codex", "task": "..."}
    - SILENT → {}

    注：语音 vs 纯文本属于**投递层**约定（payload 里的 `spoken`），不单列意图类型——
    同一句"要说的话"可由当前通道决定朗读或纯文本，甚至两者兼有。
    """

    type: IntentType
    payload: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# 能力协商：模型 / 执行器 / 端 三处共用
# --------------------------------------------------------------------------- #


class CapabilityKind(str, Enum):
    MODEL = "model"
    EFFECTOR = "effector"
    ENDPOINT = "endpoint"


class CapabilityProfile(BaseModel):
    """能力剖面：三处（模型/执行器/端）**同构**的协商结构。

    - `capabilities`：该主体支持的能力名集合，如
      模型 {"video", "native-speech"} / {"video", "external-asr-tts"}；
      执行器 {"click", "type", "scroll"}；
      端 {"screen-capture", "wda-exclude-from-capture", "camera"}。
    - `params`：能力相关参数，如 {"max_fps": 10, "audio_sample_rate": 16000}。

    Core 依据 `negotiate()` 得到"缺哪些能力"，从而**裁剪/降级**（§6.3），
    实现"新增模型只加 Adapter、Core 零改动"（FR-2M.5）。
    """

    kind: CapabilityKind
    name: str = Field(description="主体名，如 'minicpm-o'、'joyai-vl'、'keyboard_mouse'、'windows'")
    capabilities: set[str] = Field(default_factory=set)
    params: dict[str, Any] = Field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def negotiate(self, required: set[str]) -> set[str]:
        """返回 `required` 中该主体**尚不支持**的能力集合；空集表示完全满足。"""
        return set(required) - self.capabilities
