from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_spec.py"


class ValidateSpecTests(unittest.TestCase):
    def test_repository_specification_is_structurally_valid(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: specification structure valid", result.stdout)

    def test_requirement_and_acceptance_ids_are_one_to_one(self) -> None:
        module_spec = importlib.util.spec_from_file_location("validate_spec", VALIDATOR)
        if module_spec is None or module_spec.loader is None:
            self.fail("could not load specification validator module")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        text = (ROOT / "docs" / "SPECIFICATION.md").read_text(encoding="utf-8")
        requirements = module.REQ_RE.findall(text)
        acceptance = [item.removeprefix("AT-") for item in module.AT_RE.findall(text)]
        self.assertEqual(len(requirements), len(set(requirements)))
        self.assertEqual(len(acceptance), len(set(acceptance)))
        self.assertSetEqual(set(requirements), set(acceptance))


if __name__ == "__main__":
    unittest.main()
