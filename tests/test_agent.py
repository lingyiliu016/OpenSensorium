"""Tests for SensoriumAgent."""

import threading
from unittest.mock import MagicMock, PropertyMock

import pytest

from opensensorium.agent import SensoriumAgent
from opensensorium.audio.sensor import AudioSensor
from opensensorium.llm.backbone import LLMBackbone
from opensensorium.memory.store import AgentMemory
from opensensorium.vision.sensor import VisionSensor


def _make_agent(
    listen_side_effect=None,
    llm_reply="I see you.",
    has_vision_frame=True,
    greet=False,
) -> SensoriumAgent:
    """Build a SensoriumAgent with fully mocked sub-components."""
    vision = MagicMock(spec=VisionSensor)
    type(vision).is_available = PropertyMock(return_value=has_vision_frame)
    vision.get_frame_b64.return_value = (
        "data:image/jpeg;base64,abc" if has_vision_frame else None
    )
    vision.start.return_value = None
    vision.stop.return_value = None

    audio = MagicMock(spec=AudioSensor)
    audio.listen.side_effect = listen_side_effect or [None]
    audio.speak.return_value = None
    type(audio).is_speaking = PropertyMock(return_value=False)

    llm = MagicMock(spec=LLMBackbone)
    llm.think.return_value = llm_reply

    memory = AgentMemory()

    return SensoriumAgent(
        vision=vision,
        audio=audio,
        llm=llm,
        memory=memory,
        use_vision=True,
        greet_on_start=greet,
    )


class TestSensoriumAgentCycle:
    def test_cycle_with_no_speech_does_not_call_llm(self):
        agent = _make_agent(listen_side_effect=[None])
        agent._setup()
        agent._cycle()
        agent.llm.think.assert_not_called()
        agent._teardown()

    def test_cycle_with_speech_calls_llm(self):
        agent = _make_agent(listen_side_effect=["Hello agent"])
        agent._setup()
        agent._cycle()
        agent.llm.think.assert_called_once()
        agent._teardown()

    def test_cycle_reply_is_spoken(self):
        agent = _make_agent(listen_side_effect=["hi"], llm_reply="Hey!")
        agent._setup()
        agent._cycle()
        agent.audio.speak.assert_called_once_with("Hey!")
        agent._teardown()

    def test_cycle_stores_turns_in_memory(self):
        agent = _make_agent(listen_side_effect=["tell me something"])
        agent._setup()
        agent._cycle()
        # Both user and assistant turns should be in memory
        assert agent.memory.turn_count == 2
        agent._teardown()

    def test_cycle_includes_image_when_available(self):
        agent = _make_agent(listen_side_effect=["describe what you see"])
        agent._setup()
        agent._cycle()
        call_kwargs = agent.llm.think.call_args[1]
        assert call_kwargs.get("image_b64") is not None
        agent._teardown()

    def test_cycle_skips_image_when_not_available(self):
        agent = _make_agent(
            listen_side_effect=["hello"], has_vision_frame=False
        )
        agent._setup()
        agent._cycle()
        call_kwargs = agent.llm.think.call_args[1]
        assert call_kwargs.get("image_b64") is None
        agent._teardown()

    def test_vision_failure_during_setup_disables_vision(self):
        agent = _make_agent(listen_side_effect=[None])
        agent.vision.start.side_effect = OSError("no camera")
        agent._setup()
        assert not agent.use_vision
        agent._teardown()


class TestSensoriumAgentRun:
    def test_run_stops_on_stop_event(self):
        """Agent loop should exit when stop() is called."""
        agent = _make_agent(listen_side_effect=[None] * 100)
        agent._setup()

        def _stop_soon():
            import time
            time.sleep(0.05)
            agent.stop()

        t = threading.Thread(target=_stop_soon, daemon=True)
        t.start()

        # _cycle is mocked to return immediately
        call_count = 0

        def _fast_cycle():
            nonlocal call_count
            call_count += 1
            if call_count > 50:
                agent.stop()

        agent._cycle = _fast_cycle
        agent.run()
        t.join(timeout=2.0)
        assert agent._stop_event.is_set()


class TestSensoriumAgentAsync:
    @pytest.mark.asyncio
    async def test_async_cycle_with_speech(self):
        agent = _make_agent(listen_side_effect=["async test"], llm_reply="async reply")
        agent.llm = MagicMock(spec=LLMBackbone)
        agent.llm.think_async = MagicMock(return_value=None)


        async def _fake_think_async(*args, **kwargs):
            return "async reply"

        agent.llm.think_async = _fake_think_async
        agent._setup()
        await agent._cycle_async()
        agent.audio.speak.assert_called_once_with("async reply")
        agent._teardown()
