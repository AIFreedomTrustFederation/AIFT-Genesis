"""The Genesis CLI must not claim trust creation when its initial Git commit fails."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class TrustInitCommitTests(unittest.TestCase):
    def test_missing_git_identity_fails_without_success_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env.update(
                AIFT_HOME=str(REPO_ROOT),
                AIFT_TRUSTS=temp_dir,
                GIT_CONFIG_GLOBAL=os.devnull,
                GIT_CONFIG_NOSYSTEM="1",
                GIT_AUTHOR_NAME="",
                GIT_AUTHOR_EMAIL="",
                GIT_COMMITTER_NAME="",
                GIT_COMMITTER_EMAIL="",
            )

            completed = subprocess.run(
                ["bash", str(REPO_ROOT / "bin" / "aift"), "trust", "init", "Missing Identity"],
                input="A private trust\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            output = completed.stdout + completed.stderr
            self.assertNotEqual(completed.returncode, 0, output)
            self.assertNotIn("Trust created:", output)
            self.assertIn("ident", output.lower())

            target = Path(temp_dir) / "missing-identity"
            self.assertTrue(target.is_dir(), "generated files should remain for recovery")
            history = subprocess.run(
                ["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(history.returncode, 0, "no initial commit should exist")


if __name__ == "__main__":
    unittest.main()
