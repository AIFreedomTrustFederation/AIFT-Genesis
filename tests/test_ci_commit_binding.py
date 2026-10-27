"""Verify that Genesis CI cannot attest a different clean Git revision."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "genesis-integrity.yml"


def checkout_guard() -> str:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    matches = [step["run"] for step in steps if step.get("name") == "Verify clean checkout"]
    if len(matches) != 1:
        raise AssertionError("expected exactly one final checkout guard")
    return matches[0]


class GenesisCICommitBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "CI Test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "ci-test@example.invalid"], cwd=self.repo, check=True)
        (self.repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.repo, check=True)
        self.expected_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True
        ).strip()

    def run_guard(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-e", "-c", checkout_guard()],
            cwd=self.repo,
            env={**os.environ, "GITHUB_SHA": self.expected_sha},
            capture_output=True,
            text=True,
        )

    def test_original_clean_revision_passes(self) -> None:
        self.assertEqual(self.run_guard().returncode, 0)

    def test_clean_worktree_with_changed_head_fails(self) -> None:
        subprocess.run(
            ["git", "commit", "--allow-empty", "-qm", "QA moved HEAD"],
            cwd=self.repo,
            check=True,
        )
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=self.repo, text=True
        )
        self.assertEqual(status, "")
        self.assertNotEqual(self.run_guard().returncode, 0)

    def test_dirty_worktree_fails(self) -> None:
        (self.repo / "tracked.txt").write_text("modified\n", encoding="utf-8")
        self.assertNotEqual(self.run_guard().returncode, 0)


if __name__ == "__main__":
    unittest.main()
