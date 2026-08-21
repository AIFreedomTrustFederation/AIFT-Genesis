#!/usr/bin/env python3
"""Validate the AIFT Living Atlas manifest and Tree mapping boundary."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATLAS = REPO_ROOT / "manifests" / "living-atlas.manifest.json"
DEFAULT_TREE = REPO_ROOT / "manifests" / "tree.manifest.json"

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PROHIBITED_TREE_KEYS = {
    "atlas",
    "atlasEntities",
    "atlasMappings",
    "atlasRecords",
    "livingAtlas",
    "livingAtlasEntities",
    "livingAtlasMappings",
}


class ValidationError(Exception):
    """Raised when a JSON file cannot be loaded."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: root must be an object")
    return data


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_fields(item: dict[str, Any], required: set[str], context: str, errors: list[str]) -> None:
    for key in sorted(required - set(item.keys())):
        fail(errors, f"{context} missing required field: {key}")


def duplicate_ids(items: list[Any], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            fail(errors, f"each {label} must be an object")
            continue
        item_id = item.get("id")
        if item_id in seen:
            fail(errors, f"duplicate {label} id: {item_id}")
        seen.add(str(item_id))


def validate_id(value: Any, context: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not ID_RE.match(value):
        fail(errors, f"{context} must be a lowercase hyphenated id")


def validate_source_id(value: Any, context: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SOURCE_ID_RE.match(value):
        fail(errors, f"{context} must be a lowercase source id")


def validate_type_definitions(
    definitions: Any,
    label: str,
    errors: list[str],
) -> set[str]:
    if not isinstance(definitions, dict) or not definitions:
        fail(errors, f"{label} must be a non-empty object")
        return set()
    ids: set[str] = set()
    for item_id, item in definitions.items():
        validate_id(item_id, f"{label} id {item_id}", errors)
        ids.add(item_id)
        if not isinstance(item, dict):
            fail(errors, f"{label} {item_id} must be an object")
            continue
        require_fields(item, {"label", "definition"}, f"{label} {item_id}", errors)
        for field in ("label", "definition"):
            if not isinstance(item.get(field), str) or not item.get(field):
                fail(errors, f"{label} {item_id} {field} must be a non-empty string")
    return ids


def validate_source_refs(data: dict[str, Any], errors: list[str]) -> set[str]:
    source_refs = data.get("sourceRefs", [])
    if not isinstance(source_refs, list):
        fail(errors, "sourceRefs must be an array")
        return set()
    duplicate_ids(source_refs, "sourceRef", errors)
    known: set[str] = set()
    for ref in source_refs:
        if not isinstance(ref, dict):
            continue
        ref_id = ref.get("id")
        validate_source_id(ref_id, f"sourceRef {ref_id} id", errors)
        known.add(str(ref_id))
        require_fields(ref, {"id", "label", "uri", "type"}, f"sourceRef {ref_id}", errors)
        for field in ("label", "uri", "type"):
            if not isinstance(ref.get(field), str) or not ref.get(field):
                fail(errors, f"sourceRef {ref_id} {field} must be a non-empty string")
    return known


def validate_ref_list(
    refs: Any,
    known_refs: set[str],
    context: str,
    errors: list[str],
) -> None:
    if not isinstance(refs, list):
        fail(errors, f"{context} sourceRefs must be an array")
        return
    for ref in refs:
        if not isinstance(ref, str):
            fail(errors, f"{context} sourceRefs must contain strings")
        elif ref not in known_refs:
            fail(errors, f"{context} references unknown sourceRef: {ref}")


def validate_entities(
    data: dict[str, Any],
    entity_types: set[str],
    known_refs: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        fail(errors, "entities must be an array")
        return {}
    duplicate_ids(entities, "entity", errors)
    by_id: dict[str, dict[str, Any]] = {}
    required = {
        "id",
        "type",
        "label",
        "description",
        "status",
        "visibility",
        "evidenceStatus",
        "sourceRefs",
        "links",
        "tags",
        "metadata",
    }
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("id", "<missing>")
        validate_id(entity_id, f"entity {entity_id} id", errors)
        by_id[str(entity_id)] = entity
        require_fields(entity, required, f"entity {entity_id}", errors)
        if entity.get("type") not in entity_types:
            fail(errors, f"entity {entity_id} has unknown type: {entity.get('type')}")
        if entity.get("visibility") != "public":
            fail(errors, f"canonical Atlas entity {entity_id} must be public or omitted from this manifest")
        for field in ("label", "description", "status", "visibility", "evidenceStatus"):
            if not isinstance(entity.get(field), str) or not entity.get(field):
                fail(errors, f"entity {entity_id} {field} must be a non-empty string")
        validate_ref_list(entity.get("sourceRefs"), known_refs, f"entity {entity_id}", errors)
        if not isinstance(entity.get("links"), list):
            fail(errors, f"entity {entity_id} links must be an array")
        if not isinstance(entity.get("tags"), list):
            fail(errors, f"entity {entity_id} tags must be an array")
        if not isinstance(entity.get("metadata"), dict):
            fail(errors, f"entity {entity_id} metadata must be an object")
    return by_id


def validate_tree_boundary(tree: dict[str, Any], errors: list[str]) -> set[str]:
    found = PROHIBITED_TREE_KEYS & set(tree.keys())
    for key in sorted(found):
        fail(errors, f"tree manifest must not contain Atlas field: {key}")
    nodes = tree.get("nodes", [])
    if not isinstance(nodes, list):
        fail(errors, "tree manifest nodes must be an array")
        return set()
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id"))
        node_ids.add(node_id)
        found_node_keys = PROHIBITED_TREE_KEYS & set(node.keys())
        for key in sorted(found_node_keys):
            fail(errors, f"tree node {node_id} must not contain Atlas field: {key}")
    return node_ids


def validate_tree_mappings(
    data: dict[str, Any],
    entity_ids: set[str],
    tree_node_ids: set[str],
    mapping_relations: set[str],
    known_refs: set[str],
    errors: list[str],
) -> None:
    mappings = data.get("treeMappings", [])
    if not isinstance(mappings, list):
        fail(errors, "treeMappings must be an array")
        return
    duplicate_ids(mappings, "treeMapping", errors)
    seen_pairs: set[tuple[str, str, str]] = set()
    required = {"id", "treeNodeId", "atlasEntityId", "relation", "status", "description", "sourceRefs"}
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        mapping_id = mapping.get("id", "<missing>")
        validate_id(mapping_id, f"treeMapping {mapping_id} id", errors)
        require_fields(mapping, required, f"treeMapping {mapping_id}", errors)
        tree_node_id = mapping.get("treeNodeId")
        atlas_entity_id = mapping.get("atlasEntityId")
        relation = mapping.get("relation")
        if tree_node_id not in tree_node_ids:
            fail(errors, f"treeMapping {mapping_id} references unknown treeNodeId: {tree_node_id}")
        if atlas_entity_id not in entity_ids:
            fail(errors, f"treeMapping {mapping_id} references unknown atlasEntityId: {atlas_entity_id}")
        if relation not in mapping_relations:
            fail(errors, f"treeMapping {mapping_id} has unknown relation: {relation}")
        pair = (str(tree_node_id), str(atlas_entity_id), str(relation))
        if pair in seen_pairs:
            fail(
                errors,
                f"duplicate tree mapping pair: {tree_node_id} / {atlas_entity_id} / {relation}",
            )
        seen_pairs.add(pair)
        if not isinstance(mapping.get("description"), str) or not mapping.get("description"):
            fail(errors, f"treeMapping {mapping_id} description must be a non-empty string")
        validate_ref_list(mapping.get("sourceRefs"), known_refs, f"treeMapping {mapping_id}", errors)


def validate_provenance(data: dict[str, Any], atlas_path: Path, errors: list[str]) -> None:
    provenance = data.get("provenance", {})
    if not isinstance(provenance, dict):
        fail(errors, "provenance must be an object")
        return
    required = {"repository", "schema", "validator", "sourceDocuments", "lastUpdated", "sourceCommit"}
    require_fields(provenance, required, "provenance", errors)
    repo_root = atlas_path.resolve().parents[1]
    for source in provenance.get("sourceDocuments", []):
        if not isinstance(source, str) or not source:
            fail(errors, "provenance sourceDocuments must contain non-empty strings")
            continue
        if source.startswith("http://") or source.startswith("https://"):
            continue
        if not (repo_root / source).exists():
            fail(errors, f"provenance sourceDocument does not exist: {source}")


def validate_manifest(atlas_path: Path = DEFAULT_ATLAS, tree_path: Path = DEFAULT_TREE) -> list[str]:
    atlas = load_json(atlas_path)
    tree = load_json(tree_path)
    errors: list[str] = []

    required = {
        "kind",
        "schemaVersion",
        "atlasVersion",
        "atlasId",
        "title",
        "status",
        "description",
        "boundaries",
        "entityTypes",
        "mappingRelations",
        "sourceRefs",
        "entities",
        "treeMappings",
        "provenance",
    }
    require_fields(atlas, required, "manifest", errors)
    if atlas.get("kind") != "living-atlas-manifest":
        fail(errors, "kind must be living-atlas-manifest")
    for field in ("schemaVersion", "atlasVersion"):
        value = atlas.get(field)
        if not isinstance(value, str) or not SEMVER_RE.match(value):
            fail(errors, f"{field} must be a semantic version string")
    validate_id(atlas.get("atlasId"), "atlasId", errors)

    entity_types = validate_type_definitions(atlas.get("entityTypes"), "entityTypes", errors)
    mapping_relations = validate_type_definitions(
        atlas.get("mappingRelations"),
        "mappingRelations",
        errors,
    )
    known_refs = validate_source_refs(atlas, errors)
    entities_by_id = validate_entities(atlas, entity_types, known_refs, errors)
    tree_node_ids = validate_tree_boundary(tree, errors)
    validate_tree_mappings(
        atlas,
        set(entities_by_id.keys()),
        tree_node_ids,
        mapping_relations,
        known_refs,
        errors,
    )
    validate_provenance(atlas, atlas_path, errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--tree-manifest", type=Path, default=DEFAULT_TREE)
    args = parser.parse_args(argv)

    try:
        errors = validate_manifest(args.manifest, args.tree_manifest)
    except ValidationError as exc:
        print(f"Atlas manifest validation failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Atlas manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Atlas manifest validation passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
