# AIFT Tree Explorer v1

Status: next-phase roadmap

`AIFT Tree Explorer v1` is the next implementation phase after the canonical
Tree of Emergence graph. Its purpose is to turn the graph into an explorable
knowledge world without weakening the source-of-truth boundary.

The canonical source remains:

```text
manifests/tree.manifest.json
```

The explorer is a consumer and projection of that manifest. It may add
interaction, semantic zoom, guided journeys, visual assets, and Atlas
navigation, but it must not become a competing canonical graph.

## Product Thesis

The experience should let a person move through:

```text
Tree -> branch -> node -> relationships -> Atlas -> living Federation -> Tree
```

The Tree represents lineage, emergence, inheritance, and branching possibility.
The Living Atlas represents current instantiation: repositories, agents,
communities, infrastructure, publications, trusts, missions, and observed
relationships.

Genesis defines what a thing means. Runtime or Atlas-derived overlays may later
show what currently exists. Those datasets must remain visibly distinct.

## V1 Scope

Version 1 should focus on navigability, depth, epistemic integrity, and the
first guided experience. It should not begin with heavy 3D, live Runtime data,
or elaborate animation.

The first build should include:

- semantic zoom from domain-level overview into individual nodes;
- node search, filtering, relationship traversal, and reset-to-whole-tree;
- node detail panels with descriptions, epistemic status, relationships,
  sources, canonical ID, and manifest provenance;
- an Epistemic Lens that visibly distinguishes science, active research,
  philosophy, AIFT doctrine, engineering, prototypes, architecture, and
  aspiration;
- Tree-to-Atlas navigation slots using canonical IDs, even before all Atlas
  records exist;
- Aetherion represented as federated relationships rather than a single boss
  node;
- Story Mode beginning at Energence, moving through selected milestones, and
  ending by revealing new seeds beyond Aetherion.

## Navigation Model

The full Tree of Emergence should begin as the world map. A user should be able
to:

1. Start at the whole Tree.
2. Zoom into a domain such as Physical, Life, Mind, Civilization, Technology,
   or Federation.
3. Select a node.
4. Read its detail layer.
5. Follow outgoing and incoming relationships.
6. Switch the Epistemic Lens on or off.
7. Move from an emergence node into related Living Atlas instances.
8. Return to the whole Tree without losing orientation.

The interface should make it clear whether a visible relationship is a primary
lineage edge or a cross-link. Primary edges produce the tree projection.
Cross-links preserve influence, dependency, implementation, and federation
relationships.

## Semantic Zoom

The explorer should not display every node at every distance. From far away,
users should see large structures:

```text
Physical -> Life -> Mind -> Civilization -> Technology -> Federation
```

As the camera moves closer, each structure should unfold into branches, then
individual nodes, then relationships and evidence. This approach is required if
the model grows from dozens of nodes to hundreds or thousands.

Semantic zoom should be derived from manifest fields such as `domain`,
`presentationRole`, edge role, and future view metadata. Coordinates or layout
preferences must remain renderer concerns, not canonical meaning.

## Node Depth

Every node should be able to open a detail layer. V1 should support:

- label, short label, canonical ID, and canonical URI;
- description and domain;
- epistemic class and status;
- tags and claim-boundary notes;
- incoming and outgoing relationships;
- source references and generated provenance;
- optional illustration or visual asset slot;
- optional ALO'ha or doctrine passage slot where appropriate;
- Living Atlas link slot;
- related generated artifacts or examples.

This detail layer is where the visualization becomes a knowledge system rather
than an infographic.

## Epistemic Lens

The Epistemic Lens should be one of the defining features of the explorer.

When enabled, it should make each node's classification unmistakable:

- empirical;
- scientific-consensus;
- active-research;
- interpretive;
- philosophical;
- doctrinal;
- engineering;
- prototype;
- architectural;
- aspirational.

