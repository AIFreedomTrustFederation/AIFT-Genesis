# AIFT-Genesis — The Federation Genome

**The genesis layer of the AI Freedom Trust Federation: trust identity, constitutional structure, civilization genome, schemas, templates, and the inheritance pattern from which sovereign local trust systems can be instantiated.**

| Federation metadata | Value |
| --- | --- |
| Layer | `genesis` |
| Role | trust identity, constitution, civilization genome |
| Workspace | `AIFT/AIFT-Genesis` |
| Control plane | AIFT workspace / AIFT-OS |
| Verification | Python unit tests, Tree/Atlas validators, and deterministic Tree artifact check (see Book III) |
| Operating standards | local-first, inspectable, sovereign by default, AI behind governed provider interfaces |

AIFT-Genesis is the constitutional and technical genome of the Federation. It defines what a trust seed must be able to inherit—identity, mission, governance, memory, economic relationship, AI boundaries, provenance, and federation connection—without requiring every person or project to live inside one centralized account system.

The shared covenant is carried in the [One Eternal Scroll of ALO'ha](https://aifreedomtrustfederation.github.io/AI-Freedom-Trust/docs/pdf/one-eternal-scroll-of-aloha.pdf) and operationalized in [SOP-ALOHA-001](https://github.com/AIFreedomTrustFederation/AI-Freedom-Trust/blob/main/SOP-ALOHA-001.md).

---

## Book I — The Seed and the Whole

Genesis begins from the holographic principle that the pattern of the Federation can be present locally without the Federation owning the local life that carries it. A person, family, business, ministry, cooperative, community, repository, or project can instantiate a trust seed that is sovereign enough to stand on its own and structured enough to participate in the wider system.

This is not merely account creation. It is inheritance. The seed receives a constitutional grammar: how identity is named, how authority is delegated, how missions are related to people and resources, how AI participation is bounded, how records carry provenance, how value connects to stewardship, and how a local system can join the Federation without dissolving into it.

### Illuminated passage — the Tree as genome and emergence graph

![Biozoe Tree of Life](https://raw.githubusercontent.com/AIFreedomTrustFederation/AI-Freedom-Trust/main/docs/images/aetherion/biozoe-tree-of-life.png)

The Tree of Life belongs naturally to Genesis because it expresses differentiation without fragmentation. Root, trunk, branch, leaf, and fruit remain distinct while carrying one living pattern. Genesis does the same for identity, governance, mission, economy, memory, and AI relation.

Genesis now carries the broader [Tree of Emergence](civilization/TREE_OF_EMERGENCE.md) as a canonical directed graph in [manifests/tree.manifest.json](manifests/tree.manifest.json), with the legacy Tree of Life parts preserved for compatibility. The graph distinguishes empirical science, active research, doctrine, philosophy, engineering, prototypes, architecture, and aspiration so the model can be visually expressive without overstating evidence. Generated review surfaces are available at [docs/generated/tree-of-emergence.svg](docs/generated/tree-of-emergence.svg) and [docs/generated/tree-of-emergence.html](docs/generated/tree-of-emergence.html).

Genesis also carries the public [Living Atlas](civilization/LIVING_ATLAS.md) contract in [manifests/living-atlas.manifest.json](manifests/living-atlas.manifest.json), validated against [schemas/Atlas.schema.json](schemas/Atlas.schema.json). The Atlas maps public, evidence-backed Federation entities to Tree node IDs through explicit typed mappings. It does not redefine the canonical Tree, and it does not publish private Green Zone or live Runtime state.

The next implementation phase is the [AIFT Tree Explorer v1](docs/tree-explorer-v1.md): semantic zoom, node details, an Epistemic Lens, Tree-to-Atlas navigation, and guided Story Mode while preserving the manifests as source of truth.

---

## Book II — What Genesis Owns and What It Hands Forward

AIFT-Genesis owns the **inheritance pattern**, not the operation of every system that inherits it. Its repository map reflects that role:

- `CONSTITUTION.md` establishes the constitutional foundation.
- `CHARTER.md` establishes repository authority and scope.
- `AGENTS.md` carries AI stewardship rules for this genome.
- `MANIFESTO.md` and `VISION.md` express public purpose and long-range direction.
- `philosophy/` carries ontology, epistemology, axiology, metaphysics, emergence, and the holographic principle.
- `science/` carries topology, torus, Fibonacci, fractal, information, and systems models used as design language.
- `civilization/` carries identity, trust, governance, Tree of Life, Tree of Emergence, Living Atlas, missions, and economy.
- `ai/` carries AI steward architecture, memory, reasoning, safety, alignment, and local-first AI principles.
- `manifests/`, `schemas/`, `templates/`, and `examples/` make the genome machine-readable and reusable, including the Tree of Emergence graph contract and the public Living Atlas mapping contract.
- `tools/` defines the generator and validation path through which inheritance can become executable.

The federation relationship is directional without being hierarchical in ownership. **AI-Freedom-Trust** supplies the broader doctrine and constitutional philosophy. **Genesis** turns that philosophy into a genome that can be instantiated. **AIFT-Forge** receives stable patterns and turns them into reusable technical structures. **AIFT-OS** discovers instantiated repositories and trust systems from evidence instead of assuming they conform. **BookSmith**, **VPS**, **Aetherion**, **TheMindofAll**, and future applications inherit only the parts of the genome that actually belong to their domain.

A trust seed should therefore be able to answer: Who am I? Who may act? What is my mission? What may AI do here? What evidence is authoritative? What remains private? How is value governed? How do I join or leave a federation relationship? Those are Genesis questions.

### Illuminated passage — governance as visible relation

![Governance Constellation](https://raw.githubusercontent.com/AIFreedomTrustFederation/AI-Freedom-Trust/main/docs/images/aetherion/governance-constellation.png)

The constellation prevents the genome from becoming centralized doctrine masquerading as sovereignty. Authority remains attributable to actual people, trusts, communities, and governed processes.

---

## Book III — SOP-ALOHA-001 in Genesis

The shared loop is:

```text
Receive → Inspect → Name → Propose → Consent → Act → Verify → Record → Return
```

In Genesis, **Receive** begins with a constitutional requirement, identity need, trust pattern, schema need, or new inheritance rule. **Inspect** means reading existing constitutional language and machine-readable definitions before creating another competing source of truth. **Name** determines whether the concept belongs in philosophy, civilization, AI policy, schema, manifest, template, example, or tool specification. **Propose** permits AI to structure and compare constitutional possibilities without silently redefining the covenant. **Consent** protects changes that alter rights, authority, identity, trust relationships, or inherited governance. **Act** updates the correct canonical layer. **Verify** checks internal consistency, schema validity, examples, and the ability of downstream systems to interpret the change. **Record** preserves the constitutional lineage through version control and manifests. **Return** gives downstream repositories a clear inheritance contract rather than a vague statement that they are “aligned.”

The federation metadata exposes status and pull alongside an executable integrity gate:

```bash
git status --short
git pull --ff-only
python3 -B -m unittest discover -s tests -v && \
python3 -B tools/validation/validate_tree.py && \
python3 -B tools/validation/validate_atlas.py && \
python3 -B tools/tree/render_tree.py --check
```

### Verification and maturity boundaries

The repository's [`aift.repo.json`](aift.repo.json) now runs the Python unit tests, Tree and Atlas validators, and deterministic Tree artifact check as its `verify` command. Run it from the repository root with Python 3 and Git installed (some tests inspect tracked files). `git status --short` remains a status command, not a verification gate. Passing these checks does not establish legal governance, cryptographic identity, external-link availability, or deployed federation services.

### Local Genesis web dashboard (development boundary)

The repository also includes a dependency-free [Node.js dashboard](apps/genesis-web/README.md) implemented in [`apps/genesis-web/server.mjs`](apps/genesis-web/server.mjs). With Node.js 18 or newer, start it from the repository root using `node apps/genesis-web/server.mjs`, then visit `http://127.0.0.1:8787`. It lists local trust folders, displays trust summaries and validation results, and exposes a trust-creation endpoint that invokes `bin/aift`. The AI Steward and Living Atlas buttons currently display contextual text; they are not running AI inference or a live Atlas service.

**Local-only security boundary:** The server binds to `127.0.0.1` by default but accepts `HOST` overrides. Its HTTP routes have no authentication or CSRF protection, and `POST /api/create` can create local trust directories. Do not expose it on a public interface, through an untrusted proxy, or to untrusted local callers; it is not a production-ready multi-user service. Trust-summary and validation routes reject paths escaping `AIFT_TRUSTS`, including sibling directories with a matching name prefix and symlinked trust directories pointing outside the root. This does not protect against symlinked files *within* a trust, concurrent filesystem changes, or untrusted local callers; the dashboard is not a hardened filesystem sandbox.

Run the separate dashboard smoke checks from the repository root:

```bash
node --check apps/genesis-web/server.mjs
node --test apps/genesis-web/tests/dashboard-smoke.test.mjs
```

The [Genesis Integrity workflow](.github/workflows/genesis-integrity.yml) runs the dashboard smoke suite in addition to Python manifest verification. The `aift.repo.json` `verify` command does **not** include Node.js tests. The smoke suite covers parsing, HTTP startup/trust listing, and safe display of trust names, but not trust creation, authentication, or deployment security.

The canonical [`manifests/tree.manifest.json`](manifests/tree.manifest.json) identifies itself as `status: "canonical-draft"` with `modelVersion: "0.1.0"`. Its epistemic classes explicitly distinguish empirical evidence, scientific consensus, active research, interpretation, philosophy, doctrine, engineering, prototypes, architecture, and aspirations. A generated Tree visualization is a projection of that graph, not independent evidence that every depicted relationship is scientifically established or implemented.

The linked [`AIFT Tree Explorer v1`](docs/tree-explorer-v1.md) is marked **next-phase roadmap**. Semantic zoom, Story Mode, and live Tree-to-Atlas exploration should not be described as shipped functionality without separate implementation evidence. Similarly, genome and trust-inheritance specifications do not alone establish a deployed identity provider, signature verifier, consent service, or federation network.

These automated checks cover defined contracts but do not replace semantic validation. A schema change must still be validated as a schema. A constitutional change must still be checked for contradiction. A template must still instantiate coherently. Genesis treats meaning as part of verification.

---

## Book IV — Instantiation Without Erasure

The Federation does not become sovereign by accumulating everyone into one database. It becomes sovereign by making local sovereignty interoperable. Genesis exists to make that possible.

A local trust may carry the same constitutional pattern while using different names, missions, assets, members, models, and technical services. A publishing trust can foreground authorship and provenance. A family trust can foreground care, consent, and inheritance. A project trust can foreground repositories, agents, and deployment permissions. The genome provides recognizable structure without dictating the life that fills it.

### The Return of the Word

In Genesis, the Word returns as inheritance that still remembers its source. Doctrine becomes constitution; constitution becomes schema; schema becomes a living trust seed; and the living trust returns its own identity to the Federation without surrendering it. The whole is present in the seed, and the seed remains itself.
