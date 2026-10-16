"""Guard the federation verification command against status-only regressions."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FederationVerifyContractTests(unittest.TestCase):
    def test_verify_matches_ci_integrity_stages(self):
        manifest = json.loads((ROOT / "aift.repo.json").read_text(encoding="utf-8"))
        command = manifest["commands"]["verify"]
        stages = (
            "python3 -B -m unittest discover -s tests -v",
            "python3 -B tools/validation/validate_tree.py",
            "python3 -B tools/validation/validate_atlas.py",
            "python3 -B tools/tree/render_tree.py --check",
        )
        self.assertEqual(command.split(" && "), list(stages))

    def test_verify_is_valid_shell_syntax(self):
        manifest = json.loads((ROOT / "aift.repo.json").read_text(encoding="utf-8"))
        command = manifest["commands"]["verify"]
        subprocess.run(["sh", "-n", "-c", command], check=True)


if __name__ == "__main__":
    unittest.main()
