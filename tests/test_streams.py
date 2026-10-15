import io
from pathlib import Path
import tempfile
import threading
import unittest
from distroflash.streams import Cancelled, TransferError, copy_stream, verify_stream


class ShortWriter(io.BytesIO):
    def write(self, value):
        return super().write(value[:3])


class StreamTests(unittest.TestCase):
    def test_partial_writes_are_completed(self):
        target = ShortWriter()
        source = b"bytes to copy" * 100
        digest = copy_stream(io.BytesIO(source), target, len(source))
        self.assertEqual(target.getvalue(), source)
        target.seek(0)
        verify_stream(target, len(source), digest)

    def test_truncated_source_is_rejected(self):
        with self.assertRaises(TransferError):
            copy_stream(io.BytesIO(b"abc"), io.BytesIO(), 10)

    def test_growing_source_is_rejected(self):
        with self.assertRaises(TransferError):
            copy_stream(io.BytesIO(b"abcdef"), io.BytesIO(), 3)

    def test_corruption_is_detected(self):
        target = io.BytesIO()
        digest = copy_stream(io.BytesIO(b"abc"), target, 3)
        with self.assertRaises(TransferError):
            verify_stream(io.BytesIO(b"abd"), 3, digest)

    def test_readback_shorter_than_image_is_rejected(self):
        with self.assertRaises(TransferError):
            verify_stream(io.BytesIO(b"a"), 3, "irrelevant")

    def test_cancel_before_copy_leaves_target_untouched(self):
        event = threading.Event()
        event.set()
        target = io.BytesIO()
        with self.assertRaises(Cancelled):
            copy_stream(io.BytesIO(b"abc"), target, 3, event)
        self.assertEqual(target.getvalue(), b"")

    def test_copy_and_readback_on_real_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = bytes(range(256)) * 10000
            with (Path(tmp)/"target").open("w+b", buffering=0) as target:
                digest = copy_stream(io.BytesIO(data), target, len(data))
                target.seek(0)
                verify_stream(target, len(data), digest)


if __name__ == "__main__":
    unittest.main()
