# OpenSensorium

> **做一个真正像人/动物的智能体。视觉、语音交互是第一性原理。**  
> *Build a truly human/animal-like AI agent. Vision and voice interaction are first principles.*

OpenSensorium is an embodied AI agent that perceives the world through a **camera** and a **microphone** — just like a person or an animal — and responds through natural **speech**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SensoriumAgent                           │
│                                                                 │
│  ① PERCEIVE          ② THINK             ③ ACT                 │
│  ┌──────────┐        ┌───────────┐        ┌──────────────────┐  │
│  │ Vision   │──────▶ │           │        │   AudioSensor    │  │
│  │ Sensor   │ frame  │    LLM    │──────▶ │   .speak(reply)  │  │
│  │ (camera) │        │  Backbone │ reply  └──────────────────┘  │
│  └──────────┘        │ (GPT-4o)  │                              │
│                      │           │        ┌──────────────────┐  │
│  ┌──────────┐        │           │◀──────│  AgentMemory     │  │
│  │ Audio    │──────▶ │           │history │  (rolling ctx)   │  │
│  │ Sensor   │ speech └───────────┘        └──────────────────┘  │
│  │ (Whisper)│                                                    │
│  └──────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Sub-modules

| Module | Description |
|--------|-------------|
| `opensensorium/vision/sensor.py` | Captures frames from a webcam (OpenCV) or a static image; encodes them as base-64 JPEG for the LLM |
| `opensensorium/audio/sensor.py` | Records microphone input, transcribes via Whisper, and plays TTS replies via OpenAI or pyttsx3 |
| `opensensorium/llm/backbone.py` | Multimodal LLM backbone (GPT-4o by default) that assembles vision + audio + memory into a single request |
| `opensensorium/memory/store.py` | Rolling conversation window + sensory annotations (thread-safe) |
| `opensensorium/agent.py` | Main perceive→think→act loop (sync and async) |
| `opensensorium/__main__.py` | CLI entry point |

---

## Quick Start

### 1. Install

```bash
# System dependency for microphone access
sudo apt-get install portaudio19-dev    # Debian/Ubuntu
# brew install portaudio                # macOS

pip install -e ".[dev]"
```

### 2. Set environment variables

```bash
cp .env.example .env      # then edit .env
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:

```
OPENAI_API_KEY=sk-...
OPENSENSORIUM_MODEL=gpt-4o   # optional, default: gpt-4o
```

### 3. Run

```bash
# Default: webcam + microphone + OpenAI backends
python -m opensensorium

# Chinese language hint, offline TTS
python -m opensensorium --language zh --tts pyttsx3

# No camera (voice-only mode)
python -m opensensorium --no-vision

# Use a static image instead of a live webcam
python -m opensensorium --static-image path/to/image.jpg

# Async event-loop mode
python -m opensensorium --async

# Verbose logging
python -m opensensorium -v
```

### CLI options

```
usage: opensensorium [options]

  --no-vision           Disable camera input
  --camera INDEX        Camera device index (default: 0)
  --static-image PATH   Use a static image instead of a live camera
  --stt {openai,local}  STT backend (default: openai / Whisper API)
  --tts {openai,pyttsx3} TTS backend (default: openai)
  --voice VOICE         OpenAI TTS voice (default: alloy)
  --language LANG       BCP-47 STT language hint (e.g. zh, en)
  --model MODEL         OpenAI model (default: gpt-4o)
  --listen-timeout SECS Seconds to wait for speech (default: 10)
  --async               Use asyncio event loop
  -v, --verbose         Debug logging
```

---

## Programmatic API

```python
from opensensorium import SensoriumAgent
from opensensorium.vision.sensor import VisionSensor, VisionBackend
from opensensorium.audio.sensor import AudioSensor
from opensensorium.llm.backbone import LLMBackbone

agent = SensoriumAgent(
    vision=VisionSensor(backend=VisionBackend.OPENCV, device_index=0),
    audio=AudioSensor(tts_voice="nova", language="zh"),
    llm=LLMBackbone(model="gpt-4o"),
    listen_timeout=8.0,
)

agent.run()           # synchronous loop (Ctrl-C to stop)
# or
import asyncio
asyncio.run(agent.run_async())
```

---

## Development

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opensensorium --cov-report=term-missing

# Lint
ruff check opensensorium tests
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `OPENSENSORIUM_MODEL` | `gpt-4o` | Chat-completion model |

---

## License

MIT
