import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from file_lock import acquire


class FileLockTests(unittest.TestCase):
    def test_other_process_is_excluded_and_close_releases(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'worker.lock'
            script = ('from file_lock import acquire; import sys; '
                      'f=open(sys.argv[1], "a"); acquire(f)')
            with path.open('a') as lock:
                acquire(lock)
                result = subprocess.run([sys.executable, '-c', script, str(path)],
                                        cwd=Path(__file__).parent, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'BlockingIOError', result.stderr)
            result = subprocess.run([sys.executable, '-c', script, str(path)],
                                    cwd=Path(__file__).parent, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
