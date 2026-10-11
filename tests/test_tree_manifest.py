import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "tree"))

from validate_tree import validate_manifest, validate_provenance  # noqa: E402
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

    def test_provenance_paths_must_exist(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["provenance"]["generator"] = "tools/tree/missing-renderer.py"
        errors = []

        validate_provenance(manifest, self.manifest_path, errors)

        self.assertIn(
            "provenance generator does not exist: tools/tree/missing-renderer.py",
            errors,
        )

    def test_provenance_paths_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "repo"
            manifest_path = repo_root / "manifests" / "tree.manifest.json"
            manifest_path.parent.mkdir(parents=True)
            outside = root / "outside.py"
            outside.write_text("# outside repository\n", encoding="utf-8")

            manifest = copy.deepcopy(self.manifest)
            manifest["provenance"]["generator"] = "../outside.py"
            errors = []

            validate_provenance(manifest, manifest_path, errors)

            self.assertIn(
                "provenance generator escapes repository: ../outside.py",
                errors,
            )

    def test_non_array_provenance_source_documents_report_validation_error(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["provenance"]["sourceDocuments"] = None
        errors = []

        validate_provenance(manifest, self.manifest_path, errors)

        self.assertIn("provenance sourceDocuments must be an array", errors)

    def test_non_array_generated_artifacts_report_validation_error(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["provenance"]["generatedArtifacts"] = None
        errors = []

        validate_provenance(manifest, self.manifest_path, errors)

        self.assertIn("provenance generatedArtifacts must be an array", errors)

    def test_non_array_source_refs_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["sourceRefs"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("sourceRefs must be an array", errors)

    def test_non_object_epistemic_classes_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["epistemicClasses"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("epistemicClasses must be a non-empty object", errors)

    def test_non_array_domains_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["domains"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("domains must be a non-empty array", errors)

    def test_non_array_edge_relations_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["edgeRelations"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("edgeRelations must be a non-empty array", errors)

    def test_non_array_node_tags_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = next(
                item for item in manifest["nodes"] if item["epistemicClass"] == "aspirational"
            )
            node["tags"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"node {node['id']} tags must be an array", errors)

    def test_non_string_root_node_ids_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["rootNodeIds"] = [{}]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("rootNodeIds must contain strings", errors)

    def test_non_object_graph_items_report_validation_errors(self):
        for collection, invalid_value, expected_error in (
            ("nodes", "not-a-node", "each node must be an object"),
            ("edges", "not-an-edge", "each edge must be an object"),
        ):
            with self.subTest(collection=collection), tempfile.TemporaryDirectory() as temp_dir:
                manifest_path = Path(temp_dir) / "tree.manifest.json"
                manifest = copy.deepcopy(self.manifest)
                manifest[collection].append(invalid_value)
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                errors = validate_manifest(manifest_path)

                self.assertIn(expected_error, errors)


if __name__ == "__main__":
    unittest.main()
