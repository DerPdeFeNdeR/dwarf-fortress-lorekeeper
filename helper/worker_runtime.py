"""Single-worker ownership and heartbeat independent of model execution."""
from file_lock import acquire
import os
import threading
import time
from contextlib import contextmanager
from process_queue import write_results


@contextmanager
def worker_runtime(save_directory):
    stop = threading.Event()
    lock = (save_directory / '.lorekeeper-worker.lock').open('a')
    try:
        acquire(lock)
    except BlockingIOError:
        lock.close()
        raise RuntimeError('A Lorekeeper watcher already owns this save directory.')
    def heartbeat():
        while not stop.is_set():
            try:
                write_results(save_directory / 'lorekeeper-worker.json',
                              {'pid': os.getpid(), 'updated_at': time.time()})
            except OSError as error:
                print(f'Lorekeeper: heartbeat write failed: {error}', flush=True)
            stop.wait(5)
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()
        lock.close()
