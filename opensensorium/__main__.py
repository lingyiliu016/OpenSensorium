"""CLI entry point for OpenSensorium.

Usage
-----
    python -m opensensorium [options]

or, after ``pip install -e .``:

    opensensorium [options]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="opensensorium",
        description=(
            "OpenSensorium — a human/animal-like AI agent grounded in vision "
            "and voice interaction."
        ),
    )
    p.add_argument(
        "--no-vision",
        action="store_true",
        default=False,
        help="Disable camera input (useful when no webcam is connected).",
    )
    p.add_argument(
        "--camera",
        type=int,
        default=0,
        metavar="INDEX",
        help="Camera device index (default: 0).",
    )
    p.add_argument(
        "--static-image",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to a static image to use instead of a live camera.",
    )
    p.add_argument(
        "--stt",
        choices=["openai", "local"],
        default="openai",
        help="Speech-to-text backend (default: openai).",
    )
    p.add_argument(
        "--tts",
        choices=["openai", "pyttsx3"],
        default="openai",
        help="Text-to-speech backend (default: openai).",
    )
    p.add_argument(
        "--voice",
        default="alloy",
        metavar="VOICE",
        help=(
                "OpenAI TTS voice name (default: alloy). "
                "Options: alloy, echo, fable, onyx, nova, shimmer."
            ),
    )
    p.add_argument(
        "--language",
        default=None,
        metavar="LANG",
        help="BCP-47 language code hint for STT, e.g. 'zh' or 'en' (default: auto-detect).",
    )
    p.add_argument(
        "--model",
        default=None,
        metavar="MODEL",
        help="OpenAI model to use (default: gpt-4o, or OPENSENSORIUM_MODEL env var).",
    )
    p.add_argument(
        "--listen-timeout",
        type=float,
        default=10.0,
        metavar="SECS",
        help="Seconds to wait for speech before looping (default: 10).",
    )
    p.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        default=False,
        help="Run the agent loop using asyncio.",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    load_dotenv()

    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Validate that OPENAI_API_KEY is set (required for default backends)
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY environment variable is not set.\n"
            "Please set it before running OpenSensorium:\n\n"
            "  export OPENAI_API_KEY='sk-...'\n\n"
            "Or create a .env file with OPENAI_API_KEY=sk-...",
            file=sys.stderr,
        )
        sys.exit(1)

    from opensensorium.agent import SensoriumAgent
    from opensensorium.audio.sensor import AudioSensor
    from opensensorium.llm.backbone import LLMBackbone
    from opensensorium.vision.sensor import VisionBackend, VisionSensor

    # Build sub-components
    if args.no_vision:
        vision = VisionSensor(backend=VisionBackend.STATIC, static_image_path=None)
    elif args.static_image:
        vision = VisionSensor(backend=VisionBackend.STATIC, static_image_path=args.static_image)
    else:
        vision = VisionSensor(backend=VisionBackend.OPENCV, device_index=args.camera)

    audio = AudioSensor(
        stt_backend=args.stt,
        tts_backend=args.tts,
        tts_voice=args.voice,
        language=args.language,
    )

    llm = LLMBackbone(model=args.model)

    agent = SensoriumAgent(
        vision=vision,
        audio=audio,
        llm=llm,
        use_vision=not args.no_vision,
        listen_timeout=args.listen_timeout,
    )

    if args.use_async:
        asyncio.run(agent.run_async())
    else:
        agent.run()


if __name__ == "__main__":
    main()
