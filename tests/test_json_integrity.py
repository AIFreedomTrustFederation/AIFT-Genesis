from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


class JsonIntegrityTests(unittest.TestCase):
    def test_duplicate_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate key: localFirst"):
            json.loads(
                '{"localFirst": true, "localFirst": false}',
                object_pairs_hook=reject_duplicate_keys,
            )

    def test_all_tracked_json_is_unambiguous(self) -> None:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "*.json"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        relative_paths = [
            Path(raw_path.decode("utf-8"))
            for raw_path in completed.stdout.split(b"\0")
            if raw_path
        ]
        self.assertGreater(len(relative_paths), 0, "no tracked JSON files found")

        for relative_path in relative_paths:
            with self.subTest(path=relative_path.as_posix()):
                source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
                try:
                    json.loads(source, object_pairs_hook=reject_duplicate_keys)
                except (json.JSONDecodeError, ValueError) as exc:
                    self.fail(f"{relative_path.as_posix()}: {exc}")


if __name__ == "__main__":
    unittest.main()
