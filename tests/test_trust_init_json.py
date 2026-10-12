"""Regression coverage for JSON-safe substitution in the Genesis trust CLI."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class TrustInitJsonTests(unittest.TestCase):
    def test_quotes_backslashes_and_control_characters_survive_generation(self) -> None:
        name = 'Acme "R&D" \\ HQ'
        purpose = 'Design "private" \\ pipelines\tsecurely'

        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["AIFT_HOME"] = str(REPO_ROOT)
            env["AIFT_TRUSTS"] = temp_dir
            env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "Genesis Test"
            env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "genesis-test@example.invalid"

            completed = subprocess.run(
                ["bash", str(REPO_ROOT / "bin" / "aift"), "trust", "init", name],
                input=purpose + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            trust_dir = Path(temp_dir) / "acme-r-d-hq"
            manifest = json.loads((trust_dir / "LOCAL_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["trust"]["name"], name)
            self.assertEqual(manifest["trust"]["slug"], "acme-r-d-hq")
            self.assertEqual(manifest["trust"]["purpose"], purpose)

            trust_text = (trust_dir / "TRUST.md").read_text(encoding="utf-8")
            self.assertIn(name, trust_text)
            self.assertIn(purpose, trust_text)


if __name__ == "__main__":
    unittest.main()
