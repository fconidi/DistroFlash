"""Bounded transfers and readback verification shared by both image paths."""
import hashlib

CHUNK = 4 * 1024**2


class TransferError(OSError):
    pass


class Cancelled(Exception):
    pass


def checkpoint(cancel=None):
    if cancel is not None and cancel.is_set():
        raise Cancelled("Operazione annullata: il supporto può essere incompleto.")


def copy_stream(source, target, size, cancel=None, progress=None):
    digest = hashlib.sha256()
    done = 0
    while done < size:
        checkpoint(cancel)
        block = source.read(min(CHUNK, size - done))
        if not block:
            raise TransferError("La sorgente è più corta del previsto.")
        view = memoryview(block)
        while view:
            checkpoint(cancel)
            written = target.write(view)
            if written is None or written <= 0:
                raise TransferError("Scrittura incompleta sul dispositivo.")
            view = view[written:]
        digest.update(block)
        done += len(block)
        if progress:
            progress(done, size)
    checkpoint(cancel)
    if source.read(1):
        raise TransferError("La sorgente è cambiata durante la copia.")
    return digest.hexdigest()


def verify_stream(source, size, expected, cancel=None, progress=None):
    digest = hashlib.sha256()
    done = 0
    while done < size:
        checkpoint(cancel)
        block = source.read(min(CHUNK, size - done))
        if not block:
            raise TransferError("Rilettura incompleta del dispositivo.")
        digest.update(block)
        done += len(block)
        if progress:
            progress(done, size)
    checkpoint(cancel)
    if digest.hexdigest() != expected:
        raise TransferError("Verifica fallita: i dati riletti sono diversi dalla sorgente.")
