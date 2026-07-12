"""
AudioSensor — listens to the microphone and speaks responses aloud.

Speech-to-text (STT)
---------------------
Uses the OpenAI Whisper API by default.  In offline mode (``stt_backend="local"``)
``faster-whisper`` is used if available, otherwise the module falls back to a
simple pyaudio-based raw PCM dump that the caller can process externally.

Text-to-speech (TTS)
---------------------
Defaults to the OpenAI TTS API (``tts_backend="openai"``).  An offline
alternative using ``pyttsx3`` can be selected with ``tts_backend="pyttsx3"``.

Audio I/O
---------
Microphone capture uses ``pyaudio``.  Playback uses ``sounddevice`` + ``soundfile``
so that MP3 / WAV / OGG files returned by the TTS API can be played directly.
"""

from __future__ import annotations

import io
import logging
import threading
import time
import wave
from typing import Optional

logger = logging.getLogger(__name__)

# Default recording parameters
_SAMPLE_RATE = 16_000  # Hz  — Whisper works best at 16 kHz
_CHANNELS = 1
_CHUNK_SIZE = 1_024    # frames per pyaudio read
_SILENCE_THRESHOLD = 500  # RMS amplitude below which we consider silence
_SILENCE_DURATION = 1.5   # seconds of silence → end of utterance


