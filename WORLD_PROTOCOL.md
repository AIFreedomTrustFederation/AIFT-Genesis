# AIFT Living Federation World Protocol

`aift.world.v1` is the engine-independent spatial contract shared by AIFT-OS, Mysterion Cortex, native game clients, and accessible web clients.

## Ownership

- AIFT-Genesis owns the schemas.
- AIFT-OS derives snapshots and deltas from inspected evidence.
- Mysterion Cortex renders the immersive world.
- AIFT-Runtime supplies model inference through an adapter.
- mobox runs approved Windows applications and game builds; it does not define world truth.
- VPS transports and hosts services without becoming the truth authority.

## Scale

Canonical coordinates use portable signed decimal strings in logical nanounits. Version 1 intentionally limits magnitude to 18 digits so every schema-valid value fits safely within signed 64-bit consumers. Renderers maintain a floating origin and convert only the visible neighborhood to GPU floating-point coordinates. Worlds are partitioned into independently streamable spatial chunks.

## Truth boundary

A world snapshot is a projection of recorded evidence. Color, scale, symmetry, coherence, proximity, animation, and level never create status, ownership, morality, financial value, scientific proof, or execution authority.

Clients submit proposals. Governed adapters execute only exact approved actions.

## Navigation contract

Clients should support continuous logarithmic altitude, anchored pinch zoom, pan/orbit, optional tilt and rotation, inertia, semantic levels of detail, screen-space labels, collision management, reduced motion, and a non-3D accessible representation.

## Synchronization

A client loads an `aift.world.v1` snapshot, then applies ordered `aift.world.delta.v1` updates.

Delta consumers must enforce these invariants before mutation:

- `revision > base_revision`; duplicate or stale revisions are ignored.
- `base_revision` must equal the currently applied revision. A gap requires a fresh snapshot.
- A complete delta is validated and applied atomically, or not applied at all.
- Operations changing evidence-derived entities require non-empty `evidence_refs`.
- Entity operations target `entity_id`; relation operations target `relation_id`.
- Upserts require a schema-valid `value`; removals prohibit `value`.

## Schemas

- `schemas/world.schema.json`
- `schemas/world-delta.schema.json`
