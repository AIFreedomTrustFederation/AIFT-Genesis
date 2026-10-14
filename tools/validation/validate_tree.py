#!/usr/bin/env python3
"""Validate the canonical AIFT Tree of Emergence manifest."""

from __future__ import annotations

import argparse
import json
import re
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
NODE_ALLOWED = NODE_REQUIRED | {"era", "timeRange", "parentHints", "symbol", "canonicalUri"}
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
SOURCE_REF_REQUIRED = {"id", "label", "uri", "type"}
SOURCE_REF_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
SOURCE_REF_TYPES = {
    "external-reference",
    "generated-artifact",
    "repository-document",
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
    allowed = required | {"canonicalDocument", "legacyCompatibility"}
    for key in sorted(required):
        if key not in data:
            fail(errors, f"missing top-level field: {key}")
    for key in sorted(set(data) - allowed):
        fail(errors, f"manifest has unexpected field: {key}")
    if data.get("kind") != "tree-manifest":
        fail(errors, "kind must be tree-manifest")
    if data.get("parts") != LEGACY_PARTS:
        fail(errors, f"parts must preserve legacy order and values: {LEGACY_PARTS}")
    for key in ("schemaVersion", "modelVersion"):
        value = data.get(key)
        if not isinstance(value, str) or value.count(".") != 2:
            fail(errors, f"{key} must be a semantic version string")
    if not isinstance(data.get("epistemicClasses"), dict) or not data.get("epistemicClasses"):
        fail(errors, "epistemicClasses must be a non-empty object")
    domains = data.get("domains")
    if not isinstance(domains, list) or not domains:
        fail(errors, "domains must be a non-empty array")
    elif not all(isinstance(domain, str) for domain in domains):
        fail(errors, "domains must contain strings")
    elif len(domains) != len(set(domains)):
        fail(errors, "domains must contain unique values")
    edge_relations = data.get("edgeRelations")
    if not isinstance(edge_relations, list) or not edge_relations:
        fail(errors, "edgeRelations must be a non-empty array")
    elif not all(isinstance(relation, str) for relation in edge_relations):
        fail(errors, "edgeRelations must contain strings")
    elif len(edge_relations) != len(set(edge_relations)):
        fail(errors, "edgeRelations must contain unique values")


def find_duplicate_ids(items: list[Any], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str):
            fail(errors, f"{label} id must be a string")
            continue
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
    epistemic_classes = data.get("epistemicClasses", {})
    classes = set(epistemic_classes.keys()) if isinstance(epistemic_classes, dict) else set()
    domain_values = data.get("domains", [])
    domains = (
        {domain for domain in domain_values if isinstance(domain, str)}
        if isinstance(domain_values, list)
        else set()
    )
    source_refs = data.get("sourceRefs", [])
    known_refs = (
        {
            ref["id"]
            for ref in source_refs
            if isinstance(ref, dict) and isinstance(ref.get("id"), str)
        }
        if isinstance(source_refs, list)
        else set()
    )

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
        for key in sorted(set(node) - NODE_ALLOWED):
            fail(errors, f"node {node_id} has unexpected field: {key}")
        epistemic_class = node.get("epistemicClass")
        if not isinstance(epistemic_class, str):
            fail(errors, f"node {node_id} epistemicClass must be a string")
        elif epistemic_class not in classes:
            fail(errors, f"node {node_id} has invalid epistemicClass: {epistemic_class}")
        domain = node.get("domain")
        if not isinstance(domain, str):
            fail(errors, f"node {node_id} domain must be a string")
        elif domain not in domains:
            fail(errors, f"node {node_id} has invalid domain: {domain}")
        tags = node.get("tags", [])
        if not isinstance(tags, list):
            fail(errors, f"node {node_id} tags must be an array")
            tags = []
        elif not all(isinstance(tag, str) for tag in tags):
            fail(errors, f"node {node_id} tags must contain strings")
            tags = [tag for tag in tags if isinstance(tag, str)]
        status = node.get("status")
        if not isinstance(status, str):
            fail(errors, f"node {node_id} status must be a string")
        if not isinstance(node.get("sourceRefs", []), list):
            fail(errors, f"node {node_id} sourceRefs must be an array")
        else:
            validate_refs(node.get("sourceRefs", []), known_refs, f"node {node_id}", errors)
        if node.get("epistemicClass") == "aspirational":
            marker_values = {*tags}
            if isinstance(status, str):
                marker_values.add(status)
            if not ({"aspirational", "open", "future"} & marker_values):
                fail(errors, f"aspirational node {node_id} must be visibly aspirational/open/future")
        if node.get("epistemicClass") == "doctrinal":
            marker_values = {*tags}
            if isinstance(status, str):
                marker_values.add(status)
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
    epistemic_classes = data.get("epistemicClasses", {})
    classes = set(epistemic_classes.keys()) if isinstance(epistemic_classes, dict) else set()
    relation_values = data.get("edgeRelations", [])
    relations = (
        {relation for relation in relation_values if isinstance(relation, str)}
        if isinstance(relation_values, list)
        else set()
    )
    source_refs = data.get("sourceRefs", [])
    known_refs = (
        {
            ref["id"]
            for ref in source_refs
            if isinstance(ref, dict) and isinstance(ref.get("id"), str)
        }
        if isinstance(source_refs, list)
        else set()
    )
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
        for key in sorted(set(edge) - EDGE_REQUIRED):
            fail(errors, f"edge {edge_id} has unexpected field: {key}")
        source = edge.get("from")
        target = edge.get("to")
        if not isinstance(source, str):
            fail(errors, f"edge {edge_id} from must be a string")
        elif source not in node_ids:
            fail(errors, f"edge {edge_id} references missing from node: {source}")
        if not isinstance(target, str):
            fail(errors, f"edge {edge_id} to must be a string")
        elif target not in node_ids:
            fail(errors, f"edge {edge_id} references missing to node: {target}")
        relation = edge.get("relation")
        if not isinstance(relation, str):
            fail(errors, f"edge {edge_id} relation must be a string")
        elif relation not in relations:
            fail(errors, f"edge {edge_id} has invalid relation: {relation}")
        epistemic_class = edge.get("epistemicClass")
        if not isinstance(epistemic_class, str):
            fail(errors, f"edge {edge_id} epistemicClass must be a string")
        elif epistemic_class not in classes:
            fail(errors, f"edge {edge_id} has invalid epistemicClass: {epistemic_class}")
        role = edge.get("role")
        if not isinstance(role, str):
            fail(errors, f"edge {edge_id} role must be a string")
        elif role not in {"primary", "cross-link"}:
            fail(errors, f"edge {edge_id} role must be primary or cross-link")
        if not isinstance(edge.get("sourceRefs", []), list):
            fail(errors, f"edge {edge_id} sourceRefs must be an array")
        else:
            validate_refs(edge.get("sourceRefs", []), known_refs, f"edge {edge_id}", errors)
    return [edge for edge in edges if isinstance(edge, dict)]


def validate_primary_projection(
    data: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    errors: list[str],
) -> None:
    node_ids = set(nodes_by_id.keys())
    root_values = data.get("rootNodeIds", [])
    if not isinstance(root_values, list) or not root_values:
        fail(errors, "rootNodeIds must be a non-empty array")
        return
    roots: list[str] = []
    for root in root_values:
        if not isinstance(root, str):
            fail(errors, "rootNodeIds must contain strings")
        else:
            roots.append(root)
    for root in roots:
        if root not in node_ids:
            fail(errors, f"rootNodeIds references missing node: {root}")

    primary_edges = [edge for edge in edges if edge.get("role") == "primary"]
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in primary_edges:
        source = edge.get("from")
        target = edge.get("to")
        if (
            isinstance(source, str)
            and isinstance(target, str)
            and source in node_ids
            and target in node_ids
        ):
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
    required = {
        "repository",
        "sourceDocuments",
        "schema",
        "generator",
        "validator",
        "generatedArtifacts",
        "lastGenerated",
        "sourceCommit",
    }
    for key in sorted(required - set(provenance)):
        fail(errors, f"provenance missing required field: {key}")
    for key in sorted(set(provenance) - required):
        fail(errors, f"provenance has unexpected field: {key}")
    if not isinstance(provenance.get("repository"), str) or not provenance.get("repository"):
        fail(errors, "provenance repository must be a non-empty string")
    for field in ("lastGenerated", "sourceCommit"):
        if provenance.get(field) is not None and not isinstance(provenance.get(field), str):
            fail(errors, f"provenance {field} must be a string or null")
    repo_root = manifest_path.resolve().parents[1]

    def repository_path(relative_path: Any, context: str) -> Path | None:
        if not isinstance(relative_path, str) or not relative_path:
            fail(errors, f"provenance {context} must be a non-empty repository-relative path")
            return None
        candidate = (repo_root / relative_path).resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            fail(errors, f"provenance {context} escapes repository: {relative_path}")
            return None
        return candidate

    source_documents = provenance.get("sourceDocuments", [])
    if not isinstance(source_documents, list):
        fail(errors, "provenance sourceDocuments must be an array")
    else:
        for source in source_documents:
            source_path = repository_path(source, "sourceDocument")
            if source_path is not None:
                if not source_path.exists():
                    fail(errors, f"provenance sourceDocument does not exist: {source}")
                elif not source_path.is_file():
                    fail(errors, f"provenance sourceDocument must be a file: {source}")
    for field in ("schema", "generator", "validator"):
        relative_path = provenance.get(field)
        resolved_path = repository_path(relative_path, field)
        if resolved_path is not None and not resolved_path.is_file():
            fail(errors, f"provenance {field} does not exist: {relative_path}")
    generated_artifacts = provenance.get("generatedArtifacts", [])
    if not isinstance(generated_artifacts, list):
        fail(errors, "provenance generatedArtifacts must be an array")
    else:
        for artifact in generated_artifacts:
            artifact_path = repository_path(artifact, "generatedArtifact")
            if artifact_path is not None and not artifact_path.is_file():
                fail(errors, f"provenance generatedArtifact does not exist: {artifact}")


def validate_manifest(path: Path) -> list[str]:
    data = load_manifest(path)
    errors: list[str] = []

    require_top_level(data, errors)

    source_refs = data.get("sourceRefs", [])
    if isinstance(source_refs, list):
        find_duplicate_ids([ref for ref in source_refs if isinstance(ref, dict)], "sourceRef", errors)
        for ref in source_refs:
            if not isinstance(ref, dict):
                fail(errors, "sourceRefs must contain objects")
                continue
            ref_id = ref.get("id", "<missing>")
            if isinstance(ref_id, str) and SOURCE_REF_ID_RE.fullmatch(ref_id) is None:
                fail(errors, f"sourceRef {ref_id} id must be a lowercase source id")
            for key in sorted(SOURCE_REF_REQUIRED - set(ref)):
                fail(errors, f"sourceRef {ref_id} missing required field: {key}")
            for key in sorted(set(ref) - SOURCE_REF_REQUIRED):
                fail(errors, f"sourceRef {ref_id} has unexpected field: {key}")
            for key in ("label", "uri", "type"):
                if not isinstance(ref.get(key), str) or not ref.get(key):
                    fail(errors, f"sourceRef {ref_id} {key} must be a non-empty string")
            ref_type = ref.get("type")
            if isinstance(ref_type, str) and ref_type not in SOURCE_REF_TYPES:
                fail(errors, f"sourceRef {ref_id} has unknown type: {ref_type}")
            uri = ref.get("uri")
            if isinstance(uri, str) and uri:
                scheme = re.match(r"^[a-z][a-z0-9+.-]*:", uri, re.IGNORECASE)
                if scheme is not None:
                    if scheme.group(0).lower() != "https:":
                        fail(errors, f"sourceRef {ref_id} uri must use HTTPS: {uri}")
                    continue
                source_path = (REPO_ROOT / uri).resolve()
                try:
                    source_path.relative_to(REPO_ROOT)
                except ValueError:
                    fail(errors, f"sourceRef {ref_id} uri escapes repository: {uri}")
                    continue
                if not source_path.is_file():
                    fail(errors, f"sourceRef {ref_id} uri does not exist: {uri}")
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
