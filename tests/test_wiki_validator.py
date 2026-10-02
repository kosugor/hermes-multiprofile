import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "profiles/wiki-maintainer/skills/audit-vault-links/scripts/validate-vault.py"


class VaultValidatorTests(unittest.TestCase):
    def run_validator(self, root: Path):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_declared_display_alias_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            concepts.mkdir()
            (concepts / "canonical.md").write_text(
                "---\ntitle: Canonical Name\naliases:\n  - Display Name\n---\n# Canonical Name\n",
                encoding="utf-8",
            )
            (root / "index.md").write_text(
                "---\ntitle: Index\n---\n[[concepts/canonical|Display Name]]\n",
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("problems=0", result.stdout)

    def test_undeclared_display_alias_remains_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            concepts.mkdir()
            (concepts / "canonical.md").write_text(
                "---\ntitle: Canonical Name\n---\n# Canonical Name\n",
                encoding="utf-8",
            )
            (root / "index.md").write_text(
                "---\ntitle: Index\n---\n[[concepts/canonical|Unlisted Name]]\n",
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("declared note alias", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
