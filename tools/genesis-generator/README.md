# Genesis Generator

The Genesis Generator is the executable layer that turns the AIFT Genesis trust genome into a local trust workspace.

The current command is implemented in:

```text
bin/aift
```

## Primary Command

```bash
aift trust init "My Trust Name"
```

The command copies `templates/trust-seed/` into a new trust folder under `~/AIFT-Trusts/`, replaces generator variables, validates the generated files, initializes Git, and creates the first local commit.

## Generator Variables

The generator replaces only:

```text
{{TRUST_NAME}}
{{TRUST_SLUG}}
{{TRUST_PURPOSE}}
```

The constitutional text is preserved. A generated trust should not receive empty form fields, TODO language, or weak placeholder scaffolding.

## Validation

The generator checks:

- generated JSON files parse correctly;
- required generator variables were replaced;
- weak placeholder language is not present;
- the generated trust can initialize a local Git history.

## Design Rule

The generator should instantiate a living trust genome, not a fake shell. The generated trust must be usable immediately as a local-first constitutional workspace.
