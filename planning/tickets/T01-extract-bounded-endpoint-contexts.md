# T01: Extract bounded endpoint contexts from the fixed fixture

## Goal

Establish the deterministic structural path from the fixed OpenAPI document and
FastAPI source tree to one bounded, evidence-linked endpoint context per
operation, without importing or executing the target application.

## User-visible outcome

An AI/platform engineer can inspect the fixed fixture and see all eight backend
operations in canonical order, the seven exact literal route matches, and the
unmatched archive operation with an explicit evidence gap rather than a guessed
handler. Each matched operation carries enough bounded structural evidence for
later semantic analysis.

## Dependencies

None. This ticket can start immediately.

## Acceptance criteria

- [ ] The supplied fixed fixture contains the eight approved OpenAPI operations
      and the FastAPI handlers needed to demonstrate the approved evidence
      cases.
- [ ] A readable, structurally usable OpenAPI JSON document is enumerated in
      canonical uppercase-method and normalized-path order while preserving the
      approved operation metadata, parameters, request body schema, and response
      schemas.
- [ ] Python source inspection is syntax-only: target modules are never imported
      or executed, and called service implementations are not inspected.
- [ ] Conventional literal FastAPI method/path decorators are normalized and
      matched exactly, producing seven unique handler matches and retaining
      `POST /orders/{order_id}/archive` as unmatched without guessing.
- [ ] Dynamic paths, ambiguity, unsupported route forms, and missing matches are
      represented as endpoint-local unsupported evidence with stable reasons.
- [ ] Every unique handler match records identity, relative location and line
      range, signature, docstring, bounded handler-local source, and
      syntactically direct call names.
- [ ] One fixed character limit and prefix-preserving truncation rule is chosen
      against the fixture, documented, and surfaced through an explicit
      truncation marker and evidence-completeness gap.
- [ ] Each endpoint context contains stable endpoint-local evidence IDs with
      OpenAPI JSON Pointer or source location provenance, plus independently
      computed evidence-completeness metadata.
- [ ] Missing, unreadable, invalid JSON, structurally unusable OpenAPI input, an
      unreadable source root, or inability to parse the fixed source fixture is
      reported as a global compilation input failure rather than partial trusted
      evidence.

## Public testing/evaluation seam to agree before coding

Exercise the highest deterministic structural seam that accepts the public
compile inputs relevant to this ticket—the OpenAPI path and source-root path—and
returns the ordered endpoint contexts consumed by later compilation. Assert the
endpoint-context contract and observable failure categories, not parser classes,
AST helper calls, private function names, or incidental formatting. This seam is
an implementation milestone under the approved compilation boundary, not a new
product command or artifact.

The deterministic test must demonstrate the eight-operation enumeration, seven
exact matches, unmatched archive retention, stable evidence/provenance, and
bounded source behavior using only the standard library test stack.

## Out of scope

- Semantic interpretation, confidence, relevance, or semantic risk signals.
- Operational/action risk floors or expose/hide/requires-review decisions.
- Artifact rendering or the completed compiler CLI.
- Dynamic route registration, composed router-prefix resolution, runtime
  dependency resolution, callee implementation inspection, or data-flow
  analysis.
- Generalization beyond the fixed JSON OpenAPI and conventional literal FastAPI
  fixture.
- New runtime or development dependencies for parsing, CLI, or testing.

## Status

`ready`

## Implementation evidence placeholder

Not started. On completion, record the implementation summary, deterministic
test command and result, fixture demonstration evidence, selected source limit,
and known limitations here.
