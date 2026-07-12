"""
LLMBackbone — multimodal reasoning core for the SensoriumAgent.

The backbone wraps the OpenAI Chat Completions API and assembles messages that
can carry:
  * plain text (e.g. transcribed speech),
  * base-64 encoded images (captured from the camera),
  * historical conversation context supplied by AgentMemory.

Model choice
------------
``gpt-4o`` is the default because it supports both vision and text natively.
Override via the ``model`` constructor argument or the ``OPENSENSORIUM_MODEL``
environment variable.

Async vs sync
-------------
Both ``think`` (synchronous) and ``think_async`` (async) entry points are
provided so the backbone can be used from either sync scripts or async
event loops.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "You are an embodied AI agent called Sensorium. "
    "You perceive the world through a camera and a microphone, just like a person. "
    "Respond naturally, concisely, and helpfully. "
    "If you can see something relevant in the image, describe or reference it. "
    "Keep responses short enough to be spoken aloud comfortably (2-4 sentences)."
)


class LLMBackbone:
    """Multimodal reasoning backbone backed by the OpenAI API.

    Parameters
    ----------
    model:
        Chat-completion model to use.  Falls back to the environment variable
        ``OPENSENSORIUM_MODEL``, then to ``"gpt-4o"``.
    system_prompt:
        System-level instructions that define the agent's persona.
    openai_client:
        A pre-configured ``openai.OpenAI`` instance.  When ``None`` a client is
        created from the environment (reads ``OPENAI_API_KEY``).
    max_tokens:
        Maximum tokens in the model's reply.
    temperature:
        Sampling temperature (0 = deterministic, 1 = creative).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
        openai_client=None,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> None:
        self.model = model or os.getenv("OPENSENSORIUM_MODEL", "gpt-4o")
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = openai_client

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def think(
        self,
        text_input: Optional[str],
        image_b64: Optional[str] = None,
        history: Optional[Sequence[dict[str, Any]]] = None,
    ) -> str:
        """Process *text_input* (and optionally *image_b64*) and return a reply.

        Parameters
        ----------
        text_input:
            Transcribed speech or typed text from the user.  May be ``None`` if
            only a visual frame is available.
        image_b64:
            Base-64-encoded JPEG frame (``data:image/jpeg;base64,...``).
            Omitted from the request when ``None``.
        history:
            Previous turns as a list of ``{"role": …, "content": …}`` dicts
            produced by :class:`~opensensorium.memory.AgentMemory`.

        Returns
        -------
        The model's reply as a plain string.
        """
        messages = self._build_messages(text_input, image_b64, history)
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        reply = response.choices[0].message.content or ""
        logger.debug("LLM reply: %r", reply[:120])
        return reply.strip()

    async def think_async(
        self,
        text_input: Optional[str],
        image_b64: Optional[str] = None,
        history: Optional[Sequence[dict[str, Any]]] = None,
    ) -> str:
        """Async variant of :meth:`think` using ``openai.AsyncOpenAI``."""
        messages = self._build_messages(text_input, image_b64, history)
        client = self._get_async_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        reply = response.choices[0].message.content or ""
        logger.debug("LLM reply (async): %r", reply[:120])
        return reply.strip()

    # ------------------------------------------------------------------
    # Message assembly
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        text_input: Optional[str],
        image_b64: Optional[str],
        history: Optional[Sequence[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Inject conversation history
        if history:
            messages.extend(history)

        # Build the current user turn (may be multimodal)
        content: list[dict[str, Any]] | str
        if image_b64 is not None:
            content = []
            if text_input:
                content.append({"type": "text", "text": text_input})
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_b64, "detail": "low"},
                }
            )
        else:
            content = text_input or "(no speech detected)"

        messages.append({"role": "user", "content": content})
        return messages

    # ------------------------------------------------------------------
    # Client helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            import openai  # noqa: PLC0415
            self._client = openai.OpenAI()
        return self._client

    def _get_async_client(self):
        import openai  # noqa: PLC0415
        return openai.AsyncOpenAI()
