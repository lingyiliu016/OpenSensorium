"""Tests for AgentMemory."""

import pytest

from opensensorium.memory.store import AgentMemory


class TestAgentMemoryBasics:
    def test_initially_empty(self):
        mem = AgentMemory()
        assert mem.turn_count == 0
        assert mem.get_history() == []

    def test_add_user_and_assistant(self):
        mem = AgentMemory()
        mem.add_user_turn("Hello")
        mem.add_assistant_turn("Hi there!")
        history = mem.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}

    def test_turn_count_increases(self):
        mem = AgentMemory()
        mem.add_user_turn("a")
        assert mem.turn_count == 1
        mem.add_assistant_turn("b")
        assert mem.turn_count == 2

    def test_clear_history(self):
        mem = AgentMemory()
        mem.add_user_turn("a")
        mem.add_assistant_turn("b")
        mem.clear_history()
        assert mem.turn_count == 0
        assert mem.get_history() == []

    def test_max_turns_eviction(self):
        mem = AgentMemory(max_turns=2)
        for i in range(5):
            mem.add_user_turn(f"user {i}")
            mem.add_assistant_turn(f"assistant {i}")
        # max_turns=2 → keeps the most recent 2 pairs (4 messages)
        assert mem.turn_count <= 4

    def test_invalid_max_turns(self):
        with pytest.raises(ValueError):
            AgentMemory(max_turns=0)


class TestSensoryNotes:
    def test_add_and_retrieve(self):
        mem = AgentMemory()
        mem.add_sensory_note("A cat is sitting on the table")
        notes = mem.get_sensory_notes()
        assert len(notes) == 1
        assert notes[0] == "A cat is sitting on the table"

    def test_sensory_notes_injected_into_history(self):
        mem = AgentMemory()
        mem.add_sensory_note("bright sunlight")
        history = mem.get_history()
        # The sensory note should appear as a system message prepended to history
        assert any(
            msg["role"] == "system" and "bright sunlight" in msg["content"]
            for msg in history
        )

    def test_blank_notes_ignored(self):
        mem = AgentMemory()
        mem.add_sensory_note("   ")
        mem.add_sensory_note("")
        assert mem.get_sensory_notes() == []

    def test_clear_sensory_notes(self):
        mem = AgentMemory()
        mem.add_sensory_note("something")
        mem.clear_sensory_notes()
        assert mem.get_sensory_notes() == []

    def test_max_sensory_notes_window(self):
        mem = AgentMemory()
        for i in range(10):
            mem.add_sensory_note(f"observation {i}")
        # Internal deque maxlen is 5
        notes = mem.get_sensory_notes()
        assert len(notes) <= 5

    def test_clear_all(self):
        mem = AgentMemory()
        mem.add_user_turn("hi")
        mem.add_sensory_note("something")
        mem.clear_all()
        assert mem.turn_count == 0
        assert mem.get_sensory_notes() == []


class TestMultimodalContent:
    def test_user_turn_with_list_content(self):
        mem = AgentMemory()
        content = [
            {"type": "text", "text": "what do you see?"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
        ]
        mem.add_user_turn(content)
        history = mem.get_history()
        assert history[0]["content"] == content
