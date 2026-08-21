# Validation

Future validation tools for links, manifests, schemas, templates, and generated trust packs.

## Tree of Emergence

Validate the canonical Tree of Emergence manifest:

```powershell
python tools\validation\validate_tree.py
```

The validator checks graph integrity beyond JSON syntax:

- unique node and edge IDs;
- edge references to existing nodes;
- valid domains, relations, and epistemic classes;
- preserved legacy `parts`;
- intentional roots;
- no orphan nodes in the primary projection;
- no primary projection cycles;
- one primary parent per non-root node;
- source references declared in the manifest;
- provenance source documents exist;
- visual metadata does not become semantic coordinates.

Regenerate and check the SVG/HTML review artifacts with:

```powershell
python tools\tree\render_tree.py
python tools\tree\render_tree.py --check
```

## Living Atlas

Validate the public Living Atlas manifest and its explicit Tree mappings:

```powershell
python tools\validation\validate_atlas.py
```

The Atlas validator checks:

- unique entity, source, and mapping IDs;
- declared Atlas entity types and mapping relations;
- every `treeMappings[].treeNodeId` exists in `manifests/tree.manifest.json`;
- every `treeMappings[].atlasEntityId` exists in `manifests/living-atlas.manifest.json`;
- source references are declared;
- provenance source documents exist;
- the Tree manifest does not embed Atlas records.

