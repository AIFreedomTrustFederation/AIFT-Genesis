# Tree of Emergence Example

This example points consumers to the canonical Tree of Emergence graph instead
of duplicating it.

Canonical source:

```text
manifests/tree.manifest.json
```

Schema:

```text
schemas/Tree.schema.json
```

Generated review artifacts:

```text
docs/generated/tree-of-emergence.svg
docs/generated/tree-of-emergence.html
```

Consumer rule:

```text
Read the manifest. Treat generated SVG and HTML as projections. Preserve the
epistemic class, domain, status, sourceRefs, and edge role fields when building
downstream interfaces.
```

Downstream repositories should link to this manifest or consume it through an
explicit import/update path. They should not become competing canonical owners of
the model.
