from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_validator", ROOT / "scripts" / "validate_repository.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidatorTests(unittest.TestCase):
    def test_repository_passes(self) -> None:
        self.assertEqual([], VALIDATOR.validate())

    def test_frontmatter_parser(self) -> None:
        path = ROOT / "skills" / "platform-writing-orchestrator" / "SKILL.md"
        data, body = VALIDATOR.parse_frontmatter(path)
        self.assertEqual("platform-writing-orchestrator", data["name"])
        self.assertIn("中文多平台写作总编", body)

    def test_local_path_detection(self) -> None:
        sample = "D:" + "\\private\\file.txt"
        self.assertIn("machine-local Windows/UNC path", VALIDATOR.scan_text(sample))

    def test_token_detection(self) -> None:
        sample = "github_" + "pat_" + ("A" * 32)
        self.assertIn("possible github-token", VALIDATOR.scan_text(sample))


if __name__ == "__main__":
    unittest.main()
