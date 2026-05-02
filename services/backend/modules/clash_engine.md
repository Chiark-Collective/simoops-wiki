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

Rule-driven clash detection where rules stored in the database are evaluated
against spatial entities using composable predicates. Uses R-tree for
O(log n) broad-phase filtering and O(n) narrow-phase predicate evaluation.

## Interface

- `declarative.py::RuleCompiler(site)` → compiles `ClashRule` rows into `CompiledRule`
- `declarative.py::compile_rules(rules, site)` → list of `CompiledRule`, skipping disabled/failed
- `declarative.py::DeclarativeClashEngine(compiled_rules)` → evaluator
- `declarative.py::engine.evaluate(entities, max_results)` → list of `ClashRuleResult`
- `declarative.py::detect_clashes(rules, entities, site, max_results)` → convenience entry point
- `declarative.py::MessageRenderer.render(template, entity_a, entity_b, rule_name, distance)` → str
- `declarative.py::VariableResolver.resolve(value)` → substitutes `$site.*` variables
- `predicates.py::PredicateRegistry.register(name, fn)` → extends available predicates
- `predicates.py::PredicateRegistry.get(name)` → lookup registered predicate
- `predicates.py::PredicateRegistry.create(name, *args)` → factory for parameterized predicates
- `adapters.py::WorkerEntity(token, building_lookup)` → `SpatialEntity` for workers
- `adapters.py::PlantEntity(plant)` → `SpatialEntity` for plants
- `adapters.py::InactivePlantEntity(plant_read)` → `SpatialEntity` for inactive cranes
- `adapters.py::GeometadataFeatureEntity(feature, layer)` → `SpatialEntity` for features
- `protocols.py::SpatialEntity` → protocol for engine consumables

## State

None. Stateless computation. Rules compiled per-evaluation; no caching between calls.

## Internals

- `CompiledRule` holds entity kind/type filters and a `Predicate` tree
- Predicates support AND, OR, NOT via `ComposedPredicate.all_of`, `any_of`, `not_of`
- `PREDICATE_COLLECTIONS` = `(_AllOfPredicate, _AnyOfPredicate)` for tree traversal
- Variables: `$site.default_amber_distance_m`, `$site.default_red_distance_m`, `$site.name`
- Message templates use `{{a.label}}`, `{{b.type}}`, `{{distance}}`, `{{rule.name}}`
- `SpatialIndex` builds rtree per-evaluation with buffer = max rule distance
- `query_nearby` expands bounds by buffer for symmetric within_distance capture
- Duplicate pair suppression uses `entity_id` (not `logical_id`) so frontend can match
- Same-filter rules track `evaluated_pairs_this_rule` to avoid (a,b)/(b,a) double work
- `WorkerEntity._compute_overhead_exposure` checks `building.top_concrete_level` vs worker level
- `PlantEntity.geometry` delegates to `plant_geometry.get_drop_zone_from_plant`
- `GeometadataFeatureEntity` buffers road LineStrings by half width using scale factor

## Touches

None directly. Consumes rules from DB via `ClashRule` model; emits results to caller.

## Gotchas

- Rule compilation is synchronous and CPU-bound
- Large sites with many tokens may trigger expensive recalculations
- `geometry is None` → entity is skipped entirely (never falsely clashed)
- `_NotPredicate` excluded from `PREDICATE_COLLECTIONS` by design; negation breaks spatial pre-filtering
- See [gotchas.md](../../../gotchas.md) for recomputation scope warning
