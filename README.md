# SimOops Wiki

A structured knowledge base for the [SimOops](https://github.com/Chiark-Collective/simoops) codebase, maintained specifically for LLM agents and AI coding assistants.

## What this is

This repository is **not** end-user documentation. It is a machine-navigable, human-auditable map of the SimOops system: a construction site safety platform with a FastAPI backend and Angular frontend.

The goal is simple: when an AI agent needs to work on the SimOops codebase, it should read this wiki first instead of ingesting tens of thousands of lines of source code. Every page is concise, cross-referenced, and bound to a specific git commit in the source repository.

## Why this approach

This wiki is inspired by [Andrej Karpathy's observation](https://gist.github.com/karpathy/4c41a78f9a8a6a47b79e6f6e844a41f1) that LLMs work best with compressed, structured knowledge about a codebase rather than raw file dumps. A 200-line module summary with cross-references beats 10,000 lines of source code when the agent needs to reason about architecture.

SimOops is a **vibe-coded** project: large portions were written iteratively with AI assistance, which means the codebase moves fast and traditional documentation rots immediately. This wiki exists precisely because vibe-coded systems need machine-maintainable maps.

The principles:

- **Precision over completeness**: Each page focuses on a single cohesive unit (a module, a flow, an API channel) with strict length caps.
- **Cross-references as navigation**: The graph is designed to be traversable without a search tool. Every link is bidirectionally verified.
- **Binding contracts**: Every page carries a `last_verified_commit` hash. Out-of-date pages are worse than missing pages, so we track drift explicitly.
- **Codebase-agnostic schema**: The structure (modules, flows, APIs, contracts) works for any system, not just SimOops.

## Structure

```
wiki/
  AGENTS.md              # Schema, style rules, lint contract
  index.md               # Top-level orientation
  topology.md            # Runtime boundaries and data flow
  log.md                 # Ingest history
  glossary.md            # Cross-service terms
  gotchas.md             # Cross-service footguns

  services/
    backend/
      index.md           # Routing table for all backend pages
      api/               # HTTP routes, WebSocket messages
      modules/           # Backend subsystems (auth, clash, planning, etc.)
      flows/             # End-to-end sequences within the backend
      analyses/          # Exploratory investigations

  flows/                 # Cross-service sequences
  contracts/             # Inter-service data contracts
  external/              # Third-party systems (Keycloak, PostGIS, Redis, etc.)
  infra/                 # Data stores, network, compute
  ops/                   # Runbooks keyed on symptoms
  build.md               # CI/CD
```

### Page types

| Type | Question it answers | Example |
|---|---|---|
| **Module** | What is this? | `entity_service.md` — CRUD, snapshots, optimistic concurrency |
| **Flow** | What happens when X? | `entity_creation.md` — trigger → validation → persistence → broadcast |
| **API** | What can occur? | `http.md` — all HTTP route prefixes by domain |
| **Contract** | What is the data shape? | (cross-service schemas) |
| **External** | How do we use this third-party system? | `keycloak/index.md` |
| **Infra** | What are the runtime resources? | `data-stores.md` |
| **Runbook** | What do I do when I see this symptom? | (ops procedures) |

## For agents

1. Start at [`index.md`](index.md) for orientation.
2. Read [`topology.md`](topology.md) if your task crosses service boundaries.
3. Use [`glossary.md`](glossary.md) for domain terms and [`gotchas.md`](gotchas.md) for footguns.
4. Follow cross-references. Every link should round-trip.

## Lifecycle phases

The wiki moves through three phases on every update cycle:

### 1. Ingest

Trace from entry points (API channels) outward one cohesive unit at a time. Update all touched pages and cross-cutting files:
- Module / flow / API pages
- Service `index.md` routing table
- `glossary.md`, `gotchas.md`
- `log.md` history
- `manifest.json` commit hashes

Record the source commit hash in `last_verified_commit` for every page touched.

### 2. Analyse

When an agent asks a question that requires investigation beyond the existing pages, file the findings into `analyses/` with `status: open`. These are explorations, not contracts. Over time, stable findings get promoted into modules or flows; stale analyses get marked `superseded`.

### 3. Refresh & Lint

```bash
# Detect drift: which pages are stale vs. current source HEAD?
python3 scripts/refresh.py

# Enforce consistency: cross-references, lengths, banned phrases
python3 scripts/lint.py
```

Refresh is planning-only — it reports, it does not auto-update. Lint is the gate. Run both before committing.

## Source

- **Wiki**: `https://github.com/Chiark-Collective/simoops-wiki`
- **Application**: `https://github.com/Chiark-Collective/simoops`

## License

Same as the SimOops application repository.