class AudioSensor:
    """Captures microphone input and converts it to text; speaks text aloud.

    Parameters
    ----------
    stt_backend:
        ``"openai"`` (Whisper API) or ``"local"`` (faster-whisper / pyaudio raw).
    tts_backend:
        ``"openai"`` (OpenAI TTS API) or ``"pyttsx3"`` (offline).
    tts_voice:
        Voice name used by the OpenAI TTS API (e.g. ``"alloy"``, ``"nova"``).
    language:
        BCP-47 language hint passed to Whisper (e.g. ``"zh"`` for Chinese,
        ``"en"`` for English, ``None`` for auto-detect).
    openai_client:
        A pre-configured ``openai.OpenAI`` (or ``AsyncOpenAI``) client.  When
        ``None`` the sensor creates a synchronous client from the environment.
    """

    def __init__(
        self,
        stt_backend: str = "openai",
        tts_backend: str = "openai",
        tts_voice: str = "alloy",
        language: Optional[str] = None,
        openai_client=None,
    ) -> None:
        self.stt_backend = stt_backend
        self.tts_backend = tts_backend
        self.tts_voice = tts_voice
        self.language = language
        self._client = openai_client
        self._speaking = threading.Event()

    # ------------------------------------------------------------------
    # STT — listen and transcribe
    # ------------------------------------------------------------------

    def listen(self, timeout: float = 10.0) -> Optional[str]:
        """Block until a complete utterance is detected, then return transcript.

        Parameters
        ----------
        timeout:
            Maximum seconds to wait for speech before returning ``None``.

        Returns
        -------
        Transcribed text string, or ``None`` if no speech was detected.
        """
        audio_bytes = self._record_utterance(timeout=timeout)
        if audio_bytes is None:
            return None
        return self._transcribe(audio_bytes)

    # ------------------------------------------------------------------
    # TTS — speak text
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Synthesise *text* to speech and play it through the speakers.

        Parameters
        ----------
        text:
            The string to speak aloud.
        """
        if not text or not text.strip():
            return
        self._speaking.set()
        try:
            if self.tts_backend == "pyttsx3":
                self._speak_pyttsx3(text)
            else:
                self._speak_openai(text)
        finally:
            self._speaking.clear()

    @property
    def is_speaking(self) -> bool:
        """``True`` while the agent is currently playing TTS audio."""
        return self._speaking.is_set()

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    def _record_utterance(self, timeout: float = 10.0) -> Optional[bytes]:
        """Record microphone audio until silence, returning raw WAV bytes."""
        try:
            import pyaudio  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "pyaudio is required for microphone input. "
                "Install it with: pip install pyaudio"
            ) from exc

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=_CHANNELS,
            rate=_SAMPLE_RATE,
            input=True,
            frames_per_buffer=_CHUNK_SIZE,
        )

        frames: list[bytes] = []
        silence_chunks = 0
        silence_limit = int(_SILENCE_DURATION * _SAMPLE_RATE / _CHUNK_SIZE)
        max_chunks = int(timeout * _SAMPLE_RATE / _CHUNK_SIZE)
        got_speech = False

        logger.debug("AudioSensor: listening…")
        try:
            for _ in range(max_chunks):
                if self.is_speaking:
                    # Don't capture our own TTS output
                    time.sleep(0.05)
                    continue
                chunk = stream.read(_CHUNK_SIZE, exception_on_overflow=False)
                frames.append(chunk)
                rms = self._rms(chunk)
                if rms > _SILENCE_THRESHOLD:
                    got_speech = True
                    silence_chunks = 0
                else:
                    silence_chunks += 1

                if got_speech and silence_chunks >= silence_limit:
                    break
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        if not got_speech:
            return None

        return self._frames_to_wav(frames)

    @staticmethod
    def _rms(chunk: bytes) -> float:
        """Compute the root-mean-square amplitude of a raw PCM chunk."""
        import array
        import math

        shorts = array.array("h", chunk)
        if not shorts:
            return 0.0
        mean_sq = sum(s * s for s in shorts) / len(shorts)
        return math.sqrt(mean_sq)

    @staticmethod
    def _frames_to_wav(frames: list[bytes]) -> bytes:
        """Wrap PCM frames in a WAV container."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(_CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(_SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Transcription helpers
    # ------------------------------------------------------------------

    def _transcribe(self, wav_bytes: bytes) -> Optional[str]:
        if self.stt_backend == "local":
            return self._transcribe_local(wav_bytes)
        return self._transcribe_openai(wav_bytes)

    def _transcribe_openai(self, wav_bytes: bytes) -> Optional[str]:
        client = self._get_client()
        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "audio.wav"  # openai SDK reads the name for MIME type
        kwargs: dict = {"model": "whisper-1", "file": audio_file}
        if self.language:
            kwargs["language"] = self.language
        result = client.audio.transcriptions.create(**kwargs)
        text = result.text.strip()
        logger.debug("STT transcript: %r", text)
        return text if text else None

    def _transcribe_local(self, wav_bytes: bytes) -> Optional[str]:
        try:
            from faster_whisper import WhisperModel  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is required for local STT. "
                "Install it with: pip install faster-whisper"
            ) from exc
        model = WhisperModel("base", device="cpu", compute_type="int8")
        audio_io = io.BytesIO(wav_bytes)
        segments, _ = model.transcribe(audio_io, language=self.language)
        text = " ".join(seg.text for seg in segments).strip()
        return text if text else None

    # ------------------------------------------------------------------
    # TTS helpers
    # ------------------------------------------------------------------

    def _speak_openai(self, text: str) -> None:
        client = self._get_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=self.tts_voice,
            input=text,
            response_format="wav",
        )
        audio_bytes = response.content
        self._play_wav_bytes(audio_bytes)

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            import pyttsx3  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "pyttsx3 is required for the offline TTS backend. "
                "Install it with: pip install pyttsx3"
            ) from exc
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    @staticmethod
    def _play_wav_bytes(wav_bytes: bytes) -> None:
        try:
            import sounddevice as sd  # noqa: PLC0415
            import soundfile as sf  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice and soundfile are required for audio playback. "
                "Install them with: pip install sounddevice soundfile"
            ) from exc
        buf = io.BytesIO(wav_bytes)
        data, samplerate = sf.read(buf, dtype="float32")
        sd.play(data, samplerate)
        sd.wait()

    # ------------------------------------------------------------------
    # Client helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            import openai  # noqa: PLC0415
            self._client = openai.OpenAI()
        return self._client
