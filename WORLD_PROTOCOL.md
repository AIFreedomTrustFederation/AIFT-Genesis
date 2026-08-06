# AIFT Living Federation World Protocol

`aift.world.v1` is the engine-independent spatial contract shared by AIFT-OS, Mysterion Cortex, native game clients, accessible web clients, and compatibility runtimes.

## Ownership

- AIFT-Genesis owns the schemas.
- AIFT-OS derives snapshots and deltas from inspected evidence.
- Mysterion Cortex renders the immersive world.
- AIFT-Runtime supplies model inference through an adapter.
- mobox runs approved Windows applications and game builds; it does not define world truth.
- VPS transports and hosts services without becoming the truth authority.

## Scale

Canonical coordinates use signed 64-bit decimal strings in logical nanounits. Renderers maintain a floating origin and convert only the visible neighborhood to GPU floating-point coordinates. Worlds are partitioned into independently streamable spatial chunks.

## Truth boundary

A world snapshot is a projection of recorded evidence. Color, scale, symmetry, coherence, proximity, animation, and level never create status, ownership, morality, financial value, scientific proof, or execution authority.

Clients submit proposals. Governed adapters execute only exact approved actions.

## Navigation contract

Clients should support continuous logarithmic altitude, anchored pinch zoom, pan/orbit, optional tilt and rotation, inertia, semantic levels of detail, screen-space labels, collision management, reduced motion, and a non-3D accessible representation.

## Synchronization

A client loads an `aift.world.v1` snapshot, then applies ordered `aift.world.delta.v1` updates. Revision gaps require a new snapshot. Delta operations carry evidence references when they change an evidence-derived entity.

## Schemas

- `schemas/world.schema.json`
- `schemas/world-delta.schema.json`
