# AGENTS.md

Schema, style rules, lint contract, and workflows for this wiki.

This document is codebase-agnostic. It describes universal concepts. Concrete examples from this wiki's codebase appear under *"Example from this wiki:"*.

---

## Philosophy

- Ingest from code only. Do not trust `CLAUDE.md`, `AGENTS.md`, or `docs/` inside the source repo.
- Every page is a binding contract. Out-of-date pages are worse than missing pages.
- Three orthogonal questions govern the structure:
  1. What is this? → `modules/`
  2. What happens when X? → `flows/`
  3. What can occur? → `api/`, `contracts/`
- Cross-references are the primary navigation mechanism. The graph must be traversable without a search tool.

---

## Directory Layout

```
wiki/
  AGENTS.md              # this file
  index.md               # top-level orientation
  topology.md            # every service in one table
  log.md                 # ingest history + manifest reference
  glossary.md            # cross-service terms
  gotchas.md             # cross-service footguns

  services/
    <service>/
      index.md           # routing table + frontmatter
      api/               # one page per channel (http, grpc, kafka, graphql, websocket, cli, lib, etc.)
      modules/           # one page per cohesive code unit
      flows/             # service-local sequences
      analyses/          # explorations filed from queries

  flows/                 # cross-service sequences only
  contracts/             # one page per inter-service contract (schema, producer, consumers)
  external/              # one page per third-party system
  infra/                 # network, stores, queues, compute, secrets, observability
  ops/                   # runbooks keyed on symptoms
  build.md               # cross-cutting CI/CD
```

---

## Page Types

### Module

A cohesive unit of code: a package, a subsystem, a library, a component tree.

```md
---
service: <name>
summary: <≤15 words>
paths: [<source paths>]
flows: [<flow references>]
touches: [<infra references>]
external: [<external references>]
last_verified_commit: <hash>
---

## Purpose
1–3 sentences

## Interface
Public surface area: functions, methods, endpoints, events, exported types.
One line per symbol.

## State
Runtime state this module maintains: caches, registries, connection pools,
computed indexes, session stores, derived view models.
Include invariants and lifecycle rules.
Omit this section entirely if the module is purely stateless.

## Internals
Bulleted, one fact per line.

## Touches
| resource | how | why |

## Gotchas
Bulleted. Link to shared gotchas.md when applicable.
```

**State section rules:**
- Mandatory if the module maintains any runtime state (anything not the primary persistent database).
- Omit entirely if the module is stateless (e.g., a pure function library, a compiler, a formatter).
- Invariant format: `condition ⟂ consequence` or `condition → guarantee`.

**Symbol citations:** Use `path/to/file.py::symbol_name`. Line numbers are banned.

### Flow

A trigger causes a sequence of steps with side effects.

```md
---
trigger: { channel: <type>, ref: "<identifier>" }
services: [<names>]
contracts: [<names>]
external: [<names>]
---

## Trigger
One line.

## Steps
Numbered sequence across modules/services.

## Side effects
Writes, emits, external calls, state mutations.

## Failure modes
Bulleted: what breaks, how it's detected, how it's handled.
```

### API Channel

The surface area of a service.

```md
---
service: <name>
channel: <type>  # http, grpc, kafka, graphql, websocket, function, cli, etc.
---

| identifier | direction | audience | auth | flow | notes |
```

### Contract

An inter-service data contract.

```md
---
producer: <service>
consumers: [<services>]
schema: <path or reference>
breaking_changes: [<history>]
---

## Purpose
One line.

## Schema
Embed or cite.

## Consumers
| service | uses | flow |
```

### External System

A third-party dependency.

```md
---
direction: in | out | both
consumed_by: [<services>]
auth: <mechanism>
---

## Use
One line per consumer.

## Endpoints / Resources
Table.

## Failure handling
Timeout, retry, fallback.

## Quirks
Bulleted.
```

### Infra

A runtime infrastructure resource.

```md
---
used_by: [<services>]
owner_team: <name>
---

## Spec
| parameter | value |

## Access
Bulleted.

## Quirks
Bulleted.
```

### Runbook

An ops procedure keyed on a symptom.

```md
---
symptom: "exact symptom string"
related_flows: [<names>]
related_infra: [<names>]
related_external: [<names>]
---

## Detect
Bulleted indicators, log snippets, metrics.

## Diagnose
Numbered steps.

## Mitigate
Numbered steps.

## Root-cause notes
Bulleted, links to analyses/.
```

