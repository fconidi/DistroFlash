"""Copy to a pinned directory without following destination symlinks."""
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import os
from .streams import checkpoint, copy_stream, verify_stream
from .i18n import tr


@contextmanager
def open_beneath(root, name, create=False):
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or any(p in {".", ".."} for p in parts):
        raise ValueError(tr('Invalid relative path.'))
    parent = os.dup(root) if isinstance(root, int) else os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        volume = os.fstat(parent).st_dev
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, dir_fd=parent)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
            if os.fstat(parent).st_dev != volume:
                raise OSError(tr('The path crosses into another filesystem.'))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY
        fd = os.open(parts[-1], flags | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb" if create else "rb", buffering=0) as stream:
            if os.fstat(stream.fileno()).st_dev != volume:
                raise OSError(tr('The destination filesystem changed.'))
            yield stream
    finally:
        os.close(parent)


def copy_files(entries, destination, cancel=None, progress=None):
    manifest = []
    total = sum(size for _, _, size in entries)
    done = 0
    directory = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for source, name, size in entries:
            checkpoint(cancel)
            with Path(source).open("rb", buffering=0) as reader, open_beneath(directory, name, True) as writer:
                digest = copy_stream(reader, writer, size, cancel,
                                     lambda n, _: progress(done + n, total) if progress else None)
                os.fsync(writer.fileno())
            manifest.append((name, size, digest))
            done += size
    finally:
        os.close(directory)
    return manifest


def verify_files(destination, manifest, cancel=None, progress=None):
    total = sum(size for _, size, _ in manifest)
    done = 0
    directory = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name, size, digest in manifest:
            checkpoint(cancel)
            with open_beneath(directory, name) as reader:
                if os.fstat(reader.fileno()).st_size != size:
                    raise OSError(tr('Size mismatch during verification: ') + name)
                verify_stream(reader, size, digest, cancel,
                              lambda n, _: progress(done + n, total) if progress else None)
            done += size
    finally:
        os.close(directory)
