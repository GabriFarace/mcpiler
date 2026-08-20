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

- [ ] A provider-neutral `SemanticAnalyzer` accepts exactly one bounded endpoint
      context and returns either one typed semantic analysis or one typed,
      sanitized endpoint-local failure; compiler code does not depend on a
      provider-specific request or response shape.
- [ ] The validated semantic output contains the approved purpose,
      agent-description, precondition, side-effect, relevance, semantic risk
      signal, uncertainty-reason, and analysis-provenance fields and rejects
      missing fields, extra fields, wrong types, and invalid enum values.
- [ ] Every semantic claim carries text, ordinal claim-local confidence, and one
      or more evidence references that resolve within the same endpoint context.
- [ ] Relevance remains an independent `user-facing`,
      `internal/infrastructure`, or `unknown` classification and is not treated
      as a safety or authorization decision.
- [ ] Semantic risk signals use only the approved categories and medium/high
      severities and remain review signals rather than vulnerability,
      authorization, compliance, or security findings.
- [ ] Invalid or missing evidence references, malformed structured output, and
      analyzer call failures produce a stable endpoint-local failed status with
      a concise sanitized reason; other supported endpoint analyses continue.
- [ ] Unmatched, ambiguous, and unsupported contexts are retained with a skipped
      analysis status and are never sent to the analyzer; a uniquely matched but
      truncated context may be analyzed without removing its structural gap.
- [ ] A deterministic fake analyzer supplies fixed typed results for the
      supported fixture operations and can intentionally produce malformed
      output, invalid evidence references, or endpoint-local failure for tests.
- [ ] Source, docstrings, and OpenAPI descriptions are represented as untrusted
      delimited data at the analyzer boundary, with no raw prompt or response
      logging contract introduced.
- [ ] This ticket produces validated semantic analysis and failure states only;
      it does not compute operational/action floors, effective risk, or a
      curation recommendation.

## Public testing/evaluation seam to agree before coding

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

## Out of scope

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

`blocked`

## Implementation evidence placeholder

Not started. On completion, record the analyzer contract summary, deterministic
fake behavior, validation and failure-isolation test commands/results, and known
limitations here.
