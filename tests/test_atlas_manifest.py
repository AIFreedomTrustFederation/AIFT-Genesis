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
    validate_source_refs,
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

    def test_invalid_provenance_repository_reports_validation_error(self):
        for value in ("", {}, None):
            with self.subTest(value=value):
                atlas = copy.deepcopy(self.atlas)
                atlas["provenance"]["repository"] = value
                errors = []

                validate_provenance(atlas, self.atlas_path, errors)

                self.assertIn(
                    "provenance repository must be a non-empty string",
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

    def test_remote_provenance_source_documents_must_use_https(self):
        atlas = copy.deepcopy(self.atlas)
        atlas["provenance"]["sourceDocuments"] = [
            "http://example.com/source.md",
        ]
        errors = []

        validate_provenance(atlas, self.atlas_path, errors)

        self.assertIn(
            "provenance sourceDocument must use HTTPS: "
            "http://example.com/source.md",
            errors,
        )

    def test_non_array_provenance_source_documents_report_validation_error(self):
        atlas = copy.deepcopy(self.atlas)
        atlas["provenance"]["sourceDocuments"] = None
        errors = []

        validate_provenance(atlas, self.atlas_path, errors)

        self.assertIn("provenance sourceDocuments must be an array", errors)

    def test_local_source_ref_uris_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "repo"
            atlas_path = repo_root / "manifests" / "living-atlas.manifest.json"
            atlas_path.parent.mkdir(parents=True)
            outside = root / "outside.md"
            outside.write_text("outside repository\n", encoding="utf-8")

            atlas = copy.deepcopy(self.atlas)
            atlas["sourceRefs"][0]["uri"] = "../outside.md"
            errors = []

            validate_source_refs(atlas, atlas_path, errors)

            self.assertIn(
                "sourceRef genesis.readme uri escapes repository: ../outside.md",
                errors,
            )

    def test_remote_source_ref_uris_must_use_https(self):
        atlas = copy.deepcopy(self.atlas)
        atlas["sourceRefs"][0]["uri"] = "http://example.com/source.md"
        errors = []

        validate_source_refs(atlas, self.atlas_path, errors)

        self.assertIn(
            "sourceRef genesis.readme uri must use HTTPS: "
            "http://example.com/source.md",
            errors,
        )

    def test_unknown_source_ref_type_reports_validation_error(self):
        atlas = copy.deepcopy(self.atlas)
        source_ref = atlas["sourceRefs"][0]
        source_ref["type"] = "verified-audit"
        errors = []

        validate_source_refs(atlas, self.atlas_path, errors)

        self.assertIn(
            f"sourceRef {source_ref['id']} has unknown type: verified-audit",
            errors,
        )

    def test_non_string_entity_id_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            atlas["entities"][0]["id"] = {}
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn("entity id must be a string", errors)

    def test_non_string_entity_type_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            entity = atlas["entities"][0]
            entity["type"] = {}
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(f"entity {entity['id']} type must be a string", errors)

    def test_non_string_tree_mapping_node_id_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            mapping = atlas["treeMappings"][0]
            mapping["treeNodeId"] = {}
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(f"treeMapping {mapping['id']} treeNodeId must be a string", errors)

    def test_non_string_tree_mapping_entity_id_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            mapping = atlas["treeMappings"][0]
            mapping["atlasEntityId"] = {}
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(f"treeMapping {mapping['id']} atlasEntityId must be a string", errors)

    def test_non_string_tree_mapping_relation_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            mapping = atlas["treeMappings"][0]
            mapping["relation"] = {}
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(f"treeMapping {mapping['id']} relation must be a string", errors)


    def test_invalid_tree_mapping_status_reports_validation_error(self):
        for status in ("production-ready", {}, None):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp_dir:
                atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                atlas = copy.deepcopy(self.atlas)
                mapping = atlas["treeMappings"][0]
                mapping["status"] = status
                atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                errors = validate_manifest(atlas_path, self.tree_path)

                self.assertIn(
                    f"treeMapping {mapping['id']} status must be active, candidate, or deprecated",
                    errors,
                )


    def test_unknown_entity_evidence_status_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            entity = atlas["entities"][0]
            entity["evidenceStatus"] = "externally-audited"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(
                f"entity {entity['id']} has unknown evidenceStatus: externally-audited",
                errors,
            )

    def test_unknown_entity_status_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            entity = atlas["entities"][0]
            entity["status"] = "production-ready"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(
                f"entity {entity['id']} has unknown status: production-ready",
                errors,
            )

    def test_invalid_entity_short_label_reports_validation_error(self):
        for value in ("", {}, None):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp_dir:
                atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                atlas = copy.deepcopy(self.atlas)
                entity = atlas["entities"][0]
                entity["shortLabel"] = value
                atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                errors = validate_manifest(atlas_path, self.tree_path)

                self.assertIn(
                    f"entity {entity['id']} shortLabel must be a non-empty string",
                    errors,
                )

    def test_unknown_entity_link_type_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            entity = atlas["entities"][0]
            entity["links"][0]["type"] = "verified-audit"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(
                f"entity {entity['id']} link 0 has unknown type: verified-audit",
                errors,
            )

    def test_entity_link_uris_must_use_https(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
            atlas = copy.deepcopy(self.atlas)
            entity = atlas["entities"][0]
            entity["links"][0]["uri"] = "http://example.com/evidence"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            errors = validate_manifest(atlas_path, self.tree_path)

            self.assertIn(
                f"entity {entity['id']} link 0 uri must use HTTPS: "
                "http://example.com/evidence",
                errors,
            )

    def test_invalid_entity_tags_report_validation_error(self):
        for tag in ("Needs Review", {}, None):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory() as temp_dir:
                atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                atlas = copy.deepcopy(self.atlas)
                entity = atlas["entities"][0]
                entity["tags"] = [tag]
                atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                errors = validate_manifest(atlas_path, self.tree_path)

                self.assertIn(
                    f"entity {entity['id']} tags must contain lowercase tokens",
                    errors,
                )

    def test_invalid_manifest_status_reports_validation_error(self):
        for status in ("production-ready", {}, None):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp_dir:
                atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                atlas = copy.deepcopy(self.atlas)
                atlas["status"] = status
                atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                errors = validate_manifest(atlas_path, self.tree_path)

                self.assertIn(
                    "status must be draft, canonical-draft, active, or deprecated",
                    errors,
                )

    def test_invalid_manifest_descriptions_report_validation_error(self):
        for field in ("title", "description"):
            for value in ("", {}, None):
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp_dir:
                    atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                    atlas = copy.deepcopy(self.atlas)
                    atlas[field] = value
                    atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                    errors = validate_manifest(atlas_path, self.tree_path)

                    self.assertIn(
                        f"{field} must be a non-empty string",
                        errors,
                    )

    def test_invalid_manifest_boundaries_report_validation_error(self):
        for value in ("", {}, None):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp_dir:
                atlas_path = Path(temp_dir) / "living-atlas.manifest.json"
                atlas = copy.deepcopy(self.atlas)
                atlas["boundaries"]["observedRuntime"] = value
                atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

                errors = validate_manifest(atlas_path, self.tree_path)

                self.assertIn(
                    "boundaries observedRuntime must be a non-empty string",
                    errors,
                )


if __name__ == "__main__":
    unittest.main()
