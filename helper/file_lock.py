"""Nonblocking process locks; closing the file releases ownership."""
import os

if os.name == 'nt':
    import msvcrt
else:
    import fcntl


def acquire(lock):
    if os.name == 'nt':
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno in (13, 11, 36):
                raise BlockingIOError('Another process owns this lock') from error
            raise
    else:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
