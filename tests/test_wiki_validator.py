import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "profiles/wiki-maintainer/skills/audit-vault-links/scripts/validate-vault.py"


class VaultValidatorTests(unittest.TestCase):
    def canonical_note(self, title="Canonical Name", extra_frontmatter="", status="verified"):
        return (
            "---\n"
            f"title: {title}\n"
            "last_reviewed: 2026-10-02\n"
            'review_after: "90 days"\n'
            "sources:\n"
            "  - url: https://example.com/source\n"
            "    published_at: unknown\n"
            "    retrieved_at: 2026-10-02\n"
            f"{extra_frontmatter}"
            "---\n"
            f"# {title}\n\n"
            "## Evidence ledger\n\n"
            "| Claim | Source / inspected passage | Published / updated | Retrieved | Scope / version | Status | Affected / updated page |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            f"| Example claim | https://example.com/source, section 2 | unknown | 2026-10-02 | Example conditions | {status} | this page |\n"
        )

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
            (concepts / "canonical.md").write_text(self.canonical_note(extra_frontmatter="aliases:\n  - Display Name\n"), encoding="utf-8")
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
            (concepts / "canonical.md").write_text(self.canonical_note(), encoding="utf-8")
            (root / "index.md").write_text(
                "---\ntitle: Index\n---\n[[concepts/canonical|Unlisted Name]]\n",
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("declared note alias", result.stdout)

    def test_canonical_page_requires_freshness_provenance_and_ledger_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            concepts.mkdir()
            (concepts / "canonical.md").write_text(
                self.canonical_note(status="supported"), encoding="utf-8"
            )
            result = self.run_validator(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("Evidence ledger needs at least one complete row", result.stdout)

    def test_canonical_page_requires_freshness_and_source_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            concepts.mkdir()
            (concepts / "canonical.md").write_text(
                "---\ntitle: Canonical Name\n---\n# Canonical Name\n",
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("last_reviewed", result.stdout)
            self.assertIn("review_after", result.stdout)
            self.assertIn("non-empty sources list", result.stdout)

    def test_canonical_frontmatter_uses_full_yaml_and_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            concepts.mkdir()
            text = self.canonical_note(extra_frontmatter="tags: [alpha, beta]\n")
            (concepts / "valid.md").write_text(text, encoding="utf-8")
            (concepts / "duplicate.md").write_text(
                text.replace("tags: [alpha, beta]\n", "title: Shadow\ntags: [alpha, beta]\n"),
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("duplicate key 'title'", result.stdout)

    def test_hub_is_not_required_to_have_an_evidence_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hubs = root / "hubs"
            hubs.mkdir()
            (hubs / "index.md").write_text("---\ntitle: Topic index\n---\n# Topic index\n", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
