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
