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

    def test_manifest_rejects_unexpected_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["trustLevel"] = "unverified"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("manifest has unexpected field: trustLevel", errors)

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

    def test_nodes_reject_unexpected_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = manifest["nodes"][0]
            node["trustLevel"] = "unverified"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"node {node['id']} has unexpected field: trustLevel",
                errors,
            )

    def test_edges_reject_unexpected_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            edge = manifest["edges"][0]
            edge["trustLevel"] = "unverified"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"edge {edge['id']} has unexpected field: trustLevel",
                errors,
            )

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

    def test_provenance_rejects_unexpected_fields(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["provenance"]["trustLevel"] = "unverified"
        errors = []

        validate_provenance(manifest, self.manifest_path, errors)

        self.assertIn("provenance has unexpected field: trustLevel", errors)

    def test_invalid_provenance_repository_reports_validation_error(self):
        for value in ("", {}, None):
            with self.subTest(value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest["provenance"]["repository"] = value
                errors = []

                validate_provenance(manifest, self.manifest_path, errors)

                self.assertIn(
                    "provenance repository must be a non-empty string",
                    errors,
                )

    def test_invalid_nullable_provenance_fields_report_validation_error(self):
        for field in ("lastGenerated", "sourceCommit"):
            for value in ({}, [], False, 1):
                with self.subTest(field=field, value=value):
                    manifest = copy.deepcopy(self.manifest)
                    manifest["provenance"][field] = value
                    errors = []

                    validate_provenance(manifest, self.manifest_path, errors)

                    self.assertIn(
                        f"provenance {field} must be a string or null",
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

    def test_provenance_source_documents_must_be_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            manifest_path = repo_root / "manifests" / "tree.manifest.json"
            manifest_path.parent.mkdir(parents=True)
            (repo_root / "docs").mkdir()

            manifest = copy.deepcopy(self.manifest)
            manifest["provenance"]["sourceDocuments"] = ["docs"]
            errors = []

            validate_provenance(manifest, manifest_path, errors)

            self.assertIn(
                "provenance sourceDocument must be a file: docs",
                errors,
            )

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

    def test_source_refs_must_contain_objects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["sourceRefs"][0] = "genesis.readme"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("sourceRefs must contain objects", errors)

    def test_source_refs_reject_unexpected_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            source_ref = manifest["sourceRefs"][0]
            source_ref["trustLevel"] = "unverified"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"sourceRef {source_ref['id']} has unexpected field: trustLevel",
                errors,
            )

    def test_source_refs_require_schema_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            source_ref = manifest["sourceRefs"][0]
            del source_ref["label"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"sourceRef {source_ref['id']} missing required field: label",
                errors,
            )

    def test_source_refs_reject_unknown_types(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            source_ref = manifest["sourceRefs"][0]
            source_ref["type"] = "unverified"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"sourceRef {source_ref['id']} has unknown type: unverified",
                errors,
            )

    def test_source_ref_fields_require_non_empty_strings(self):
        for field in ("label", "uri", "type"):
            for value in ("", {}):
                with self.subTest(field=field, value=value):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        manifest_path = Path(temp_dir) / "tree.manifest.json"
                        manifest = copy.deepcopy(self.manifest)
                        source_ref = manifest["sourceRefs"][0]
                        source_ref[field] = value
                        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                        errors = validate_manifest(manifest_path)

                        self.assertIn(
                            f"sourceRef {source_ref['id']} {field} must be a non-empty string",
                            errors,
                        )

    def test_local_source_ref_uris_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            source_ref = manifest["sourceRefs"][0]
            source_ref["uri"] = "../outside.md"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(
                f"sourceRef {source_ref['id']} uri escapes repository: ../outside.md",
                errors,
            )

    def test_local_source_ref_uris_must_be_files(self):
        for uri in ("missing-tree-source.md", "."):
            with self.subTest(uri=uri):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manifest_path = Path(temp_dir) / "tree.manifest.json"
                    manifest = copy.deepcopy(self.manifest)
                    source_ref = manifest["sourceRefs"][0]
                    source_ref["uri"] = uri
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_manifest(manifest_path)

                    self.assertIn(
                        f"sourceRef {source_ref['id']} uri does not exist: {uri}",
                        errors,
                    )

    def test_remote_source_ref_uris_must_use_https(self):
        for uri in (
            "http://example.com/source.md",
            "javascript:alert(1)",
            "data:text/html,unsafe",
        ):
            with self.subTest(uri=uri):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manifest_path = Path(temp_dir) / "tree.manifest.json"
                    manifest = copy.deepcopy(self.manifest)
                    source_ref = manifest["sourceRefs"][0]
                    source_ref["uri"] = uri
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_manifest(manifest_path)

                    self.assertIn(
                        f"sourceRef {source_ref['id']} uri must use HTTPS: {uri}",
                        errors,
                    )

    def test_source_ref_ids_use_canonical_pattern(self):
        for ref_id in ("Genesis.Readme", "genesis/readme", ".genesis"):
            with self.subTest(ref_id=ref_id):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manifest_path = Path(temp_dir) / "tree.manifest.json"
                    manifest = copy.deepcopy(self.manifest)
                    manifest["sourceRefs"][0]["id"] = ref_id
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_manifest(manifest_path)

                    self.assertIn(
                        f"sourceRef {ref_id} id must be a lowercase source id",
                        errors,
                    )

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

    def test_non_string_domain_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["domains"][0] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("domains must contain strings", errors)

    def test_domains_must_contain_unique_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["domains"].append(manifest["domains"][0])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("domains must contain unique values", errors)

    def test_domains_must_use_canonical_tokens(self):
        for domain in ("ArtificialIntelligence", "artificial intelligence", "-ai"):
            with self.subTest(domain=domain):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manifest_path = Path(temp_dir) / "tree.manifest.json"
                    manifest = copy.deepcopy(self.manifest)
                    manifest["domains"][0] = domain
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                    errors = validate_manifest(manifest_path)

                    self.assertIn("domains must contain lowercase tokens", errors)

    def test_non_array_edge_relations_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["edgeRelations"] = None
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("edgeRelations must be a non-empty array", errors)

    def test_non_string_edge_relation_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["edgeRelations"][0] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("edgeRelations must contain strings", errors)

    def test_edge_relations_must_contain_unique_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["edgeRelations"].append(manifest["edgeRelations"][0])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("edgeRelations must contain unique values", errors)

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

    def test_non_string_node_tags_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = next(
                item for item in manifest["nodes"] if item["epistemicClass"] == "aspirational"
            )
            node["tags"].append({})
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"node {node['id']} tags must contain strings", errors)

    def test_non_string_node_status_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = next(
                item for item in manifest["nodes"] if item["epistemicClass"] == "aspirational"
            )
            node["status"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"node {node['id']} status must be a string", errors)

    def test_non_string_root_node_ids_report_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["rootNodeIds"] = [{}]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("rootNodeIds must contain strings", errors)

    def test_root_node_ids_must_contain_unique_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["rootNodeIds"].append(manifest["rootNodeIds"][0])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("rootNodeIds must contain unique values", errors)

    def test_non_string_edge_endpoint_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            edge = manifest["edges"][0]
            edge["from"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"edge {edge['id']} from must be a string", errors)

    def test_non_string_node_id_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["nodes"][0]["id"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("node id must be a string", errors)

    def test_non_string_source_ref_id_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            manifest["sourceRefs"][0]["id"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn("sourceRef id must be a string", errors)

    def test_non_string_node_epistemic_class_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = manifest["nodes"][0]
            node["epistemicClass"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"node {node['id']} epistemicClass must be a string", errors)

    def test_non_string_node_domain_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            node = manifest["nodes"][0]
            node["domain"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"node {node['id']} domain must be a string", errors)

    def test_non_string_edge_relation_value_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            edge = manifest["edges"][0]
            edge["relation"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"edge {edge['id']} relation must be a string", errors)

    def test_non_string_edge_epistemic_class_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            edge = manifest["edges"][0]
            edge["epistemicClass"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"edge {edge['id']} epistemicClass must be a string", errors)

    def test_non_string_edge_role_reports_validation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "tree.manifest.json"
            manifest = copy.deepcopy(self.manifest)
            edge = manifest["edges"][0]
            edge["role"] = {}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate_manifest(manifest_path)

            self.assertIn(f"edge {edge['id']} role must be a string", errors)

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
