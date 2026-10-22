"""Ensure Genesis trust initialization never reports success without a Git commit."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TrustInitCommitTests(unittest.TestCase):
    def run_init(self, home: Path, *, hook_failure: bool) -> tuple[subprocess.CompletedProcess[str], Path]:
        trusts = home / "trusts"
        env = os.environ.copy()
        env.update({
            "AIFT_HOME": str(REPO_ROOT),
            "AIFT_TRUSTS": str(trusts),
            "GIT_AUTHOR_NAME": "Genesis Test",
            "GIT_AUTHOR_EMAIL": "genesis-test@example.invalid",
            "GIT_COMMITTER_NAME": "Genesis Test",
            "GIT_COMMITTER_EMAIL": "genesis-test@example.invalid",
        })
        if hook_failure:
            hooks = home / "hooks"
            hooks.mkdir()
            hook = hooks / "pre-commit"
            hook.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
            hook.chmod(0o755)
            env.update({
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": str(hooks),
            })
        result = subprocess.run(
            ["bash", str(REPO_ROOT / "bin" / "aift"), "trust", "init", "Integrity Test"],
            input="Verify provenance\n",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        return result, trusts / "integrity-test"

    def test_successful_init_creates_initial_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result, trust = self.run_init(Path(temp), hook_failure=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Trust created:", result.stdout)
            self.assertTrue((trust / "LOCAL_MANIFEST.json").is_file())
            commit = subprocess.run(["git", "-C", str(trust), "rev-parse", "HEAD"], capture_output=True)
            self.assertEqual(commit.returncode, 0, commit.stderr)

    def test_failed_commit_is_reported_without_deleting_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result, trust = self.run_init(Path(temp), hook_failure=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("initial Git commit failed", result.stderr)
            self.assertNotIn("Trust created:", result.stdout)
            self.assertTrue((trust / "LOCAL_MANIFEST.json").is_file())
            commit = subprocess.run(["git", "-C", str(trust), "rev-parse", "HEAD"], capture_output=True)
            self.assertNotEqual(commit.returncode, 0)


if __name__ == "__main__":
    unittest.main()
