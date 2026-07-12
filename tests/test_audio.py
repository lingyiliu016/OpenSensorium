"""Tests for AudioSensor."""

import io
import wave
from unittest.mock import MagicMock, patch

from opensensorium.audio.sensor import _CHANNELS, _SAMPLE_RATE, AudioSensor


def _make_wav_bytes(duration_ms: int = 100) -> bytes:
    """Create a minimal PCM WAV byte string."""
    num_frames = int(_SAMPLE_RATE * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(_CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


class TestAudioSensorInit:
    def test_defaults(self):
        sensor = AudioSensor()
        assert sensor.stt_backend == "openai"
        assert sensor.tts_backend == "openai"
        assert sensor.tts_voice == "alloy"
        assert not sensor.is_speaking

    def test_custom_backends(self):
        sensor = AudioSensor(stt_backend="local", tts_backend="pyttsx3", tts_voice="nova")
        assert sensor.stt_backend == "local"
        assert sensor.tts_backend == "pyttsx3"
        assert sensor.tts_voice == "nova"


class TestRmsHelper:
    def test_silence_returns_low_value(self):
        silent_chunk = b"\x00\x00" * 512
        assert AudioSensor._rms(silent_chunk) == 0.0

    def test_nonzero_signal_returns_positive(self):
        # Alternating +1000 / -1000 samples (int16)
        import array
        shorts = array.array("h", [1000, -1000] * 256)
        chunk = shorts.tobytes()
        rms = AudioSensor._rms(chunk)
        assert rms > 0

    def test_empty_chunk(self):
        assert AudioSensor._rms(b"") == 0.0


class TestFramesToWav:
    def test_produces_valid_wav(self):
        frames = [b"\x00\x00" * 512, b"\x00\x00" * 512]
        wav_bytes = AudioSensor._frames_to_wav(frames)
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == _CHANNELS
            assert wf.getframerate() == _SAMPLE_RATE
            assert wf.getsampwidth() == 2


class TestSTTOpenAI:
    def test_transcribe_calls_openai_api(self):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="hello world")

        sensor = AudioSensor(openai_client=mock_client)
        wav_bytes = _make_wav_bytes()
        result = sensor._transcribe_openai(wav_bytes)

        assert result == "hello world"
        mock_client.audio.transcriptions.create.assert_called_once()

    def test_transcribe_returns_none_for_empty_transcript(self):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="   ")

        sensor = AudioSensor(openai_client=mock_client)
        wav_bytes = _make_wav_bytes()
        result = sensor._transcribe_openai(wav_bytes)

        assert result is None

    def test_transcribe_passes_language_hint(self):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="你好")

        sensor = AudioSensor(openai_client=mock_client, language="zh")
        sensor._transcribe_openai(_make_wav_bytes())

        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs.get("language") == "zh"


class TestTTSOpenAI:
    def test_speak_openai_calls_api(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = _make_wav_bytes()
        mock_client.audio.speech.create.return_value = mock_response

        sensor = AudioSensor(openai_client=mock_client)

        with patch.object(sensor, "_play_wav_bytes") as mock_play:
            sensor._speak_openai("Hello, world!")

        mock_client.audio.speech.create.assert_called_once()
        call_kwargs = mock_client.audio.speech.create.call_args[1]
        assert call_kwargs["input"] == "Hello, world!"
        mock_play.assert_called_once()

    def test_speak_skips_empty_text(self):
        mock_client = MagicMock()
        sensor = AudioSensor(openai_client=mock_client)
        sensor.speak("")  # should not raise or call TTS
        mock_client.audio.speech.create.assert_not_called()

    def test_speaking_flag_cleared_after_speak(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = _make_wav_bytes()
        mock_client.audio.speech.create.return_value = mock_response

        sensor = AudioSensor(openai_client=mock_client)

        with patch.object(sensor, "_play_wav_bytes"):
            sensor.speak("test")

        assert not sensor.is_speaking
