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

- [x] The supplied fixed fixture contains the eight approved OpenAPI operations
      and the FastAPI handlers needed to demonstrate the approved evidence
      cases.
- [x] A readable, structurally usable OpenAPI JSON document is enumerated in
      canonical uppercase-method and normalized-path order while preserving the
      approved operation metadata, parameters, request body schema, and response
      schemas.
- [x] Python source inspection is syntax-only: target modules are never imported
      or executed, and called service implementations are not inspected.
- [x] Conventional literal FastAPI method/path decorators are normalized and
      matched exactly, producing seven unique handler matches and retaining
      `POST /orders/{order_id}/archive` as unmatched without guessing.
- [x] Dynamic paths, ambiguity, unsupported route forms, and missing matches are
      represented as endpoint-local unsupported evidence with stable reasons.
- [x] Every unique handler match records identity, relative location and line
      range, signature, docstring, bounded handler-local source, and
      syntactically direct call names.
- [x] One fixed character limit and prefix-preserving truncation rule is chosen
      against the fixture, documented, and surfaced through an explicit
      truncation marker and evidence-completeness gap.
- [x] Each endpoint context contains stable endpoint-local evidence IDs with
      OpenAPI JSON Pointer or source location provenance, plus independently
      computed evidence-completeness metadata.
- [x] Missing, unreadable, invalid JSON, structurally unusable OpenAPI input, an
      unreadable source root, or inability to parse the fixed source fixture is
      reported as a global compilation input failure rather than partial trusted
      evidence.

## Testing/evaluation seam

Approved on 2026-08-20:

`extract_endpoint_contexts(openapi_path: Path, source_root: Path) -> StructuralAnalysis`

This deterministic structural seam accepts the OpenAPI path and source-root
path and returns immutable, canonically ordered endpoint contexts consumed by
later compilation. It exposes the approved OpenAPI operation, source-match,
handler evidence, endpoint-local evidence/provenance, and evidence-completeness
contracts. Global input failures use stable public categories; unmatched,
ambiguous, unsupported, and truncated evidence remains endpoint-local.

The fixed handler-source limit is 4,000 characters. Handler source and extracted
docstrings use deterministic prefix-preserving truncation and record original
length, truncation state, provenance, and an evidence-completeness gap when
truncated.

Tests assert this returned contract and observable failure categories, not
parser classes, AST helper calls, private function names, or incidental
formatting. The seam is an implementation milestone under the approved
compilation boundary, not a new product command or artifact.

The deterministic test must demonstrate the eight-operation enumeration, seven
exact matches, unmatched archive retention, stable evidence/provenance, and
bounded source behavior using only the standard library test stack.

## Out-of-scope notes

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

`done`

## Implementation evidence

Implemented the approved deterministic
`extract_endpoint_contexts(openapi_path, source_root) -> StructuralAnalysis`
seam with immutable structural records, stable global input-failure categories,
canonical operation ordering, exact literal route matching, bounded handler
evidence, endpoint-local evidence/provenance, and deterministic completeness
gaps. Extraction uses only JSON parsing, Python AST parsing, and raw source
segments; analyzed target modules are never imported or executed.

The fixed synthetic fixture contains all eight approved OpenAPI operations and
exactly seven conventional literal FastAPI handlers. The archive operation is
OpenAPI-only and remains unmatched. The selected handler-source and docstring
limit is **4,000 characters**, applied as deterministic prefix-preserving
truncation with original character count and explicit completeness gaps.

Verification completed on 2026-08-20:

- `uv run python -m unittest discover -v` — 7 tests passed.
- `uv run python -m compileall -q mcpiler tests` — passed.
- Public-seam fixture verification — `operations=8 matched=7 unmatched=1
  limit=4000`.
- No linter or static type checker is configured. No dependency was added for
  T01.

Known limitations are deliberate T01 scope boundaries: JSON OpenAPI only;
operation-level parameters and inline object schemas; top-level sync/async
handlers with attribute-style method decorators and a first positional literal
path; no dynamic paths, composed router prefixes, runtime route registration,
import resolution, callee inspection, or control/data-flow analysis. Direct
call names are syntactic `Name`/dotted `Attribute` expressions only and do not
claim runtime execution or resolved behavior.
