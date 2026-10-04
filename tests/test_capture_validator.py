import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "profiles/web-scraper/skills/web-clipper/scripts/validate-capture.py"


def render_capture(body: bytes, *, status: str = "complete", extra: str = "") -> bytes:
    digest = hashlib.sha256(body).hexdigest()
    frontmatter = (
        "---\n"
        'title: "Example"\n'
        'aliases: "Example display name"\n'
        'supplied_url: "https://example.com/input"\n'
        'canonical_url: "https://example.com/article"\n'
        'source: "https://example.com/article"\n'
        'published_at: "unknown"\n'
        'clipped: "2026-10-02"\n'
        'retrieved_at: "2026-10-02T10:00:00Z"\n'
        f'capture_status: "{status}"\n'
        'capture_method: "firecrawl"\n'
        'provider: "test"\n'
        'model: "test"\n'
        f'content_sha256: "{digest}"\n'
        f"{extra}"
        "---\n"
    ).encode()
    return frontmatter + body


class CaptureValidatorTests(unittest.TestCase):
    def run_validator(self, path: Path, root: Path | None = None):
        command = [sys.executable, str(VALIDATOR), str(path), "--json"]
        if root is not None:
            command.extend(("--root", str(root)))
        return subprocess.run(command, check=False, capture_output=True, text=True)

    def test_invalid_yaml_is_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"# Example\n", extra="invalid yaml line\n"))
            result = self.run_validator(path, root)
            self.assertEqual(1, result.returncode)
            self.assertIn("invalid YAML frontmatter", json.loads(result.stdout)["errors"][0])

    def test_full_yaml_sequences_and_nested_mappings_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            extra = "capture_details: {headers: [content-type, etag], browser: {used: false}}\n"
            path.write_bytes(render_capture(b"# Example\nBody.\n", extra=extra))
            result = self.run_validator(path, root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("complete", json.loads(result.stdout)["outcome"])

    def test_duplicate_yaml_keys_are_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"# Example\n", extra='title: "Shadow"\n'))
            result = self.run_validator(path, root)
            self.assertEqual(1, result.returncode)
            self.assertIn("duplicate key", json.loads(result.stdout)["errors"][0])

    def test_changed_body_with_stale_hash_is_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"# Example\nOriginal.\n") + b"Changed.\n")
            result = self.run_validator(path, root)
            self.assertEqual(1, result.returncode)
            self.assertTrue(any("exact Markdown body bytes" in error for error in json.loads(result.stdout)["errors"]))

    def test_valid_display_alias_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"# Example\nBody.\n"))
            result = self.run_validator(path, root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("complete", json.loads(result.stdout)["outcome"])

    def test_wrong_workspace_root_is_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed = root / "allowed"
            other = root / "other"
            allowed.mkdir()
            other.mkdir()
            path = other / "capture.md"
            path.write_bytes(render_capture(b"# Example\nBody.\n"))
            result = self.run_validator(path, allowed)
            self.assertEqual(1, result.returncode)
            self.assertIn("outside expected root", json.loads(result.stdout)["errors"][0])

    def test_expected_deferred_input_is_valid_and_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"Body is incomplete.\n", status="partial"))
            result = self.run_validator(path, root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("deferred", json.loads(result.stdout)["outcome"])

    def test_error_page_cannot_be_marked_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capture.md"
            path.write_bytes(render_capture(b"# Access denied\nRequest blocked.\n"))
            result = self.run_validator(path, root)
            self.assertEqual(1, result.returncode)
            self.assertTrue(any("error/challenge page" in error for error in json.loads(result.stdout)["errors"]))

    def test_shell_and_failed_are_valid_distinct_dispositions(self):
        for status in ("shell", "failed"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "capture.md"
                path.write_bytes(render_capture(b"", status=status))
                result = self.run_validator(path, root)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(status, json.loads(result.stdout)["outcome"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
