"""
AgentMemory — rolling conversational and sensory context.

The memory module manages two types of state:

1. **Conversation history** — a bounded deque of ``{"role", "content"}`` dicts
   that mirrors the OpenAI messages format.  Old turns are evicted from the
   *front* when the window exceeds ``max_turns``.

2. **Sensory annotations** — short text descriptions of what the agent
   recently *saw* (e.g. from a vision-language model).  These are injected as
   context when the conversation history is retrieved.

Thread safety
-------------
All public methods acquire an internal ``threading.Lock`` so that the memory
store can be safely shared between the perception, reasoning, and action
threads of the main agent loop.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Any


class AgentMemory:
    """Bounded rolling window of conversation turns and sensory notes.

    Parameters
    ----------
    max_turns:
        Maximum number of past turns (user + assistant pairs) to retain.
        When this limit is exceeded the oldest *user* turn and its paired
        *assistant* reply are removed together.
    """

    def __init__(self, max_turns: int = 20) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        self.max_turns = max_turns
        self._history: deque[dict[str, Any]] = deque()
        self._sensory_notes: deque[str] = deque(maxlen=5)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def add_user_turn(self, content: Any) -> None:
        """Append a user message to the history.

        Parameters
        ----------
        content:
            Either a plain string or the list-of-content-parts format used by
            multimodal OpenAI messages.
        """
        with self._lock:
            self._history.append({"role": "user", "content": content})
            self._evict_if_needed()

    def add_assistant_turn(self, text: str) -> None:
        """Append an assistant (agent) message to the history."""
        with self._lock:
            self._history.append({"role": "assistant", "content": text})
            self._evict_if_needed()

    def get_history(self) -> list[dict[str, Any]]:
        """Return a snapshot of the current conversation history.

        Sensory context (if any) is prepended as a system-style note so the
        LLM is aware of recent visual observations.
        """
        with self._lock:
            result = list(self._history)
            if self._sensory_notes:
                context_note = "Recent visual context: " + "; ".join(self._sensory_notes)
                result.insert(0, {"role": "system", "content": context_note})
            return result

    def clear_history(self) -> None:
        """Erase all conversation turns."""
        with self._lock:
            self._history.clear()

    @property
    def turn_count(self) -> int:
        """Number of individual messages currently stored."""
        with self._lock:
            return len(self._history)

    # ------------------------------------------------------------------
    # Sensory annotations
    # ------------------------------------------------------------------

    def add_sensory_note(self, note: str) -> None:
        """Record a brief textual description of what the agent currently sees.

        Parameters
        ----------
        note:
            A short sentence describing the current visual scene.
        """
        if note and note.strip():
            with self._lock:
                self._sensory_notes.append(note.strip())

    def get_sensory_notes(self) -> list[str]:
        """Return all retained sensory notes (up to ``maxlen``)."""
        with self._lock:
            return list(self._sensory_notes)

    def clear_sensory_notes(self) -> None:
        """Erase all retained sensory annotations."""
        with self._lock:
            self._sensory_notes.clear()

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def clear_all(self) -> None:
        """Reset the memory store completely."""
        with self._lock:
            self._history.clear()
            self._sensory_notes.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_if_needed(self) -> None:
        """Remove oldest user+assistant pair when the window is full.

        Called with ``self._lock`` already held.
        """
        # Count pairs: each pair is 2 messages
        while len(self._history) > self.max_turns * 2:
            # Drop the oldest message (could be user or assistant)
            self._history.popleft()
