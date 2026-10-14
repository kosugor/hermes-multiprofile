#!/usr/bin/env python3
"""Regression tests for validate-vault.py."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate-vault.py")
spec = importlib.util.spec_from_file_location("validate_vault", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ValidatorTests(unittest.TestCase):
    def make_vault(self, target: str, source: str) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "wiki/ai/concepts").mkdir(parents=True)
        (root / "wiki/ai/concepts/example.md").write_text(target, encoding="utf-8")
        (root / "source.md").write_text(source, encoding="utf-8")
        return root

    def test_full_path_and_title_alias(self) -> None:
        root = self.make_vault(
            "---\ntitle: Example Note\n---\n# Details\n",
            "[[wiki/ai/concepts/example|Example Note]]\n[[wiki/ai/concepts/example#Details|Example Note]]\n",
        )
        self.assertEqual(module.validate(root), [])

    def test_short_link_is_rejected(self) -> None:
        root = self.make_vault("---\ntitle: Example Note\n---\n", "[[example]]\n")
        self.assertEqual(len(module.validate(root)), 1)

    def test_alias_must_match_title(self) -> None:
        root = self.make_vault("---\ntitle: Example Note\n---\n", "[[wiki/ai/concepts/example|Wrong]]\n")
        self.assertIn("alias must equal", module.validate(root)[0].reason)

    def test_missing_target_is_rejected(self) -> None:
        root = self.make_vault("---\ntitle: Example Note\n---\n", "[[wiki/missing/note|Missing]]\n")
        self.assertIn("existing full vault-relative", module.validate(root)[0].reason)

    def test_fenced_code_is_ignored(self) -> None:
        root = self.make_vault("---\ntitle: Example Note\n---\n", "```md\n[[not/a/real/link|Example Note]]\n```\n")
        self.assertEqual(module.validate(root), [])


if __name__ == "__main__":
    unittest.main()
