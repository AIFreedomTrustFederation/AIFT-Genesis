#!/usr/bin/env python3
"""Render the AIFT Tree of Emergence from the canonical manifest."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "manifests" / "tree.manifest.json"
DEFAULT_SVG = REPO_ROOT / "docs" / "generated" / "tree-of-emergence.svg"
DEFAULT_HTML = REPO_ROOT / "docs" / "generated" / "tree-of-emergence.html"

sys.path.insert(0, str(REPO_ROOT / "tools" / "validation"))
from validate_tree import validate_manifest  # noqa: E402


DOMAIN_COLORS = {
    "metaphysical-doctrinal": "#7057c4",
    "physical": "#2563eb",
    "chemical": "#0f766e",
    "biological": "#2f7d32",
    "ecological": "#6b8e23",
    "cognitive": "#a35d00",
    "human-cultural": "#b33f62",
    "technological": "#475569",
    "ai": "#0e7490",
    "federation": "#7c3aed",
    "future": "#c2410c",
}

CLASS_BADGES = {
    "empirical": "EMP",
    "scientific-consensus": "SCI",
    "active-research": "RES",
    "interpretive": "INT",
    "philosophical": "PHI",
    "doctrinal": "DOC",
    "engineering": "ENG",
    "prototype": "PRO",
    "architectural": "ARC",
    "aspirational": "ASP",
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def domain_label(domain: str) -> str:
    return domain.replace("-", " ").replace("_", " ").title()


def wrap_text(text: str, max_chars: int = 21, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) <= max_lines:
        return lines
    trimmed = lines[:max_lines]
    trimmed[-1] = trimmed[-1].rstrip(".") + "..."
    return trimmed


def build_layout(manifest: dict[str, Any]) -> dict[str, Any]:
    nodes = {node["id"]: node for node in manifest["nodes"]}
    domains = {domain: index for index, domain in enumerate(manifest["domains"])}
    children: dict[str, list[str]] = defaultdict(list)
    primary_edges = [edge for edge in manifest["edges"] if edge["role"] == "primary"]
    for edge in primary_edges:
        children[edge["from"]].append(edge["to"])
    for parent, child_ids in children.items():
        child_ids.sort(key=lambda node_id: (domains.get(nodes[node_id]["domain"], 999), nodes[node_id]["label"], node_id))

    positions: dict[str, tuple[float, float, int]] = {}
    leaf_index = 0
    max_depth = 0
    visited: set[str] = set()

    def place(node_id: str, depth: int) -> float:
        nonlocal leaf_index, max_depth
        max_depth = max(max_depth, depth)
        if node_id in visited:
            x, _, _ = positions[node_id]
            return x
        visited.add(node_id)
        child_ids = children.get(node_id, [])
        if not child_ids:
            x = float(leaf_index)
            leaf_index += 1
        else:
            child_x = [place(child, depth + 1) for child in child_ids]
            x = sum(child_x) / len(child_x)
        positions[node_id] = (x, float(depth), depth)
        return x

    for root in manifest["rootNodeIds"]:
        place(root, 0)

    leaf_count = max(leaf_index, 1)
    margin_x = 120
    margin_y = 190
    x_gap = 230
    y_gap = 150
    width = int(max(1320, (leaf_count - 1) * x_gap + margin_x * 2))
    height = int(max(900, max_depth * y_gap + margin_y + 190))
    scaled_positions = {
        node_id: {
            "x": margin_x + x * x_gap,
            "y": margin_y + depth * y_gap,
            "depth": depth,
        }
        for node_id, (x, _y, depth) in positions.items()
    }
    return {
        "nodes": nodes,
        "children": children,
        "positions": scaled_positions,
        "width": width,
        "height": height,
        "primaryEdges": primary_edges,
        "crossEdges": [edge for edge in manifest["edges"] if edge["role"] == "cross-link"],
    }


def edge_path(start: dict[str, float], end: dict[str, float]) -> str:
    x1 = start["x"]
    y1 = start["y"] + 42
    x2 = end["x"]
    y2 = end["y"] - 42
    mid = (y1 + y2) / 2
    return f"M {x1:.1f} {y1:.1f} C {x1:.1f} {mid:.1f}, {x2:.1f} {mid:.1f}, {x2:.1f} {y2:.1f}"


def render_node(node: dict[str, Any], position: dict[str, float], interactive: bool) -> str:
    node_id = node["id"]
    domain = node["domain"]
    epistemic = node["epistemicClass"]
    color = DOMAIN_COLORS.get(domain, "#475569")
    badge = CLASS_BADGES.get(epistemic, epistemic[:3].upper())
    x = position["x"]
    y = position["y"]
    label_lines = wrap_text(node["shortLabel"])
    label_y = y - 10 if len(label_lines) == 1 else y - 18
    attrs = [
        f'id="node-{esc(node_id)}"',
        'class="tree-node"',
        f'data-node-id="{esc(node_id)}"',
        f'data-domain="{esc(domain)}"',
        f'data-epistemic="{esc(epistemic)}"',
        f'data-x="{x:.1f}"',
        f'data-y="{y:.1f}"',
        f'aria-label="{esc(node["label"])}; {esc(domain_label(domain))}; {esc(epistemic)}"',
    ]
    if interactive:
        attrs.extend(['tabindex="0"', 'role="button"'])
    else:
        attrs.append('role="img"')

    text_parts = [
        f"<g {' '.join(attrs)}>",
        f"<title>{esc(node['label'])}: {esc(node['description'])}</title>",
        f'<rect x="{x - 88:.1f}" y="{y - 45:.1f}" width="176" height="90" rx="8" fill="#ffffff" stroke="{color}" stroke-width="3" />',
        f'<rect x="{x - 88:.1f}" y="{y - 45:.1f}" width="176" height="8" rx="4" fill="{color}" />',
        f'<circle cx="{x - 69:.1f}" cy="{y + 25:.1f}" r="16" fill="{color}" />',
        f'<text x="{x - 69:.1f}" y="{y + 29:.1f}" text-anchor="middle" class="node-badge">{esc(badge)}</text>',
    ]
    for index, line in enumerate(label_lines):
        text_parts.append(
            f'<text x="{x:.1f}" y="{label_y + index * 16:.1f}" text-anchor="middle" class="node-label">{esc(line)}</text>'
        )
    text_parts.append(
        f'<text x="{x + 14:.1f}" y="{y + 23:.1f}" class="node-domain">{esc(domain_label(domain))}</text>'
    )
    text_parts.append(
        f'<text x="{x + 14:.1f}" y="{y + 39:.1f}" class="node-class">{esc(epistemic)}</text>'
    )
    text_parts.append("</g>")
    return "\n".join(text_parts)


def render_edges(edges: list[dict[str, Any]], layout: dict[str, Any], role: str) -> str:
    positions = layout["positions"]
    parts: list[str] = []
    for edge in edges:
        if edge["from"] not in positions or edge["to"] not in positions:
            continue
        path = edge_path(positions[edge["from"]], positions[edge["to"]])
        css_class = "primary-edge" if role == "primary" else "cross-edge"
        marker = ' marker-end="url(#arrow)"' if role == "primary" else ""
        parts.append(
            f'<path id="edge-{esc(edge["id"])}" class="{css_class}" data-edge-id="{esc(edge["id"])}" '
            f'data-from="{esc(edge["from"])}" data-to="{esc(edge["to"])}" data-relation="{esc(edge["relation"])}" '
            f'd="{path}"{marker}><title>{esc(edge["description"])}</title></path>'
        )
    return "\n".join(parts)


def render_legend(manifest: dict[str, Any]) -> str:
    domain_items = []
    x = 40
    y = 78
    for index, domain in enumerate(manifest["domains"]):
        item_x = x + (index % 4) * 260
        item_y = y + (index // 4) * 28
        color = DOMAIN_COLORS.get(domain, "#475569")
        domain_items.append(
            f'<g class="legend-item"><rect x="{item_x}" y="{item_y - 13}" width="18" height="18" fill="{color}" />'
            f'<text x="{item_x + 26}" y="{item_y + 1}" class="legend-text">{esc(domain_label(domain))}</text></g>'
        )
    class_items = []
    class_x = 1120
    class_y = 78
    for index, (class_id, class_info) in enumerate(manifest["epistemicClasses"].items()):
        item_y = class_y + index * 24
        badge = CLASS_BADGES.get(class_id, class_id[:3].upper())
        class_items.append(
            f'<g class="legend-item"><circle cx="{class_x}" cy="{item_y - 5}" r="11" fill="#1f2937" />'
            f'<text x="{class_x}" y="{item_y - 1}" text-anchor="middle" class="legend-badge">{esc(badge)}</text>'
            f'<text x="{class_x + 20}" y="{item_y}" class="legend-text">{esc(class_info["label"])}</text></g>'
        )
    return "\n".join(
        [
            '<g id="legend" class="legend">',
            '<rect x="24" y="24" width="1510" height="300" rx="8" fill="#f8fafc" stroke="#cbd5e1" />',
            '<text x="40" y="54" class="legend-heading">Domains</text>',
            *domain_items,
            '<text x="1120" y="54" class="legend-heading">Epistemic status badges</text>',
            *class_items,
            '<line x1="40" y1="292" x2="150" y2="292" class="primary-edge" marker-end="url(#arrow)" />',
            '<text x="165" y="296" class="legend-text">Primary lineage projection</text>',
            '<line x1="430" y1="292" x2="540" y2="292" class="cross-edge" />',
            '<text x="555" y="296" class="legend-text">Cross-link influence or dependency</text>',
            '</g>',
        ]
    )


def render_svg(manifest: dict[str, Any], interactive: bool = False) -> str:
    layout = build_layout(manifest)
    width = layout["width"]
    height = layout["height"] + 210
    title_id = "aift-tree-title"
    desc_id = "aift-tree-desc"
    nodes = [layout["nodes"][node_id] for node_id in sorted(layout["positions"], key=lambda n: (layout["positions"][n]["depth"], layout["positions"][n]["x"]))]
    node_markup = "\n".join(render_node(node, layout["positions"][node["id"]], interactive) for node in nodes)
    viewport_open = '<g id="viewport" transform="translate(0 210)">'
    viewport_close = "</g>"
    generated_note = (
        "Generated from manifests/tree.manifest.json by tools/tree/render_tree.py. "
        "Do not hand-edit generated artifacts; edit the canonical manifest instead."
    )
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f"<!-- {generated_note} -->",
            f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{title_id} {desc_id}" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
            f'<title id="{title_id}">{esc(manifest["title"])}</title>',
            f'<desc id="{desc_id}">{esc(manifest["description"])} Domains are labeled by color and text; epistemic classes are shown as badges and text.</desc>',
            "<defs>",
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />',
            "</marker>",
            "</defs>",
            "<style>",
            "svg { background: #f8fafc; font-family: Arial, Helvetica, sans-serif; }",
            ".title { font-size: 30px; font-weight: 700; fill: #0f172a; }",
            ".subtitle { font-size: 15px; fill: #334155; }",
            ".primary-edge { fill: none; stroke: #334155; stroke-width: 2.4; }",
            ".cross-edge { fill: none; stroke: #64748b; stroke-width: 1.5; stroke-dasharray: 7 6; opacity: 0.72; }",
            ".tree-node rect { filter: drop-shadow(0 1px 2px rgba(15, 23, 42, 0.16)); }",
            ".node-label { font-size: 15px; font-weight: 700; fill: #111827; }",
            ".node-domain { font-size: 11px; font-weight: 700; fill: #334155; }",
            ".node-class { font-size: 10px; fill: #475569; }",
            ".node-badge, .legend-badge { font-size: 9px; font-weight: 700; fill: #ffffff; }",
            ".legend-heading { font-size: 15px; font-weight: 700; fill: #0f172a; }",
            ".legend-text { font-size: 13px; fill: #334155; }",
            ".tree-node:focus rect { stroke-width: 5; }",
            "</style>",
            '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc" />',
            f'<text x="40" y="42" class="title">{esc(manifest["title"])}</text>',
            '<text x="40" y="69" class="subtitle">One history, many branches, continuing emergence. The manifest defines meaning; this SVG is a deterministic projection.</text>',
            render_legend(manifest),
            viewport_open,
            '<g id="cross-links">',
            render_edges(layout["crossEdges"], layout, "cross-link"),
            "</g>",
            '<g id="primary-links">',
            render_edges(layout["primaryEdges"], layout, "primary"),
            "</g>",
            '<g id="nodes">',
            node_markup,
            "</g>",
            viewport_close,
            "</svg>",
        ]
    )


def render_filter_group(title: str, name: str, values: list[str], labels: dict[str, str] | None = None) -> str:
    items = [f'<fieldset><legend>{esc(title)}</legend>']
    for value in values:
        label = labels.get(value, value) if labels else value
        items.append(
            f'<label><input type="checkbox" name="{esc(name)}" value="{esc(value)}" checked> {esc(label)}</label>'
        )
    items.append("</fieldset>")
    return "\n".join(items)


def render_html(manifest: dict[str, Any]) -> str:
    svg = render_svg(manifest, interactive=True)
    embedded_data = json.dumps(manifest, indent=2, sort_keys=True).replace("</", "<\\/")
    domain_labels = {domain: domain_label(domain) for domain in manifest["domains"]}
    class_labels = {key: value["label"] for key, value in manifest["epistemicClasses"].items()}
    source_refs = {ref["id"]: ref for ref in manifest["sourceRefs"]}
    source_data = json.dumps(source_refs, sort_keys=True).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(manifest["title"])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #0f172a;
      --muted: #475569;
      --line: #cbd5e1;
      --accent: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    header {{
      padding: 20px 24px 14px;
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 8px 0 0;
      max-width: 980px;
      color: var(--muted);
      line-height: 1.45;
      font-size: 14px;
    }}
    .app {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr) 360px;
      min-height: calc(100vh - 86px);
    }}
    aside, .details {{
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 16px;
      overflow: auto;
    }}
    .details {{
      border-right: 0;
      border-left: 1px solid var(--line);
    }}
    main {{
      min-width: 0;
      overflow: hidden;
      position: relative;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      padding: 10px;
      border-bottom: 1px solid var(--line);
      background: #f1f5f9;
    }}
    button, input[type="search"] {{
      min-height: 36px;
      border: 1px solid #94a3b8;
      border-radius: 6px;
      background: #ffffff;
      color: var(--ink);
      font: inherit;
    }}
    button {{
      padding: 0 12px;
      cursor: pointer;
    }}
    button:focus, input:focus, .tree-node:focus rect {{
      outline: 3px solid #14b8a6;
      outline-offset: 2px;
    }}
    input[type="search"] {{
      width: 100%;
      padding: 0 10px;
      margin: 0 0 14px;
    }}
    fieldset {{
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 0 0 14px;
      padding: 10px;
    }}
    legend {{
      font-weight: 700;
      font-size: 13px;
      padding: 0 4px;
    }}
    label {{
      display: block;
      margin: 7px 0;
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
    }}
    .viewer {{
      width: 100%;
      height: calc(100vh - 141px);
      overflow: hidden;
      background: #e2e8f0;
    }}
    .viewer svg {{
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
    }}
    .tree-node {{
      cursor: pointer;
    }}
    .is-hidden {{
      display: none;
    }}
    .details h2 {{
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.25;
    }}
    .meta {{
      display: grid;
      grid-template-columns: 110px 1fr;
      gap: 6px 12px;
      font-size: 13px;
      margin: 12px 0;
    }}
    .meta dt {{
      color: var(--muted);
      font-weight: 700;
    }}
    .meta dd {{
      margin: 0;
    }}
    .details p, .details li {{
      font-size: 14px;
      line-height: 1.45;
    }}
    .details ul {{
      padding-left: 18px;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 7px;
      border-radius: 999px;
      background: #e2e8f0;
      color: #1f2937;
      font-size: 12px;
      font-weight: 700;
    }}
    .small {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }}
    @media (max-width: 1050px) {{
      .app {{
        grid-template-columns: 1fr;
      }}
      aside, .details {{
        border: 0;
        border-bottom: 1px solid var(--line);
        max-height: none;
      }}
      .viewer {{
        height: 68vh;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{esc(manifest["title"])}</h1>
    <p class="subtitle">Generated from <code>manifests/tree.manifest.json</code>. The manifest is authoritative; this standalone explorer is a practical, accessible projection for review.</p>
  </header>
  <div class="app">
    <aside aria-label="Tree filters">
      <label for="search"><strong>Search nodes</strong></label>
      <input id="search" type="search" autocomplete="off" placeholder="Search by name, domain, or description">
      {render_filter_group("Domains", "domain", manifest["domains"], domain_labels)}
      {render_filter_group("Epistemic status", "epistemic", list(manifest["epistemicClasses"].keys()), class_labels)}
      <fieldset>
        <legend>Relationships</legend>
        <label><input type="checkbox" id="show-primary" checked> Primary lineage</label>
        <label><input type="checkbox" id="show-cross" checked> Cross-links</label>
      </fieldset>
      <p class="small">Primary edges define the acyclic tree projection. Cross-links preserve influence, dependency, and federation relationships that do not fit a single branch.</p>
    </aside>
    <main aria-label="Tree visualization">
      <div class="toolbar" aria-label="View controls">
        <button type="button" id="zoom-in">Zoom in</button>
        <button type="button" id="zoom-out">Zoom out</button>
        <button type="button" id="reset-view">Reset view</button>
        <button type="button" id="reset-filters">Reset filters</button>
      </div>
      <div class="viewer" id="viewer">
        {svg}
      </div>
    </main>
    <section class="details" aria-live="polite" aria-label="Selected node details">
      <h2 id="detail-title">Select a node</h2>
      <p id="detail-description">Use search, filters, or keyboard focus to inspect a node.</p>
      <dl class="meta" id="detail-meta"></dl>
      <div id="detail-relationships"></div>
      <div id="detail-sources"></div>
    </section>
  </div>
  <script type="application/json" id="tree-data">
{embedded_data}
  </script>
  <script type="application/json" id="source-data">
{source_data}
  </script>
  <script>
    const tree = JSON.parse(document.getElementById('tree-data').textContent);
    const sources = JSON.parse(document.getElementById('source-data').textContent);
    const nodes = new Map(tree.nodes.map((node) => [node.id, node]));
    const edges = tree.edges;
    const svgEl = document.querySelector('.viewer svg');
    const viewport = document.getElementById('viewport');
    const initialScale = 3.4;
    let scale = initialScale;
    let panX = 0;
    let panY = 0;
    let dragging = false;
    let lastPoint = null;

    function selectedValues(name) {{
      return new Set([...document.querySelectorAll(`input[name="${{name}}"]:checked`)].map((input) => input.value));
    }}

    function visibleNodeIds() {{
      return new Set([...document.querySelectorAll('.tree-node:not(.is-hidden)')].map((node) => node.dataset.nodeId));
    }}

    function nodeMatchesSearch(node, query) {{
      if (!query) return true;
      const haystack = [node.label, node.shortLabel, node.description, node.domain, node.epistemicClass, node.id, ...(node.tags || [])].join(' ').toLowerCase();
      return haystack.includes(query);
    }}

    function applyFilters() {{
      const domains = selectedValues('domain');
      const classes = selectedValues('epistemic');
      const query = document.getElementById('search').value.trim().toLowerCase();
      for (const element of document.querySelectorAll('.tree-node')) {{
        const node = nodes.get(element.dataset.nodeId);
        const shown = domains.has(node.domain) && classes.has(node.epistemicClass) && nodeMatchesSearch(node, query);
        element.classList.toggle('is-hidden', !shown);
      }}
      const visible = visibleNodeIds();
      const showPrimary = document.getElementById('show-primary').checked;
      const showCross = document.getElementById('show-cross').checked;
      for (const edge of document.querySelectorAll('[data-edge-id]')) {{
        const roleShown = edge.classList.contains('primary-edge') ? showPrimary : showCross;
        const shown = roleShown && visible.has(edge.dataset.from) && visible.has(edge.dataset.to);
        edge.classList.toggle('is-hidden', !shown);
      }}
    }}

    function formatValue(value) {{
      return String(value || '').replace(/[-_]/g, ' ');
    }}

    function renderDetails(nodeId) {{
      const node = nodes.get(nodeId);
      if (!node) return;
      document.getElementById('detail-title').textContent = node.label;
      document.getElementById('detail-description').textContent = node.description;
      document.getElementById('detail-meta').innerHTML = `
        <dt>Canonical ID</dt><dd><code>${{node.id}}</code></dd>
        <dt>Domain</dt><dd>${{formatValue(node.domain)}}</dd>
        <dt>Epistemic</dt><dd><span class="badge">${{formatValue(node.epistemicClass)}}</span></dd>
        <dt>Status</dt><dd>${{formatValue(node.status)}}</dd>
      `;
      const related = edges.filter((edge) => edge.from === node.id || edge.to === node.id);
      const relationItems = related.map((edge) => {{
        const direction = edge.from === node.id ? 'to' : 'from';
        const otherId = edge.from === node.id ? edge.to : edge.from;
        const other = nodes.get(otherId);
        return `<li><strong>${{formatValue(edge.relation)}}</strong> ${{direction}} <button type="button" data-select-node="${{otherId}}">${{other ? other.label : otherId}}</button> <span class="small">(${{edge.role}})</span></li>`;
      }}).join('');
      document.getElementById('detail-relationships').innerHTML = `<h3>Relationships</h3><ul>${{relationItems || '<li>No relationships found.</li>'}}</ul>`;
      const sourceItems = (node.sourceRefs || []).map((refId) => {{
        const source = sources[refId];
        return source ? `<li><code>${{refId}}</code>: ${{source.label}} <span class="small">${{source.uri}}</span></li>` : `<li><code>${{refId}}</code></li>`;
      }}).join('');
      document.getElementById('detail-sources').innerHTML = `<h3>Sources</h3><ul>${{sourceItems || '<li>No repository source reference declared for this node.</li>'}}</ul>`;
      document.querySelectorAll('[data-select-node]').forEach((button) => {{
        button.addEventListener('click', () => renderDetails(button.dataset.selectNode));
      }});
    }}

    function updateTransform() {{
      viewport.setAttribute('transform', `translate(${{panX}} ${{210 + panY}}) scale(${{scale}})`);
    }}

    function focusNode(nodeId, targetY = 520) {{
      const element = document.querySelector(`[data-node-id="${{nodeId}}"]`);
      if (!element || !svgEl.viewBox || !svgEl.viewBox.baseVal) return;
      const nodeX = Number(element.dataset.x || 0);
      const nodeY = Number(element.dataset.y || 0);
      const box = svgEl.viewBox.baseVal;
      panX = box.width * 0.52 - nodeX * scale;
      panY = targetY - 210 - nodeY * scale;
      updateTransform();
    }}

    function zoomBy(factor) {{
      scale = Math.max(0.35, Math.min(3, scale * factor));
      updateTransform();
    }}

    document.querySelectorAll('.tree-node').forEach((nodeEl) => {{
      nodeEl.addEventListener('click', () => renderDetails(nodeEl.dataset.nodeId));
      nodeEl.addEventListener('keydown', (event) => {{
        if (event.key === 'Enter' || event.key === ' ') {{
          event.preventDefault();
          renderDetails(nodeEl.dataset.nodeId);
        }}
      }});
    }});

    document.querySelectorAll('input[type="checkbox"], #search').forEach((input) => {{
      input.addEventListener('input', applyFilters);
      input.addEventListener('change', applyFilters);
    }});

    document.getElementById('zoom-in').addEventListener('click', () => zoomBy(1.18));
    document.getElementById('zoom-out').addEventListener('click', () => zoomBy(0.85));
    document.getElementById('reset-view').addEventListener('click', () => {{
      scale = initialScale;
      focusNode(tree.rootNodeIds[0]);
    }});
    document.getElementById('reset-filters').addEventListener('click', () => {{
      document.getElementById('search').value = '';
      document.querySelectorAll('input[type="checkbox"]').forEach((input) => {{ input.checked = true; }});
      applyFilters();
    }});

    svgEl.addEventListener('wheel', (event) => {{
      event.preventDefault();
      zoomBy(event.deltaY < 0 ? 1.08 : 0.92);
    }}, {{ passive: false }});
    svgEl.addEventListener('pointerdown', (event) => {{
      dragging = true;
      lastPoint = {{ x: event.clientX, y: event.clientY }};
      svgEl.setPointerCapture(event.pointerId);
    }});
    svgEl.addEventListener('pointermove', (event) => {{
      if (!dragging || !lastPoint) return;
      panX += event.clientX - lastPoint.x;
      panY += event.clientY - lastPoint.y;
      lastPoint = {{ x: event.clientX, y: event.clientY }};
      updateTransform();
    }});
    svgEl.addEventListener('pointerup', () => {{
      dragging = false;
      lastPoint = null;
    }});

    focusNode(tree.rootNodeIds[0]);
    applyFilters();
    renderDetails(tree.rootNodeIds[0]);
  </script>
</body>
</html>
"""


def write_if_changed(path: Path, content: str) -> bool:
    normalized = content.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == normalized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    return True


def check_file(path: Path, content: str) -> bool:
    expected = content.rstrip() + "\n"
    return path.exists() and path.read_text(encoding="utf-8") == expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--check", action="store_true", help="Fail if generated artifacts are missing or stale")
    args = parser.parse_args(argv)

    errors = validate_manifest(args.manifest)
    if errors:
        print("Tree manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    manifest = load_manifest(args.manifest)
    svg = render_svg(manifest)
    html_doc = render_html(manifest)

    if args.check:
        stale = []
        if not check_file(args.svg, svg):
            stale.append(str(args.svg))
        if not check_file(args.html, html_doc):
            stale.append(str(args.html))
        if stale:
            print("Generated Tree artifacts are stale or missing:", file=sys.stderr)
            for path in stale:
                print(f"- {path}", file=sys.stderr)
            return 1
        print("Generated Tree artifacts are current.")
        return 0

    changed_svg = write_if_changed(args.svg, svg)
    changed_html = write_if_changed(args.html, html_doc)
    print(f"SVG {'updated' if changed_svg else 'current'}: {args.svg}")
    print(f"HTML {'updated' if changed_html else 'current'}: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
