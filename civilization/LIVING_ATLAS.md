# Living Atlas

The Living Atlas centers every user in their own Green Zone while connecting them to local and global Federation layers.

The Atlas is the present-tense map of instantiated relationships. It should show
where trusts, missions, repositories, communities, public resources, and
governed systems exist now, while preserving privacy, consent, and local-first
sovereignty.

It is related to, but distinct from, the
[Tree of Emergence](TREE_OF_EMERGENCE.md):

```text
Tree of Emergence = lineage, emergence, inheritance, and branching possibility
Living Atlas      = present relationships, places, actors, and systems
```

The Tree asks how forms emerge and relate across time or possibility. The Atlas
asks where instantiated forms are now and what relationships are visible by
consent. A branch in the Tree may later appear as one or more Atlas nodes, but
the Atlas should not rewrite the canonical Tree manifest and the Tree should not
publish private Atlas location data.

## Machine-readable Atlas contract

The canonical public Atlas contract begins in:

- `schemas/Atlas.schema.json`
- `manifests/living-atlas.manifest.json`
- `tools/validation/validate_atlas.py`

The Atlas uses explicit typed mappings:

```text
Tree canonical node ID
        ^
        | treeMappings[].treeNodeId
        |
Living Atlas entity ID
        |
        v
treeMappings[].atlasEntityId
```

Atlas records must not be inserted into `manifests/tree.manifest.json` merely
because they relate to a Tree node. The Tree answers what a form means in the
emergence graph. The Atlas answers where a form is publicly instantiated now.
Runtime overlays may later answer what is observed happening now.

The public Genesis Atlas manifest should only contain public, evidence-backed
entities. Private Green Zone records, sensitive place data, private repository
state, operational health, and live telemetry belong outside this public
manifest unless a future consented publication path explicitly governs them.

