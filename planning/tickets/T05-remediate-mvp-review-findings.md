# T05: Remediate MVP review findings

## Goal

Resolve every P0 and P1 finding from the seven-commit MVP review without
broadening the approved fixture, analyzer, or artifact scope.

## User-visible outcome

The fixed-fixture compiler rejects invalid or wrong-fixture global input before
semantic analysis, keeps source inspection within the selected source root,
prevents ambient LangSmith tracing, gives the provider only provider-owned
semantic fields, and emits an authoritative Semantic IR with explicit relevance
and semantic risk signals for every operation. The documented live configuration
is directly runnable.

## Dependencies

Depends on completed tickets T01-T04 and the approved MVP specification.

## Acceptance criteria

- [x] The live analyzer cannot inherit environment/global LangSmith tracing;
      bounded context and provider responses are not exported through callbacks.
- [x] Python source candidates that resolve outside `source_root`, including
      symlinked files, fail as an unreadable source-root input before analysis.
- [x] Provider structured output excludes adapter-owned analysis provenance;
      the adapter adds provenance before the shared application validation seam.
- [x] `.env.example` has usable timeout/retry defaults and tracing disabled, and
      the root README documents the fixed fake and live commands plus the
      human-review-only artifact boundary.
- [x] Non-standard JSON constants such as `NaN` and `Infinity` fail as
      `openapi_invalid_json` before any analyzer call.
- [x] A successful compile requires exactly the approved eight canonical
      operation keys; missing, extra, or empty operation sets fail globally
      before semantic analysis.
- [x] Every Semantic IR operation has explicit independent relevance and risk
      signals, using `unknown` and an empty signal collection when analysis is
      unavailable.
- [x] The deterministic golden fixture still produces four expose, three
      requires-review, and one hide recommendation with four internally
      consistent artifacts.

## Testing/evaluation seam

Use the already-approved public seams:

- `compile_interface(CompileRequest(...))` for global input classification,
  analyzer isolation from rejected inputs, and emitted Semantic IR contracts;
- `SemanticAnalyzer.analyze(endpoint_context)` for provider-owned output,
  adapter-owned provenance, and tracing isolation.

Tests use deterministic boundary doubles only for the external model SDK and do
not make network, credential, paid, or local-model calls.

## Out-of-scope notes

- New providers, dependencies, policy rules, route-analysis generalization, or
  artifact types.
- P2/P3 findings, including all-failure analyzer provenance and dynamic-route
  reason refinement.
- Refactoring unrelated working code.

## Status

`done`

## Implementation evidence

Completed on 2026-08-20.

The live adapter now disables LangSmith tracing for the invocation, detaches an
inherited LangChain tracer context, supplies an explicit empty callback config,
and restores the caller's context afterward. Provider structured output uses the
application-owned `EndpointSemanticOutput` claims schema; adapter provenance is
added before the unchanged `validate_endpoint_semantics` seam.

Structural analysis rejects symlinked source roots and Python files before
reading handler evidence. Strict JSON parsing rejects non-standard constants as
`openapi_invalid_json`, and the compilation boundary rejects any operation set
other than the approved eight before calling the analyzer.

Semantic IR schema `mcpiler.semantic-ir.v2` adds one explicit relevance record
and one semantic-risk-signal collection to every operation. Skipped and failed
analyses receive `unknown` relevance with no confidence/evidence references and
an empty signal collection. The T04 captured live artifacts remain truthful
historical `v1` evidence and are marked as such rather than regenerated without
a live model run.

Documentation now includes runnable fixed fake/live commands, usable non-secret
LM Studio defaults, the human-review-only artifact boundary, and verification
commands. T05 introduced no new package; the final audit later promoted the
already-resolved `langchain-core` and `langsmith` packages to direct
dependencies because `mcpiler/live.py` imports their public APIs.

Verification:

- `uv run python -m unittest discover -v` — 34 deterministic tests passed.
- `.venv/bin/python -m compileall -q mcpiler tests` — passed.
- `git diff --check` — passed.
- Deterministic CLI fixture run — exit zero with `expose=4`, `hide=1`,
  `requires-review=3`, and `degraded=1`.
- Generated IR verification — schema `mcpiler.semantic-ir.v2`, eight operations,
  eight explicit relevance records, and eight risk signal collections.

No linter or static type checker is configured. The reviewed P2 items remain
out of scope: all-failure analyzer provenance and dynamic-route reason
refinement.
