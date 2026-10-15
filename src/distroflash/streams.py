"""Bounded transfers and readback verification shared by both image paths."""
import hashlib
from .i18n import tr

CHUNK = 4 * 1024**2


class TransferError(OSError):
    pass


class Cancelled(Exception):
    pass


def checkpoint(cancel=None):
    if cancel is not None and cancel.is_set():
        raise Cancelled(tr('Operation cancelled: the media may be incomplete.'))


def copy_stream(source, target, size, cancel=None, progress=None):
    digest = hashlib.sha256()
    done = 0
    while done < size:
        checkpoint(cancel)
        block = source.read(min(CHUNK, size - done))
        if not block:
            raise TransferError(tr('The source is shorter than expected.'))
        view = memoryview(block)
        while view:
            checkpoint(cancel)
            written = target.write(view)
            if written is None or written <= 0:
                raise TransferError(tr('Incomplete write to the device.'))
            view = view[written:]
        digest.update(block)
        done += len(block)
        if progress:
            progress(done, size)
    checkpoint(cancel)
    if source.read(1):
        raise TransferError(tr('The source changed during copying.'))
    return digest.hexdigest()


def verify_stream(source, size, expected, cancel=None, progress=None):
    digest = hashlib.sha256()
    done = 0
    while done < size:
        checkpoint(cancel)
        block = source.read(min(CHUNK, size - done))
        if not block:
            raise TransferError(tr('Incomplete device readback.'))
        digest.update(block)
        done += len(block)
        if progress:
            progress(done, size)
    checkpoint(cancel)
    if digest.hexdigest() != expected:
        raise TransferError(tr('Verification failed: readback data differs from the source.'))
