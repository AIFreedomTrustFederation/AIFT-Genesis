import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "tree"))

from validate_tree import validate_manifest  # noqa: E402
from render_tree import load_manifest, render_html, render_svg  # noqa: E402


class TreeManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest_path = REPO_ROOT / "manifests" / "tree.manifest.json"
        self.manifest = load_manifest(self.manifest_path)

    def test_manifest_validates(self):
        self.assertEqual(validate_manifest(self.manifest_path), [])

    def test_legacy_parts_are_preserved(self):
        self.assertEqual(
            self.manifest["parts"],
            ["seed", "roots", "trunk", "branches", "leaves", "fruit", "newSeeds"],
        )

    def test_biological_branching_is_present(self):
        node_ids = {node["id"] for node in self.manifest["nodes"]}
        expected = {
            "biological-life",
            "microbial-lineages",
            "plant-life",
            "fungal-life",
            "animal-life",
            "ecosystems",
            "human-lineage",
        }
        self.assertTrue(expected.issubset(node_ids))

    def test_aetherion_remains_aspirational(self):
        aetherion = next(node for node in self.manifest["nodes"] if node["id"] == "aetherion")
        self.assertEqual(aetherion["epistemicClass"], "aspirational")
        self.assertIn("aspiration", aetherion["tags"])

    def test_renderer_is_deterministic(self):
        self.assertEqual(render_svg(self.manifest), render_svg(self.manifest))
        self.assertEqual(render_html(self.manifest), render_html(self.manifest))


if __name__ == "__main__":
    unittest.main()
