"""
VisionSensor — captures frames from a camera and encodes them for the LLM.

The sensor supports two backends:
  * ``opencv``  — reads frames from a local webcam via OpenCV (default).
  * ``static``  — accepts a pre-supplied image path (useful for testing or
                   when running without a physical camera).

Frames are base-64 encoded as JPEG so they can be embedded directly inside
an OpenAI ``image_url`` message part.
"""

from __future__ import annotations

import base64
import logging
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class VisionBackend(str, Enum):
    OPENCV = "opencv"
    STATIC = "static"


class VisionSensor:
    """Continuously captures frames from a camera (or static image source).

    Parameters
    ----------
    backend:
        Which capture backend to use (``"opencv"`` or ``"static"``).
    device_index:
        Camera device index passed to ``cv2.VideoCapture`` (default ``0``).
    static_image_path:
        Path to a static image used when ``backend="static"``.
    fps:
        Target capture rate when running the background capture loop.
    """

    def __init__(
        self,
        backend: VisionBackend | str = VisionBackend.OPENCV,
        device_index: int = 0,
        static_image_path: Optional[str | Path] = None,
        fps: float = 1.0,
    ) -> None:
        self.backend = VisionBackend(backend)
        self.device_index = device_index
        self.static_image_path = Path(static_image_path) if static_image_path else None
        self.fps = fps

        self._cap = None  # cv2.VideoCapture, opened lazily
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._capture_thread: Optional[threading.Thread] = None
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open the capture device and start the background frame-grab loop."""
        if self.backend == VisionBackend.STATIC:
            self._load_static_image()
            return

        self._open_camera()
        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop, name="vision-capture", daemon=True
        )
        self._capture_thread.start()
        logger.info("VisionSensor started (device=%d, fps=%.1f)", self.device_index, self.fps)

    def stop(self) -> None:
        """Stop capturing and release the camera device."""
        self._running = False
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=3.0)
            self._capture_thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("VisionSensor stopped")

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the most recently captured frame (BGR, HxWxC uint8), or ``None``."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def get_frame_b64(self, quality: int = 80) -> Optional[str]:
        """Return the latest frame encoded as a base-64 JPEG string.

        Parameters
        ----------
        quality:
            JPEG compression quality (1–100).  Lower → smaller payload.

        Returns
        -------
        A ``data:image/jpeg;base64,<data>`` string suitable for embedding in
        an OpenAI multimodal message, or ``None`` if no frame is available.
        """
        frame = self.get_frame()
        if frame is None:
            return None
        return self._encode_frame(frame, quality=quality)

    @property
    def is_available(self) -> bool:
        """``True`` if the sensor has at least one captured frame ready."""
        with self._lock:
            return self._latest_frame is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open_camera(self) -> None:
        try:
            import cv2  # imported lazily so the package is optional at test time
        except ImportError as exc:
            raise RuntimeError(
                "opencv-python is required for the 'opencv' backend. "
                "Install it with: pip install opencv-python"
            ) from exc

        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            raise OSError(
                f"Could not open camera device {self.device_index}. "
                "Check that a webcam is connected or use backend='static'."
            )

    def _capture_loop(self) -> None:

        interval = 1.0 / max(self.fps, 0.1)
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame
            else:
                logger.warning("VisionSensor: failed to read frame from camera")
            time.sleep(interval)

    def _load_static_image(self) -> None:
        if self.static_image_path is None or not self.static_image_path.exists():
            raise FileNotFoundError(
                f"Static image not found: {self.static_image_path}"
            )
        try:
            import cv2
            frame = cv2.imread(str(self.static_image_path))
        except ImportError:
            # Fallback: read raw bytes and wrap as 1D array so encode still works
            raw = self.static_image_path.read_bytes()
            frame = np.frombuffer(raw, dtype=np.uint8)

        with self._lock:
            self._latest_frame = frame
        logger.info("VisionSensor loaded static image: %s", self.static_image_path)

    @staticmethod
    def _encode_frame(frame: np.ndarray, quality: int = 80) -> str:
        try:
            import cv2
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, buf = cv2.imencode(".jpg", frame, encode_params)
            if not success:
                raise RuntimeError("cv2.imencode failed")
            raw_bytes = buf.tobytes()
        except ImportError:
            # cv2 not available — assume frame already holds raw JPEG bytes
            raw_bytes = frame.tobytes()

        b64 = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "VisionSensor":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
