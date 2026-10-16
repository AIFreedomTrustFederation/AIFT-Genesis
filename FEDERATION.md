# Federation Role: AIFT-Genesis

## Layer

`genesis`

## Role

trust identity, constitution, civilization genome

## Operating Principle

This repository is part of the AI Freedom Trust Federation operating system. It remains sovereign in its own repo while participating in the shared federation control plane.

## Control Plane

Top-level workspace:

```bash
/data/data/com.termux/files/home/AIFT
```

Primary command:

```bash
/data/data/com.termux/files/home/AIFT/aift-os.sh
```

## Standard Commands

Status:

```bash
git status --short
```

Pull:

```bash
git pull --ff-only
```

Verify (run from the repository root with Python 3 and Git installed):

```bash
python3 -B -m unittest discover -s tests -v && \
python3 -B tools/validation/validate_tree.py && \
python3 -B tools/validation/validate_atlas.py && \
python3 -B tools/tree/render_tree.py --check
```

This checks unit contracts, Tree and Atlas manifests, and deterministic generated Tree artifacts. It does not prove governance semantics, cryptographic identity, external-link health, or deployment readiness.

## Federation Metadata

This repo declares its federation role in:

```bash
aift.repo.json
```

The workspace-level federation manifest is generated at:

```bash
/data/data/com.termux/files/home/AIFT/manifests/workspace.json
```
