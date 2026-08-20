# Tree Renderer

`render_tree.py` reads the canonical graph at
`manifests/tree.manifest.json` and writes deterministic review artifacts:

```powershell
python tools\tree\render_tree.py
```

Generated outputs:

- `docs/generated/tree-of-emergence.svg`
- `docs/generated/tree-of-emergence.html`

Check that committed artifacts match the manifest:

```powershell
python tools\tree\render_tree.py --check
```

The manifest remains authoritative. The renderer computes presentation from
primary edges and shows cross-links separately. Do not add semantic meaning by
hand-editing generated coordinates or duplicating the canonical graph inside a
viewer.
