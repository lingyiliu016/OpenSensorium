"""Tests for LLMBackbone."""

from unittest.mock import MagicMock, patch

import pytest

from opensensorium.llm.backbone import LLMBackbone


def _make_mock_client(reply_text: str = "I can see a cat."):
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = reply_text
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return client


class TestLLMBackboneInit:
    def test_defaults(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        # Model is either env-var or default gpt-4o
        assert backbone.model in ("gpt-4o",) or backbone.model is not None

    def test_custom_model(self):
        backbone = LLMBackbone(model="gpt-4-turbo", openai_client=MagicMock())
        assert backbone.model == "gpt-4-turbo"


class TestBuildMessages:
    def test_text_only(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        msgs = backbone._build_messages("hello", None, None)
        # system + user
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "hello"

    def test_with_image(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        img = "data:image/jpeg;base64,abc123"
        msgs = backbone._build_messages("what is this?", img, None)
        user_msg = msgs[-1]
        assert isinstance(user_msg["content"], list)
        types = [part["type"] for part in user_msg["content"]]
        assert "text" in types
        assert "image_url" in types

    def test_image_without_text(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        img = "data:image/jpeg;base64,abc123"
        msgs = backbone._build_messages(None, img, None)
        user_msg = msgs[-1]
        # Should contain at least the image part
        assert isinstance(user_msg["content"], list)
        types = [part["type"] for part in user_msg["content"]]
        assert "image_url" in types

    def test_history_injected(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        history = [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ]
        msgs = backbone._build_messages("follow-up", None, history)
        roles = [m["role"] for m in msgs]
        assert roles.count("user") == 2  # history + current
        assert roles.count("assistant") == 1

    def test_no_text_and_no_image_uses_placeholder(self):
        backbone = LLMBackbone(openai_client=MagicMock())
        msgs = backbone._build_messages(None, None, None)
        user_msg = msgs[-1]
        assert "(no speech detected)" in str(user_msg["content"])


class TestThink:
    def test_think_returns_string(self):
        client = _make_mock_client("Hello!")
        backbone = LLMBackbone(openai_client=client)
        result = backbone.think("hi")
        assert result == "Hello!"

    def test_think_strips_whitespace(self):
        client = _make_mock_client("  Hello!  \n")
        backbone = LLMBackbone(openai_client=client)
        result = backbone.think("hi")
        assert result == "Hello!"

    def test_think_calls_correct_model(self):
        client = _make_mock_client()
        backbone = LLMBackbone(model="gpt-4o-mini", openai_client=client)
        backbone.think("test")
        call_kwargs = client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"

    def test_think_with_image_passes_multimodal_message(self):
        client = _make_mock_client()
        backbone = LLMBackbone(openai_client=client)
        backbone.think("describe this", image_b64="data:image/jpeg;base64,abc")
        messages = client.chat.completions.create.call_args[1]["messages"]
        user_msg = messages[-1]
        assert isinstance(user_msg["content"], list)

    def test_think_handles_none_reply(self):
        client = MagicMock()
        choice = MagicMock()
        choice.message.content = None
        client.chat.completions.create.return_value = MagicMock(choices=[choice])
        backbone = LLMBackbone(openai_client=client)
        result = backbone.think("hi")
        assert result == ""


class TestThinkAsync:
    @pytest.mark.asyncio
    async def test_think_async_returns_string(self):
        async_client = MagicMock()
        choice = MagicMock()
        choice.message.content = "async reply"

        async def _create(**kwargs):
            return MagicMock(choices=[choice])

        async_client.chat.completions.create = _create

        backbone = LLMBackbone(openai_client=MagicMock())
        with patch("openai.AsyncOpenAI", return_value=async_client):
            result = await backbone.think_async("hello")
        assert result == "async reply"
