"""
SensoriumAgent — the main agent loop.

Architecture
------------
The agent is built around three sequential phases that mirror the cognitive
loop of an embodied animal:

1. **Perceive** — concurrently sample the camera (vision) and microphone (audio).
2. **Think**   — feed sensory data plus memory context to the LLM backbone.
3. **Act**     — speak the reply aloud and update memory.

The loop runs synchronously by default (``run()``) or asynchronously
(``run_async()``) so it fits both scripted and event-driven contexts.

Configuration
-------------
All settings can be supplied via the constructor or via environment variables.
See the constructor docstring for details.

Usage
-----
    from opensensorium import SensoriumAgent

    agent = SensoriumAgent()
    agent.run()          # blocks until KeyboardInterrupt
"""

from __future__ import annotations

import asyncio
import logging
import signal
import threading
from typing import Optional

from opensensorium.audio.sensor import AudioSensor
from opensensorium.llm.backbone import LLMBackbone
from opensensorium.memory.store import AgentMemory
from opensensorium.vision.sensor import VisionSensor

logger = logging.getLogger(__name__)


class SensoriumAgent:
    """A human/animal-like AI agent grounded in vision and voice.

    Parameters
    ----------
    vision:
        :class:`~opensensorium.vision.VisionSensor` instance.  When ``None``
        one is created with the default ``opencv`` backend.
    audio:
        :class:`~opensensorium.audio.AudioSensor` instance.  When ``None`` one
        is created with the ``openai`` STT/TTS backends.
    llm:
        :class:`~opensensorium.llm.LLMBackbone` instance.  When ``None`` one
        is created with the default ``gpt-4o`` model.
    memory:
        :class:`~opensensorium.memory.AgentMemory` instance.  When ``None``
        a fresh memory store is created.
    listen_timeout:
        Seconds to wait for the user to speak before looping back.
    use_vision:
        If ``False`` the camera frame is never included in the LLM request.
        Useful when running without a physical camera.
    greet_on_start:
        If ``True`` the agent speaks a greeting when ``run()`` is first called.
    greeting_text:
        The greeting to speak (if *greet_on_start* is ``True``).
    """

    def __init__(
        self,
        vision: Optional[VisionSensor] = None,
        audio: Optional[AudioSensor] = None,
        llm: Optional[LLMBackbone] = None,
        memory: Optional[AgentMemory] = None,
        listen_timeout: float = 10.0,
        use_vision: bool = True,
        greet_on_start: bool = True,
        greeting_text: str = (
            "Hello! I'm Sensorium, your embodied AI companion. "
            "I can see and hear you. How can I help?"
        ),
    ) -> None:
        self.vision = vision or VisionSensor()
        self.audio = audio or AudioSensor()
        self.llm = llm or LLMBackbone()
        self.memory = memory or AgentMemory()
        self.listen_timeout = listen_timeout
        self.use_vision = use_vision
        self.greet_on_start = greet_on_start
        self.greeting_text = greeting_text
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public run interfaces
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the synchronous perceive→think→act loop.

        Runs until a ``KeyboardInterrupt`` or :meth:`stop` is called.
        """
        self._setup()
        logger.info("SensoriumAgent running. Press Ctrl-C to quit.")
        try:
            while not self._stop_event.is_set():
                self._cycle()
        except KeyboardInterrupt:
            pass
        finally:
            self._teardown()

    async def run_async(self) -> None:
        """Async variant of :meth:`run` (compatible with ``asyncio.run()``)."""
        self._setup()
        logger.info("SensoriumAgent running (async). Press Ctrl-C to quit.")
        try:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, self.stop)
            while not self._stop_event.is_set():
                await self._cycle_async()
        finally:
            self._teardown()

    def stop(self) -> None:
        """Request the agent loop to stop gracefully."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Synchronous cycle
    # ------------------------------------------------------------------

    def _cycle(self) -> None:
        # 1. PERCEIVE — grab the latest camera frame (non-blocking)
        image_b64: Optional[str] = None
        if self.use_vision and self.vision.is_available:
            image_b64 = self.vision.get_frame_b64()

        # 2. PERCEIVE — listen for speech
        logger.debug("Listening for speech…")
        text_input = self.audio.listen(timeout=self.listen_timeout)
        if text_input is None:
            logger.debug("No speech detected, looping…")
            return

        logger.info("User said: %r", text_input)

        # 3. THINK — assemble context and call the LLM
        history = self.memory.get_history()
        reply = self.llm.think(text_input, image_b64=image_b64, history=history)
        logger.info("Agent says: %r", reply)

        # 4. REMEMBER — store this turn
        if image_b64:
            user_content: object = [
                {"type": "text", "text": text_input},
                {"type": "image_url", "image_url": {"url": image_b64, "detail": "low"}},
            ]
        else:
            user_content = text_input
        self.memory.add_user_turn(user_content)
        self.memory.add_assistant_turn(reply)

        # 5. ACT — speak the reply
        self.audio.speak(reply)

    # ------------------------------------------------------------------
    # Async cycle
    # ------------------------------------------------------------------

    async def _cycle_async(self) -> None:
        image_b64: Optional[str] = None
        if self.use_vision and self.vision.is_available:
            image_b64 = self.vision.get_frame_b64()

        # STT is I/O-bound; run it in a thread to avoid blocking the event loop
        text_input: Optional[str] = await asyncio.to_thread(
            self.audio.listen, self.listen_timeout
        )
        if text_input is None:
            return

        logger.info("User said: %r", text_input)

        history = self.memory.get_history()
        reply = await self.llm.think_async(text_input, image_b64=image_b64, history=history)
        logger.info("Agent says: %r", reply)

        if image_b64:
            user_content: object = [
                {"type": "text", "text": text_input},
                {"type": "image_url", "image_url": {"url": image_b64, "detail": "low"}},
            ]
        else:
            user_content = text_input
        self.memory.add_user_turn(user_content)
        self.memory.add_assistant_turn(reply)

        await asyncio.to_thread(self.audio.speak, reply)

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        self._stop_event.clear()
        if self.use_vision:
            try:
                self.vision.start()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not start vision sensor (%s). Running without camera.", exc
                )
                self.use_vision = False

        if self.greet_on_start:
            try:
                self.audio.speak(self.greeting_text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not play greeting (%s).", exc)

    def _teardown(self) -> None:
        if self.use_vision:
            try:
                self.vision.stop()
            except Exception:  # noqa: BLE001
                pass
        logger.info("SensoriumAgent stopped.")
