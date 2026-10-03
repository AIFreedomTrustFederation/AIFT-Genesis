from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


class ShellIntegrityTests(unittest.TestCase):
    def test_all_tracked_shell_sources_parse_with_declared_shell(self) -> None:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        tracked_paths = [
            Path(raw_path.decode("utf-8"))
            for raw_path in completed.stdout.split(b"\\0")
            if raw_path
        ]
        relative_paths = []
        for relative_path in tracked_paths:
            source_path = REPO_ROOT / relative_path
            if not source_path.is_file():
                continue
            first_line = source_path.read_bytes().splitlines()[:1]
            if relative_path.suffix == ".sh" or (
                first_line
                and (
                    first_line[0] in (b"#!/usr/bin/env bash", b"#!/usr/bin/env sh")
                    or first_line[0].endswith((b"/bash", b"/sh"))
                )
            ):
                relative_paths.append(relative_path)
        self.assertGreater(len(relative_paths), 0, "no tracked shell sources found")

        for relative_path in relative_paths:
            with self.subTest(path=relative_path.as_posix()):
                first_line = (REPO_ROOT / relative_path).read_text(
                    encoding="utf-8"
                ).splitlines()[0]
                if first_line == "#!/usr/bin/env sh":
                    shell = "sh"
                elif first_line == "#!/usr/bin/env bash" or first_line.endswith("/bash"):
                    shell = "bash"
                else:
                    self.fail(
                        f"{relative_path.as_posix()}: unsupported shell shebang: "
                        f"{first_line!r}"
                    )

                result = subprocess.run(
                    [shell, "-n", relative_path.as_posix()],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{relative_path.as_posix()}: {result.stderr.strip()}",
                )


if __name__ == "__main__":
    unittest.main()
