---
service: backend
summary: "Declarative clash detection engine with R-tree spatial indexing"
paths: [backend/app/engine/declarative.py, backend/app/engine/predicates.py, backend/app/engine/adapters.py, backend/app/engine/protocols.py]
flows: [clash_detect_and_resolve]
touches: []
external: []
last_verified_commit: TBD
---

# Clash Engine

## Purpose

Rule-driven clash detection where rules are stored in the database and evaluated against spatial entities using composable predicates. Uses R-tree for O(n log n) broad-phase filtering.

## Interface

- `RuleCompiler(site)` → compiles `ClashRule` DB rows into `CompiledRule` runtime objects
- `DeclarativeClashEngine(compiled_rules)` → evaluates a set of entities
- `engine.evaluate(entities)` → list of `ClashRuleResult`
- `PredicateRegistry.register(name, fn)` → extends available predicates

## State

None. Stateless computation. Rules are compiled per-evaluation; no caching between calls.

## Internals

- `CompiledRule` holds entity kind filters and a `Predicate` tree
- Predicates support AND, OR, NOT composition via `ComposedPredicate`
- Variables reference site settings: `$site.default_amber_distance_m`
- Message templates use `{{a.label}}` interpolation
- `SpatialEntity` protocol abstracts tokens, plants, workers, zones
- R-tree index built per-evaluation for broad-phase AABB overlap
- Narrow-phase runs predicate against overlapping pairs only

## Touches

None directly. Consumes rules from DB via `ClashRule` model; emits results to caller.

## Gotchas

- Rule compilation is synchronous and CPU-bound
- Large sites with many tokens may trigger expensive recalculations
- See [gotchas.md](../../../gotchas.md) for recomputation scope warning
