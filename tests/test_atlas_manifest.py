import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))

from validate_atlas import (  # noqa: E402
    PROHIBITED_TREE_KEYS,
    validate_manifest,
    validate_provenance,
)


class LivingAtlasManifestTests(unittest.TestCase):
    def setUp(self):
        self.atlas_path = REPO_ROOT / "manifests" / "living-atlas.manifest.json"
        self.tree_path = REPO_ROOT / "manifests" / "tree.manifest.json"
        self.atlas = json.loads(self.atlas_path.read_text(encoding="utf-8"))
        self.tree = json.loads(self.tree_path.read_text(encoding="utf-8"))

    def test_manifest_validates_against_tree_ids(self):
        self.assertEqual(validate_manifest(self.atlas_path, self.tree_path), [])

    def test_tree_manifest_does_not_embed_atlas_records(self):
        self.assertFalse(PROHIBITED_TREE_KEYS & set(self.tree.keys()))
        for node in self.tree["nodes"]:
            self.assertFalse(PROHIBITED_TREE_KEYS & set(node.keys()))

    def test_artificial_intelligence_has_explicit_atlas_mappings(self):
        related = [
            mapping
            for mapping in self.atlas["treeMappings"]
            if mapping["treeNodeId"] == "artificial-intelligence"
        ]
        self.assertGreaterEqual(len(related), 4)
        self.assertEqual(
            {mapping["atlasEntityId"] for mapping in related},
            {
                "repo-aift-genesis",
                "repo-aift-forge",
                "repo-ai-freedom-trust",
                "repo-aether-coin-biozonecurrency",
                "publication-aetherion-flight-paper",
            },
        )

    def test_all_mapping_targets_are_entity_ids_not_display_names(self):
        entity_ids = {entity["id"] for entity in self.atlas["entities"]}
        for mapping in self.atlas["treeMappings"]:
            self.assertIn(mapping["atlasEntityId"], entity_ids)
            self.assertEqual(mapping["atlasEntityId"], mapping["atlasEntityId"].lower())
            self.assertNotIn(" ", mapping["atlasEntityId"])

    def test_provenance_paths_must_exist(self):
        atlas = copy.deepcopy(self.atlas)
        atlas["provenance"]["schema"] = "schemas/MissingAtlas.schema.json"
        errors = []

        validate_provenance(atlas, self.atlas_path, errors)

        self.assertIn(
            "provenance schema does not exist: schemas/MissingAtlas.schema.json",
            errors,
        )

    def test_provenance_paths_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "repo"
            atlas_path = repo_root / "manifests" / "living-atlas.manifest.json"
            atlas_path.parent.mkdir(parents=True)
            outside = root / "outside.schema.json"
            outside.write_text("{}\n", encoding="utf-8")

            atlas = copy.deepcopy(self.atlas)
            atlas["provenance"]["schema"] = "../outside.schema.json"
            errors = []

            validate_provenance(atlas, atlas_path, errors)

            self.assertIn(
                "provenance schema escapes repository: ../outside.schema.json",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
