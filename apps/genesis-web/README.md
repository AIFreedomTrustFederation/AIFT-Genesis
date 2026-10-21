# Genesis Web Dashboard

This is the first local-first web interface for AIFT Genesis.

It is intentionally minimal: no external dependencies, no database, no cloud service, and no remote federation requirement. It uses Node's built-in HTTP server and reads local trust folders from `AIFT_TRUSTS`.

## Purpose

The dashboard proves that the Termux CLI can become a button-driven UX without changing the constitutional runtime model.

Current buttons and endpoints support:

- listing generated trusts;
- opening a trust summary;
- validating a trust;
- creating a trust through the existing `bin/aift` generator;
- showing AI Steward context;
- showing Living Atlas context.

## Run Locally

From the repository root:

```bash
node apps/genesis-web/server.mjs
```

Then open:

```text
http://127.0.0.1:8787
```

Requires Node.js 18 or newer. On Termux, install Node first if needed:

```bash
pkg install -y nodejs
```

## Verify

From the repository root, run the dashboard's dependency-free smoke tests:

```bash
node --check apps/genesis-web/server.mjs
node --test apps/genesis-web/tests/dashboard-smoke.test.mjs
```

These checks cover JavaScript syntax, HTTP startup and trust listing, and safe rendering of trust names. They do not exercise trust creation, all CLI commands, or deployed federation services. The Genesis Integrity workflow also runs this dashboard smoke test; the `aift.repo.json` Python verification command remains focused on Tree and Atlas contracts.

## Environment

```bash
AIFT_HOME=~/AIFT-Genesis
AIFT_TRUSTS=~/AIFT-Trusts
AIFT_PORT=8787
```

## Design Rule

The web dashboard must call the same trust runtime contracts as the CLI. Website buttons should not become a separate source of truth.

The constitutional documents remain the authority. The dashboard is only an interface over the trust genome, validation engine, AI steward context, Living Atlas context, mission records, economy ledger, and future Federation Link.

## Next Step

The next runtime command should be:

```bash
aift serve
```

That command will launch this dashboard directly from the CLI.
