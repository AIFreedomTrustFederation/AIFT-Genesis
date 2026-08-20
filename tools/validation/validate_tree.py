#!/usr/bin/env python3
"""Validate the canonical AIFT Tree of Emergence manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "manifests" / "tree.manifest.json"

LEGACY_PARTS = ["seed", "roots", "trunk", "branches", "leaves", "fruit", "newSeeds"]
NODE_REQUIRED = {
    "id",
    "label",
    "shortLabel",
    "description",
    "domain",
    "epistemicClass",
    "status",
    "tags",
    "sourceRefs",
    "metadata",
    "presentationRole",
}
EDGE_REQUIRED = {
    "id",
    "from",
    "to",
    "relation",
    "epistemicClass",
    "role",
    "description",
    "sourceRefs",
}
PROHIBITED_VISUAL_KEYS = {
    "x",
    "y",
    "z",
    "xy",
    "xyz",
    "coord",
    "coords",
    "coordinate",
    "coordinates",
    "position",
    "screen",
    "screenx",
    "screeny",
    "layoutx",
    "layouty",
}


class ValidationError(Exception):
    """Raised when manifest validation fails."""


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: manifest root must be an object")
    return data


def require_top_level(data: dict[str, Any], errors: list[str]) -> None:
    required = {
        "kind",
        "schemaVersion",
        "modelVersion",
        "modelId",
        "title",
        "status",
        "description",
        "parts",
        "epistemicClasses",
        "domains",
        "edgeRelations",
        "rootNodeIds",
        "primaryProjection",
        "sourceRefs",
        "nodes",
        "edges",
        "views",
        "provenance",
    }
    for key in sorted(required):
        if key not in data:
            fail(errors, f"missing top-level field: {key}")
    if data.get("kind") != "tree-manifest":
        fail(errors, "kind must be tree-manifest")
    if data.get("parts") != LEGACY_PARTS:
        fail(errors, f"parts must preserve legacy order and values: {LEGACY_PARTS}")
    for key in ("schemaVersion", "modelVersion"):
        value = data.get(key)
        if not isinstance(value, str) or value.count(".") != 2:
            fail(errors, f"{key} must be a semantic version string")


def find_duplicate_ids(items: list[dict[str, Any]], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.get("id")
        if item_id in seen:
            fail(errors, f"duplicate {label} id: {item_id}")
        seen.add(item_id)


def validate_refs(
    refs: list[Any],
    known_refs: set[str],
    context: str,
    errors: list[str],
) -> None:
    for ref in refs:
        if not isinstance(ref, str):
            fail(errors, f"{context} sourceRefs must contain strings")
        elif ref not in known_refs:
            fail(errors, f"{context} references unknown sourceRef: {ref}")


def contains_visual_coordinates(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).replace("_", "").replace("-", "").lower()
            if lowered in PROHIBITED_VISUAL_KEYS:
                fail(errors, f"{path}.{key} looks like authoritative visual coordinate metadata")
            contains_visual_coordinates(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            contains_visual_coordinates(child, f"{path}[{index}]", errors)


def validate_nodes(data: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    nodes = data.get("nodes", [])
    classes = set(data.get("epistemicClasses", {}).keys())
    domains = set(data.get("domains", []))
    known_refs = {ref.get("id") for ref in data.get("sourceRefs", []) if isinstance(ref, dict)}

    if not isinstance(nodes, list) or not nodes:
        fail(errors, "nodes must be a non-empty array")
        return {}

    find_duplicate_ids(nodes, "node", errors)
    by_id: dict[str, dict[str, Any]] = {}

    for node in nodes:
        if not isinstance(node, dict):
            fail(errors, "each node must be an object")
            continue
        node_id = node.get("id", "<missing>")
        by_id[str(node_id)] = node
        missing = NODE_REQUIRED - set(node.keys())
        for key in sorted(missing):
            fail(errors, f"node {node_id} missing required field: {key}")
        if node.get("epistemicClass") not in classes:
            fail(errors, f"node {node_id} has invalid epistemicClass: {node.get('epistemicClass')}")
        if node.get("domain") not in domains:
            fail(errors, f"node {node_id} has invalid domain: {node.get('domain')}")
        if not isinstance(node.get("tags", []), list):
            fail(errors, f"node {node_id} tags must be an array")
        if not isinstance(node.get("sourceRefs", []), list):
            fail(errors, f"node {node_id} sourceRefs must be an array")
        else:
            validate_refs(node.get("sourceRefs", []), known_refs, f"node {node_id}", errors)
        if node.get("epistemicClass") == "aspirational":
            marker_values = {node.get("status"), *node.get("tags", [])}
            if not ({"aspirational", "open", "future"} & marker_values):
                fail(errors, f"aspirational node {node_id} must be visibly aspirational/open/future")
        if node.get("epistemicClass") == "doctrinal":
            marker_values = {node.get("status"), *node.get("tags", [])}
            if "doctrine" not in marker_values and "doctrinal" not in marker_values:
                fail(errors, f"doctrinal node {node_id} must be visibly doctrinal")
        contains_visual_coordinates(node.get("metadata", {}), f"node {node_id}.metadata", errors)

    return by_id


def validate_edges(
    data: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> list[dict[str, Any]]:
    edges = data.get("edges", [])
    classes = set(data.get("epistemicClasses", {}).keys())
    relations = set(data.get("edgeRelations", []))
    known_refs = {ref.get("id") for ref in data.get("sourceRefs", []) if isinstance(ref, dict)}
    node_ids = set(nodes_by_id.keys())

    if not isinstance(edges, list):
        fail(errors, "edges must be an array")
        return []

    find_duplicate_ids(edges, "edge", errors)
    for edge in edges:
        if not isinstance(edge, dict):
            fail(errors, "each edge must be an object")
            continue
        edge_id = edge.get("id", "<missing>")
        missing = EDGE_REQUIRED - set(edge.keys())
        for key in sorted(missing):
            fail(errors, f"edge {edge_id} missing required field: {key}")
        if edge.get("from") not in node_ids:
            fail(errors, f"edge {edge_id} references missing from node: {edge.get('from')}")
        if edge.get("to") not in node_ids:
            fail(errors, f"edge {edge_id} references missing to node: {edge.get('to')}")
        if edge.get("relation") not in relations:
            fail(errors, f"edge {edge_id} has invalid relation: {edge.get('relation')}")
        if edge.get("epistemicClass") not in classes:
            fail(errors, f"edge {edge_id} has invalid epistemicClass: {edge.get('epistemicClass')}")
        if edge.get("role") not in {"primary", "cross-link"}:
            fail(errors, f"edge {edge_id} role must be primary or cross-link")
        if not isinstance(edge.get("sourceRefs", []), list):
            fail(errors, f"edge {edge_id} sourceRefs must be an array")
        else:
            validate_refs(edge.get("sourceRefs", []), known_refs, f"edge {edge_id}", errors)
    return edges


def validate_primary_projection(
    data: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    errors: list[str],
) -> None:
    node_ids = set(nodes_by_id.keys())
    roots = data.get("rootNodeIds", [])
    if not isinstance(roots, list) or not roots:
        fail(errors, "rootNodeIds must be a non-empty array")
        return
    for root in roots:
        if root not in node_ids:
            fail(errors, f"rootNodeIds references missing node: {root}")

    primary_edges = [edge for edge in edges if edge.get("role") == "primary"]
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in primary_edges:
        source = edge.get("from")
        target = edge.get("to")
        if source in node_ids and target in node_ids:
            outgoing[source].append(target)
            incoming[target].append(source)

    for root in roots:
        if incoming.get(root):
            fail(errors, f"root node {root} must not have primary incoming edges")

    non_roots = node_ids - set(roots)
    for node_id in sorted(non_roots):
        if not incoming.get(node_id):
            fail(errors, f"node {node_id} is orphaned in primary projection")
        elif len(incoming[node_id]) > 1:
            fail(errors, f"node {node_id} has multiple primary parents: {', '.join(sorted(incoming[node_id]))}")

    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node_id: str, trail: list[str]) -> None:
        if node_id in visiting:
            fail(errors, "primary projection cycle: " + " -> ".join([*trail, node_id]))
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in outgoing.get(node_id, []):
            visit(child, [*trail, node_id])
        visiting.remove(node_id)
        visited.add(node_id)

    for root in roots:
        visit(root, [])

    reachable: set[str] = set()
    queue: deque[str] = deque(root for root in roots if root in node_ids)
    while queue:
        node_id = queue.popleft()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        queue.extend(outgoing.get(node_id, []))

    for node_id in sorted(node_ids - reachable):
        fail(errors, f"node {node_id} is not reachable from rootNodeIds through primary edges")


def validate_provenance(data: dict[str, Any], manifest_path: Path, errors: list[str]) -> None:
    provenance = data.get("provenance", {})
    if not isinstance(provenance, dict):
        fail(errors, "provenance must be an object")
        return
    for key in ("repository", "sourceDocuments", "schema", "generator", "validator", "generatedArtifacts"):
        if key not in provenance:
            fail(errors, f"provenance missing required field: {key}")
    repo_root = manifest_path.resolve().parents[1]
    for source in provenance.get("sourceDocuments", []):
        if not (repo_root / source).exists():
            fail(errors, f"provenance sourceDocument does not exist: {source}")


def validate_manifest(path: Path) -> list[str]:
    data = load_manifest(path)
    errors: list[str] = []

    require_top_level(data, errors)

    source_refs = data.get("sourceRefs", [])
    if isinstance(source_refs, list):
        find_duplicate_ids([ref for ref in source_refs if isinstance(ref, dict)], "sourceRef", errors)
    else:
        fail(errors, "sourceRefs must be an array")

    nodes_by_id = validate_nodes(data, errors)
    edges = validate_edges(data, nodes_by_id, errors)
    validate_primary_projection(data, nodes_by_id, edges, errors)
    validate_provenance(data, path, errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to tree.manifest.json",
    )
    args = parser.parse_args(argv)

    try:
        errors = validate_manifest(args.manifest)
    except ValidationError as exc:
        print(f"Tree manifest validation failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Tree manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Tree manifest validation passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
