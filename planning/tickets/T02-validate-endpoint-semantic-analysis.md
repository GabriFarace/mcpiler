# T02: Validate endpoint-local semantic analysis

## Goal

Turn each supported bounded endpoint context into typed, evidence-linked
semantic interpretation through a provider-neutral analyzer boundary while
isolating malformed output and analyzer failures to the affected endpoint.

## User-visible outcome

An MCP interface compiler maintainer can substitute a deterministic fake at one
boundary and inspect validated purpose, agent description, visible or suggested
preconditions and side effects, relevance, semantic risk signals, uncertainty,
and provenance for each supported fixture operation. Invalid or failed analysis
is explicit and does not stop unrelated endpoints.

## Dependencies

Blocked by **T01: Extract bounded endpoint contexts from the fixed fixture**.

## Acceptance criteria

- [x] A provider-neutral `SemanticAnalyzer` accepts exactly one bounded endpoint
      context and returns either one typed semantic analysis or one typed,
      sanitized endpoint-local failure; compiler code does not depend on a
      provider-specific request or response shape.
- [x] The validated semantic output contains the approved purpose,
      agent-description, precondition, side-effect, relevance, semantic risk
      signal, uncertainty-reason, and analysis-provenance fields and rejects
      missing fields, extra fields, wrong types, and invalid enum values.
- [x] Every semantic claim carries text, ordinal claim-local confidence, and one
      or more evidence references that resolve within the same endpoint context.
- [x] Relevance remains an independent `user-facing`,
      `internal/infrastructure`, or `unknown` classification and is not treated
      as a safety or authorization decision.
- [x] Semantic risk signals use only the approved categories and medium/high
      severities and remain review signals rather than vulnerability,
      authorization, compliance, or security findings.
- [x] Invalid or missing evidence references, malformed structured output, and
      analyzer call failures produce a stable endpoint-local failed status with
      a concise sanitized reason; other supported endpoint analyses continue.
- [x] Unmatched, ambiguous, and unsupported contexts are retained with a skipped
      analysis status and are never sent to the analyzer; a uniquely matched but
      truncated context may be analyzed without removing its structural gap.
- [x] A deterministic fake analyzer supplies fixed typed results for the
      supported fixture operations and can intentionally produce malformed
      output, invalid evidence references, or endpoint-local failure for tests.
- [x] Source, docstrings, and OpenAPI descriptions are represented as untrusted
      delimited data at the analyzer boundary, with no raw prompt or response
      logging contract introduced.
- [x] This ticket produces validated semantic analysis and failure states only;
      it does not compute operational/action floors, effective risk, or a
      curation recommendation.

## Testing/evaluation seam

The public seam is `SemanticAnalyzer.analyze(endpoint context)`. Contract tests
inject the deterministic fake and assert accepted typed results or stable typed
failures using complete endpoint contexts from T01. A focused semantic-stage
test demonstrates that one malformed shape, invalid evidence reference, or
raised analyzer error affects only that operation while unrelated analyses
continue.

Tests assert the schema, evidence-link validity, endpoint isolation, and skipped
unsupported contexts. They do not assert prompt wording, provider SDK details,
Pydantic internals, or private orchestration helpers, and they never construct a
live analyzer or require credentials, network access, a paid call, or a local
model.

## Out-of-scope notes

- Deterministic operational/action risk floors, effective-risk calculation, or
  expose/hide/requires-review policy.
- The completed Semantic IR, whose contract also includes deterministic risk
  and recommendation data.
- Manifests, risk report, final artifact consistency, or the complete CLI.
- A live provider adapter or live model invocation.
- Numeric or aggregate confidence scores, deterministic semantic keyword
  heuristics, partial malformed-output recovery, or broad provider diagnostics.
- Additional analyzer providers or provider-comparison infrastructure.

## Status

`done`

## Implementation evidence

Implemented the provider-neutral semantic seam in `mcpiler.semantic`.
`SemanticAnalyzer.analyze(context: EndpointContext)` accepts exactly the immutable
T01 context and returns `SemanticSuccess` with strict `EndpointSemantics` or a
sanitized `SemanticFailure`. The endpoint stage returns one record retaining the
original context and a `succeeded`, `failed`, or `skipped` analysis state.

`EndpointSemantics` contains purpose, agent description, preconditions, side
effects, independent relevance, semantic risk signals, explicit uncertainty
reasons, and provenance. Evidence-linked claims carry only ordinal `high`,
`medium`, or `low` confidence. Strict validation rejects missing or extra fields,
wrong types, invalid enums, and blank uncertainty reasons. JSON-shaped provider
arrays are accepted and normalized to immutable tuples.

The shared `validate_endpoint_semantics(context, candidate)` path validates both
model-shaped data and exact membership of every evidence reference in that
context's `context.evidence` IDs. Invalid schema and evidence references become
the stable endpoint-local categories `invalid_semantic_output` and
`invalid_evidence_reference`; analyzer-returned failures and raised exceptions
become `analyzer_failed`. Failure messages are fixed and do not retain raw model
or exception data.

The stage skips T01 unmatched, ambiguous, and unsupported contexts without an
analyzer call; it analyzes uniquely matched truncated contexts while retaining
their original completeness gap. `FakeSemanticAnalyzer` provides fixed results
for the seven matched order-management endpoints and supports per-operation raw
malformed data, invalid evidence references, typed failures, and raised
exceptions. Raw fake data passes through the same shared validation seam
intended for a future live adapter.

Verification completed on 2026-08-20:

- `uv run python -m unittest tests.test_semantic_analysis -v` — 5 tests passed.
- `uv run python -m unittest discover -v` — 12 tests passed.
- `uv run python -m compileall -q mcpiler tests` — passed.
- No linter or static type checker is configured.
- Two-axis review against the pre-T02 `HEAD` found no standards issues or scope
  creep. One review finding for blank uncertainty reasons was fixed and
  re-reviewed.

Known limitations are deliberate T02 boundaries: no live provider adapter,
credentials, transport, retry/timeout diagnostics, prompt construction, raw
prompt/response logging, semantic IR completion, risk-floor/effective-risk
calculation, curation policy, artifacts, or CLI behavior. Endpoint-local evidence
IDs are validated only in the supplied context namespace; T02 does not create a
parallel global evidence-ID scheme.
