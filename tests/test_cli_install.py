"""Regression tests: Genesis CLI install must not hide a failed Git pull.

Uses a disposable checkout and a Git wrapper; no network or user files are touched.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git")


@unittest.skipUnless(GIT, "git is required")
class InstallPullTests(unittest.TestCase):
    def run_install(self, pull_exit: int) -> tuple[subprocess.CompletedProcess[str], str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            checkout = root / "genesis"
            prefix = root / "prefix"
            wrapper = root / "wrappers"
            (checkout / "bin").mkdir(parents=True)
            (prefix / "bin").mkdir(parents=True)
            wrapper.mkdir()
            home.mkdir()

            source = "#!/bin/sh\necho new-version\n"
            (checkout / "bin" / "aift").write_text(source, encoding="utf-8")
            installed = prefix / "bin" / "aift"
            old = "#!/bin/sh\necho existing-version\n"
            installed.write_text(old, encoding="utf-8")

            subprocess.run([GIT, "init", "-q", "-b", "main", str(checkout)], check=True)
            subprocess.run([GIT, "-C", str(checkout), "add", "."], check=True)
            subprocess.run([
                GIT, "-C", str(checkout), "-c", "user.name=Genesis Test",
                "-c", "user.email=genesis-test@example.invalid",
                "commit", "-q", "-m", "fixture",
            ], check=True)

            # Intercept only the pull, leaving checkout and all other Git operations real.
            fake_git = wrapper / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "pull" ]; then\n'
                '  echo "simulated pull failure" >&2\n'
                '  exit "$AIFT_TEST_PULL_EXIT"\n'
                "fi\n"
                f'exec "{GIT}" "$@"\n',
                encoding="utf-8",
            )
            fake_git.chmod(0o755)

            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "AIFT_HOME": str(checkout),
                "PREFIX": str(prefix),
                "AIFT_TEST_PULL_EXIT": str(pull_exit),
                "PATH": str(wrapper) + os.pathsep + env.get("PATH", ""),
            })
            result = subprocess.run(
                ["bash", str(ROOT / "bin" / "aift"), "install"],
                capture_output=True, text=True, env=env, check=False,
            )
            return result, installed.read_text(encoding="utf-8"), source if pull_exit == 0 else old

    def test_failed_pull_does_not_replace_installed_cli_or_report_success(self) -> None:
        result, installed, expected = self.run_install(pull_exit=42)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("simulated pull failure", result.stderr)
        self.assertNotIn("Installed:", result.stdout)
        self.assertEqual(installed, expected)

    def test_successful_pull_still_installs_cli(self) -> None:
        result, installed, expected = self.run_install(pull_exit=0)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Installed:", result.stdout)
        self.assertEqual(installed, expected)


if __name__ == "__main__":
    unittest.main()
