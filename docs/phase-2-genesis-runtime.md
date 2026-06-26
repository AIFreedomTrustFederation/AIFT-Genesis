# Phase 2 — Genesis Runtime

Phase 2 turns AIFT Genesis from a trust genome repository into an executable local-first runtime.

## Purpose

The Genesis Runtime gives every future interface the same constitutional engine:

- Termux CLI;
- desktop terminal;
- web application;
- Android app;
- local AI steward;
- Living Atlas;
- Federation services.

The CLI is the first interface. It proves the runtime contract before the web user experience is built.

## Runtime Commands

Current Phase 2 commands:

```bash
aift install
aift update
aift doctor

aift trust init "Trust Name"
aift trust validate [path]
aift trust list
aift trust open [path]

aift steward [path]
aift atlas [path]
aift sync [path]
aift mission [path]
aift economy [path]
```

## Runtime Contract

The runtime must preserve these rules:

1. The trust genome remains local-first.
2. Public federation is disabled until consented.
3. AI is assistant, not authority.
4. Material actions require human approval.
5. Generated trusts must validate before higher-level automation acts on them.
6. Website buttons must call the same runtime logic instead of inventing a separate path.

## Web UX Future

The future web interface should expose runtime actions as buttons and guided flows:

- Create Trust;
- Validate Trust;
- Generate Purpose with AI;
- Open AI Steward;
- Open Living Atlas;
- Create Mission;
- Open Economy Ledger;
- Connect Federation Link.

The website should not replace the constitutional runtime. It should make the runtime usable for people who should never need to touch Termux.

## Next Build Step

After this Phase 2 CLI layer is stable, the next milestone is a local web server command:

```bash
aift serve
```

That command should open a browser-based dashboard backed by the same trust validation, manifest, AI steward, atlas, mission, and economy contracts.
