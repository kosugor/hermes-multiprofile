import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_HELPER = ROOT / "scripts/wiki-writer-lock.py"


class WikiWriterLockTests(unittest.TestCase):
    def run_helper(self, root: Path, *args: str):
        return subprocess.run(
            [sys.executable, str(LOCK_HELPER), "--wiki-root", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_shared_lock_is_exclusive_and_owner_token_controls_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.run_helper(root, "acquire", "--owner", "kanban:t_1:web-scraper")
            self.assertEqual(0, first.returncode, first.stderr)
            lock = json.loads(first.stdout)
            self.assertTrue(lock["acquired"])
            token = lock["owner"]["token"]

            second = self.run_helper(root, "acquire", "--owner", "cron:wiki-clipping-triage")
            self.assertEqual(3, second.returncode)
            second_owner = json.loads(second.stdout)["owner"]
            self.assertEqual("kanban:t_1:web-scraper", second_owner["owner"])
            self.assertNotIn("token", second_owner)

            wrong_release = self.run_helper(root, "release", "--token", "wrong-token")
            self.assertEqual(4, wrong_release.returncode)
            self.assertTrue(json.loads(self.run_helper(root, "inspect").stdout)["locked"])

            release = self.run_helper(root, "release", "--token", token)
            self.assertEqual(0, release.returncode, release.stderr)
            self.assertFalse(json.loads(self.run_helper(root, "inspect").stdout)["locked"])

    def test_concurrent_processes_have_exactly_one_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = [sys.executable, str(LOCK_HELPER), "--wiki-root", str(root), "acquire"]
            first = subprocess.Popen(
                base + ["--owner", "kanban:t_1:wiki-maintainer"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            second = subprocess.Popen(
                base + ["--owner", "cron:wiki-clipping-triage"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            results = [first.communicate(), second.communicate()]
            codes = [first.returncode, second.returncode]
            self.assertCountEqual([0, 3], codes)
            acquired_result = results[codes.index(0)][0]
            token = json.loads(acquired_result)["owner"]["token"]
            released = self.run_helper(root, "release", "--token", token)
            self.assertEqual(0, released.returncode, released.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
