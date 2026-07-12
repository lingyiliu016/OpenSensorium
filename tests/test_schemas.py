"""T00 单元测试：核心数据模型的构造、序列化、能力协商。"""

from __future__ import annotations

import time

import pytest
from pydantic import ValidationError

from opensensorium.schemas import (
    CapabilityKind,
    CapabilityProfile,
    Intent,
    IntentType,
    Modality,
    PerceptionEvent,
    Timestamp,
)


# --------------------------------------------------------------------------- #
# Timestamp
# --------------------------------------------------------------------------- #


def test_timestamp_now_populates_both_clocks():
    before = time.monotonic()
    ts = Timestamp.now()
    after = time.monotonic()
    assert before <= ts.monotonic <= after
    assert ts.wall > 0


def test_timestamp_roundtrip():
    ts = Timestamp.now()
    dumped = ts.model_dump()
    assert set(dumped) == {"monotonic", "wall"}
    assert Timestamp.model_validate(dumped) == ts


def test_timestamps_are_monotonic_across_events():
    a = Timestamp.now()
    b = Timestamp.now()
    assert b.monotonic >= a.monotonic  # 单调不回拨，可用于跨模态排序


# --------------------------------------------------------------------------- #
# PerceptionEvent
# --------------------------------------------------------------------------- #


def test_perception_event_construct_and_defaults():
    ev = PerceptionEvent(source_id="screen:0", modality=Modality.SCREEN, seq=0)
    assert ev.modality is Modality.SCREEN
    assert ev.seq == 0
    assert ev.payload == {}
    assert isinstance(ev.timestamp, Timestamp)


def test_perception_event_json_roundtrip():
    ev = PerceptionEvent(
        source_id="camera:front",
        modality=Modality.CAMERA,
        seq=42,
        payload={"frame_ref": "buf://123", "width": 1280, "height": 720},
    )
    restored = PerceptionEvent.model_validate_json(ev.model_dump_json())
    assert restored == ev
    assert restored.payload["frame_ref"] == "buf://123"


def test_perception_event_modality_accepts_str_value():
    ev = PerceptionEvent(source_id="mic:0", modality="audio", seq=1)
    assert ev.modality is Modality.AUDIO


def test_perception_event_rejects_unknown_modality():
    with pytest.raises(ValidationError):
        PerceptionEvent(source_id="x", modality="smell", seq=0)


def test_perception_event_image_and_video_are_discrete_file_modalities():
    # 离散文件（如飞书附件），区别于 camera/screen 实时流
    img = PerceptionEvent(
        source_id="feishu:u123",
        modality="image",
        seq=0,
        payload={"file_ref": "buf://img1", "mime": "image/jpeg"},
    )
    vid = PerceptionEvent(
        source_id="feishu:u123",
        modality=Modality.VIDEO,
        seq=1,
        payload={"file_ref": "buf://vid1", "duration_s": 12.0},
    )
    assert img.modality is Modality.IMAGE
    assert vid.modality is Modality.VIDEO
    assert PerceptionEvent.model_validate_json(vid.model_dump_json()) == vid


# --------------------------------------------------------------------------- #
# Intent
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("itype", "payload"),
    [
        (IntentType.SAY, {"text": "你好"}),
        (IntentType.ACT, {"effector": "keyboard_mouse", "action": "click", "x": 10, "y": 20}),
        (IntentType.DELEGATE, {"delegate": "codex", "task": "重构模块"}),
        (IntentType.SILENT, {}),
    ],
)
def test_intent_construct_and_roundtrip(itype, payload):
    intent = Intent(type=itype, payload=payload)
    restored = Intent.model_validate_json(intent.model_dump_json())
    assert restored == intent
    assert restored.type is itype


def test_intent_silent_defaults_empty_payload():
    intent = Intent(type=IntentType.SILENT)
    assert intent.payload == {}


@pytest.mark.parametrize("spoken", [True, False])
def test_intent_say_carries_spoken_delivery_hint(spoken):
    # 语音 vs 纯文本是投递层约定，放 payload["spoken"]，不单列意图类型
    intent = Intent(type=IntentType.SAY, payload={"text": "你好", "spoken": spoken})
    restored = Intent.model_validate_json(intent.model_dump_json())
    assert restored.type is IntentType.SAY
    assert restored.payload["spoken"] is spoken


def test_intent_say_without_spoken_defers_to_channel():
    intent = Intent(type=IntentType.SAY, payload={"text": "你好"})
    assert "spoken" not in intent.payload  # 不指定 → 由当前活跃通道决定朗读/文本


# --------------------------------------------------------------------------- #
# CapabilityProfile —— 三处（模型/执行器/端）共用同一协商机制
# --------------------------------------------------------------------------- #


def test_capability_supports_and_negotiate_fully_satisfied():
    prof = CapabilityProfile(
        kind=CapabilityKind.MODEL,
        name="minicpm-o",
        capabilities={"video", "native-speech"},
        params={"max_fps": 10, "audio_sample_rate": 16000},
    )
    assert prof.supports("native-speech")
    assert not prof.supports("external-asr-tts")
    assert prof.negotiate({"video"}) == set()  # 需求全满足


def test_capability_negotiate_reports_missing():
    joyai = CapabilityProfile(
        kind=CapabilityKind.MODEL,
        name="joyai-vl",
        capabilities={"video", "external-asr-tts"},
    )
    missing = joyai.negotiate({"video", "native-speech"})
    assert missing == {"native-speech"}  # Core 据此降级/裁剪


def test_capability_profile_shared_across_kinds():
    endpoint = CapabilityProfile(
        kind=CapabilityKind.ENDPOINT,
        name="windows",
        capabilities={"screen-capture", "wda-exclude-from-capture", "camera"},
    )
    effector = CapabilityProfile(
        kind=CapabilityKind.EFFECTOR,
        name="keyboard_mouse",
        capabilities={"click", "type", "scroll"},
    )
    # 同一结构、同一 negotiate 语义服务于端与执行器
    assert endpoint.negotiate({"wda-exclude-from-capture"}) == set()
    assert effector.negotiate({"click", "drag"}) == {"drag"}


def test_capability_profile_json_roundtrip():
    prof = CapabilityProfile(
        kind=CapabilityKind.MODEL,
        name="minicpm-o",
        capabilities={"video", "native-speech"},
    )
    restored = CapabilityProfile.model_validate_json(prof.model_dump_json())
    assert restored == prof