Selecting Energence should make its doctrinal and metaphysical status visible.
Selecting a scientific node should show its empirical or consensus status.
Selecting Aetherion should show its architectural and aspirational status. The
viewer should never require a user to guess whether something is science,
interpretation, doctrine, implementation, or aspiration.

## Tree and Atlas Boundary

The Tree and the Living Atlas should connect, but they should not collapse into
one dataset.

```text
Tree of Emergence = canonical lineage and meaning
Living Atlas      = present instantiated relationships
AIFT-Runtime      = observed current state overlays
```

An `artificial-intelligence` node in the Tree can link to current AI-related
repositories, agents, documents, or services in the Atlas. Those Atlas records
should use canonical IDs or explicit mapping fields, but they must remain
separate from the Tree manifest.

Runtime overlays should come later, after the static canonical experience is
strong. Runtime may show observed repositories, deployments, health, agents,
publications, and services. Runtime must not redefine what a canonical Tree node
means.

## Aetherion Canopy

The visual language should change in the upper canopy. Branches may gradually
become network relationships.

Aetherion should emerge from relationships among:

- human beings and communities;
- trust systems;
- governed repositories;
- AI systems and agents;
- knowledge and provenance;
- infrastructure;
- governance;
- local sovereign intelligence;
- cooperative and federated intelligence.

Aetherion must not appear as a giant central brain, a final boss node, a proven
conscious entity, or the end of evolution. The view should end by revealing new
seeds leaving the canopy.

## Story Mode

Story Mode is the first guided journey for a new visitor. It should:

1. Begin at Energence with its doctrinal status visible.
2. Move through physical, chemical, biological, cognitive, cultural,
   technological, AI, and Federation milestones.
3. Show branches appearing around the path so the journey never becomes a
   simplistic ladder.
4. Pause at selected nodes to reveal short explanations and epistemic status.
5. Reach the Aetherion canopy as a federated relationship field.
6. Pull outward to show new seeds leaving the Tree.
7. Let the user exit into free exploration.

Story Mode should be skippable, keyboard-operable, and respectful of reduced
motion preferences.

## Accessibility Requirements

Explorer v1 should support:

- keyboard navigation for nodes, relationships, filters, and Story Mode;
- visible focus indicators;
- screen-reader labels for nodes, domains, epistemic classes, and relations;
- sufficient text contrast;
- no meaning communicated by color alone;
- reduced-motion behavior;
- responsive layout;
- readable node details on mobile;
- non-WebGL fallback or no WebGL requirement for the canonical viewer.

## Non-Goals for V1

V1 should not attempt:

- live Runtime overlays;
- production Atlas synchronization;
- heavy 3D;
- game mechanics;
- speculative scientific claims;
- claims that Aetherion is deployed, inevitable, conscious, or complete;
- hand-authored duplicate graph data outside the Genesis manifest.

Those can follow after the core explorer contract is stable.

## Acceptance Criteria

Explorer v1 is ready when:

- it reads `manifests/tree.manifest.json` as its graph source;
- it does not hard-code authoritative graph meaning in JavaScript;
- domain-level semantic zoom works;
- node detail panels use manifest fields and source references;
- Epistemic Lens can be toggled and is visible in both overview and detail;
- primary lineage and cross-links are distinguishable;
- Tree-to-Atlas navigation slots exist without mixing datasets;
- Story Mode runs end-to-end and exits into free exploration;
- Aetherion is rendered as a federation canopy with new seeds beyond it;
- desktop and mobile visual checks pass;
- keyboard and reduced-motion checks pass;
- generated or bundled assets identify their source/provenance;
- tests or deterministic checks prove that the explorer is in sync with the
  canonical manifest.

## Implementation Order

1. Build the semantic zoom and navigation shell.
2. Add node details and relationship traversal.
3. Add the Epistemic Lens.
4. Add Atlas link slots using canonical IDs.
5. Add Story Mode.
6. Add visual polish and illustrations.
7. Add live Runtime overlays only after the static canonical experience is
   stable.

This order keeps the work grounded: understanding first, spectacle later.
