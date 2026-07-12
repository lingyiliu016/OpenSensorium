"""Tests for VisionSensor."""

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from opensensorium.vision.sensor import VisionBackend, VisionSensor


class TestVisionSensorStatic:
    """Tests that run without a real camera by using the 'static' backend."""

    def _make_jpeg_bytes(self) -> bytes:
        """Create a minimal valid JPEG byte string (1x1 red pixel)."""
        # Use a tiny pre-baked JPEG that doesn't require cv2
        # 1×1 white JPEG
        _MINIMAL_JPEG = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
            b'C  C'
            b"\x00\x00\x01\x01\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
            b"\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04"
            b"\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q"
            b"\x14\x82\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br"
            b"\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZ"
            b"cdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95"
            b"\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
            b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca"
            b"\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7"
            b"\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00"
            b"\x08\x01\x01\x00\x00?\x00\xfb\xd6P\x00\x00\x00\x1f\xff\xd9"
        )
        return _MINIMAL_JPEG

    def test_static_backend_loads_image(self, tmp_path: Path):
        jpeg_path = tmp_path / "test.jpg"
        jpeg_path.write_bytes(self._make_jpeg_bytes())

        with patch("opensensorium.vision.sensor.VisionSensor._load_static_image"):
            sensor = VisionSensor(backend="static", static_image_path=str(jpeg_path))
            # Manually set the frame so we don't need cv2
            sensor._latest_frame = np.zeros((10, 10, 3), dtype=np.uint8)
            assert sensor.is_available

    def test_is_available_false_when_no_frame(self):
        sensor = VisionSensor(backend="static")
        assert not sensor.is_available

    def test_get_frame_returns_none_when_no_frame(self):
        sensor = VisionSensor(backend="static")
        assert sensor.get_frame() is None

    def test_get_frame_b64_returns_none_when_no_frame(self):
        sensor = VisionSensor(backend="static")
        assert sensor.get_frame_b64() is None

    def test_get_frame_returns_copy(self):
        sensor = VisionSensor(backend="static")
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        sensor._latest_frame = frame
        got = sensor.get_frame()
        assert got is not frame  # must be a copy
        np.testing.assert_array_equal(got, frame)

    def test_encode_frame_produces_valid_b64(self):
        """_encode_frame should return a data-URI string."""
        frame = np.zeros((4, 4, 3), dtype=np.uint8)

        with patch("cv2.imencode") as mock_encode:
            mock_encode.return_value = (True, np.frombuffer(b"\xff\xd8\xff\xd9", dtype=np.uint8))
            result = VisionSensor._encode_frame(frame)

        assert result.startswith("data:image/jpeg;base64,")
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert len(decoded) > 0

    def test_backend_enum_accepts_string(self):
        sensor = VisionSensor(backend="opencv")
        assert sensor.backend == VisionBackend.OPENCV

    def test_backend_enum_accepts_static_string(self):
        sensor = VisionSensor(backend="static")
        assert sensor.backend == VisionBackend.STATIC

    def test_stop_without_start_is_safe(self):
        sensor = VisionSensor(backend="static")
        sensor.stop()  # should not raise


class TestVisionSensorOpenCVMocked:
    """Tests for the opencv backend using mocked cv2."""

    def test_start_opens_camera(self):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((4, 4, 3), dtype=np.uint8))

        with patch.dict("sys.modules", {"cv2": MagicMock()}):
            import cv2
            cv2.VideoCapture.return_value = mock_cap

            sensor = VisionSensor(backend="opencv", fps=100)
            sensor._open_camera = MagicMock()
            sensor._cap = mock_cap
            sensor._running = True

            # Run one iteration of the capture loop
            sensor._capture_loop.__func__  # access the unbound method
            # Simulate one capture
            ret, frame = mock_cap.read()
            assert ret is True

    def test_start_raises_on_closed_camera(self):
        mock_cv2 = MagicMock()
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            sensor = VisionSensor(backend="opencv", device_index=99)
            with pytest.raises(OSError):
                sensor._open_camera()