### Analysis

An exploratory or investigatory page filed from a query.

```md
---
status: open | stale | merged | superseded
---

## Question

## Findings

## Links
```

---

## Style Rules

### Symbols (define once)

- `→` leads to
- `⇒` produces
- `⟂` blocks / depends on / mutually exclusive with
- `!` warning

### Banned universally

Introductory prose, transitional phrases, restated headers, recaps, generic best-practice statements, marketing language, TODOs, redundant qualifications.

### Length caps

| Page type | Max lines |
|---|---|
| Module | 150 | 250 |
| Flow | 100 | 200 |
| API channel | 80 | 150 |
| Glossary entry | 5 | 10 |

### Bidirectional cross-references

Every link must be round-trippable:
- Module `flows:` → every listed flow must reference this module
- Contract `consumers:` → every consumer must list this contract
- External `consumed_by:` → every listed service must reference this external
- Infra `used_by:` → every listed service must reference this infra

---

## Workflows

### Ingest

1. Start at entry points (API channel rows)
2. Trace outward one cohesive unit at a time
3. Update every touched page and cross-cutting file:
   - [ ] Module page(s) — new or modified
   - [ ] Flow page(s) — if trigger/sequence changed
   - [ ] API channel page(s) — if surface area changed
   - [ ] Service `index.md` routing table
   - [ ] `glossary.md` — new domain terms
   - [ ] `gotchas.md` — new footguns or invariants
   - [ ] `log.md` history table + next targets **(! lint.py does NOT catch missing log updates)**
   - [ ] `manifest.json` — new pages, commit hashes
4. Typical touch: 5–12 pages
5. Record commit hash in `last_verified_commit` for every source touch

### Query

1. Read `index.md` (and `topology.md` if cross-service)
2. Read frontmatter of candidates
3. Read targeted sections
4. Target: resolve under ~5k tokens
5. File answers into `analyses/` with `status: open`

### Lint

Enforced by `scripts/lint.py`:
- Broken cross-references
- Stale `last_verified_commit` (compared to manifest)
- Orphan pages (no inbound links)
- Missing flow links
- Unresolved frontmatter round-trips
- Banned phrases
- Page length caps

---

## Subagent Orchestration

When delegating multi-step ingest or exploration tasks to parallel subagents:

### Progress Monitoring

1. **Heartbeat files** — Each subagent writes a progress file (e.g. `/tmp/flow-<name>.progress`) every 60 seconds containing a timestamp and current step.
2. **Orchestrator polling** — The orchestrator checks all heartbeat files every 90 seconds.
3. **Intervention threshold** — If a heartbeat file has not been updated in 120 seconds:
   - Read any partial output the subagent wrote to its assigned scratch directory.
   - If meaningful progress exists (>50% complete, or key sections drafted), send a lightweight "ping" task (30s timeout) to verify responsiveness.
   - If the ping fails or no meaningful progress exists, treat the subagent as stuck.
4. **Re-delegation** — Kill the stuck task and spawn a fresh subagent:
   - Pass along all partial markdown already produced.
   - Narrow the scope to the remaining work (e.g. skip already-completed Trigger/Steps sections; focus on Failure modes).
   - If zero progress was made, restart with a simpler decomposition (e.g. trace only HTTP call sequence, defer WebSocket dedup logic).
5. **Timeout guard** — Assign a hard timeout per flow (e.g. 8 minutes). If exceeded, the task errors automatically and the orchestrator applies the re-delegation rules above.

---

## Frontend Mapping (for multi-tier systems)

When this wiki covers a frontend tier, apply the same page types without forking the schema:

| Schema concept | Frontend mapping |
|---|---|
| Module | Feature module, component tree, store, service |
| State | Reactive state: stores, subjects, signals, derived selectors |
| Flow | User action → handler → API → store update → re-render |
| API | Outbound HTTP / WebSocket / GraphQL calls |

Use `service: ui` (or `frontend`, `client`, etc.) in frontmatter. The `State` section captures runtime reactivity, not persistent DB state.

---

## Example from this wiki:

*This wiki covers the SimOops system: a construction site safety platform with a FastAPI backend and Angular frontend. The source repo is at `/Users/williamcheung/Development/simoops`.*
