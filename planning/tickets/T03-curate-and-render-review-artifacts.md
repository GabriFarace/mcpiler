# T03: Curate and render the complete review artifact set

## Goal

Complete the offline compilation path by applying deterministic risk and
curation rules to structural evidence and validated semantic analysis, then
derive the four approved, internally consistent human-review artifacts from one
authoritative Semantic IR.

## User-visible outcome

An AI/platform engineer can run one command over the fixed fixture with the
deterministic fake analyzer and receive `semantic_ir.json`, an expose-only
`manifest.json`, an all-operation `baseline_manifest.json`, and
`risk_report.md`. The result visibly retains every backend operation, explains
each recommendation, and compares the four-tool candidate surface with the
eight-tool naive baseline.

## Dependencies

Blocked by **T02: Validate endpoint-local semantic analysis**.

## Acceptance criteria

- [ ] The deterministic operational/action floor is low for `GET`, medium for
      `POST` and `PATCH`, high for `DELETE`, and unknown for unsupported methods;
      it is described only as a likelihood-of-state-change floor.
- [ ] Effective risk is the maximum of the deterministic floor and validated
      semantic risk-signal severity; semantic output cannot lower a floor or
      override a deterministic blocker.
- [ ] The fixed policy applies the approved ordering: blockers and material
      uncertainty require review; unknown relevance or high/unknown effective
      risk requires review; sufficiently supported internal/infrastructure
      operations below high risk are hidden; sufficiently supported user-facing
      operations at low/medium risk are exposed; all unhandled states require
      review.
- [ ] Material uncertainty follows the approved ordinal rule: low confidence on
      a decision-bearing field, an explicit uncertainty reason, unknown
      relevance, or a missing/invalid evidence reference requires review. No
      numeric or aggregate confidence score is introduced.
- [ ] Endpoint-local unmatched, ambiguous, unsupported, truncated, analyzer
      failure, malformed output, and invalid-reference cases remain in the run
      as `requires-review`, are omitted from the proposed manifest, and do not
      block unrelated operations.
- [ ] `semantic_ir.json` is the authoritative stable-order record of all eight
      operations and contains complete structural evidence, semantic status,
      relevance, risk, recommendation, policy reasons, evidence references, and
      deterministic run metadata without a volatile timestamp.
- [ ] `manifest.json` contains exactly the expose recommendations and uses the
      approved MCP-like tool fields, with project-specific semantics and
      provenance confined to `_meta.mcpiler`.
- [ ] `baseline_manifest.json` contains all eight operations, preserves useful
      OpenAPI names, descriptions, parameters, and schemas, and contains no
      semantic filtering or enrichment.
- [ ] `risk_report.md` covers every operation and compares baseline exposure,
      evidence status, relevance, operational floor, semantic signals,
      effective risk, compiler recommendation, policy reasons, and evidence
      gaps.
- [ ] The fake-backed golden run produces eight Semantic IR records, four
      proposed tools, eight baseline tools, exactly four expose, three
      requires-review, and one hide recommendation, with the operation outcomes
      specified by the approved MVP spec.
- [ ] The proposed manifest is exactly the expose subset of Semantic IR; the
      baseline and report cover every Semantic IR operation; operations and
      tools use canonical stable ordering and deterministic names.
- [ ] The CLI is a thin adapter over the compilation boundary, reports artifact
      locations and recommendation/degraded counts, exits zero after isolated
      endpoint failures when consistent review artifacts were emitted, and
      exits non-zero with a concise diagnostic for global compilation failure.
- [ ] Artifact write/serialization failure is global and never presents a
      partial artifact set as a successful run; credentials, raw prompts, and
      raw model responses are never emitted.
- [ ] The output documentation states that the artifacts are candidate MCP
      interface decision aids requiring human review, not a deployable MCP
      server, publication approval, authorization result, or security guarantee.

## Public testing/evaluation seam to agree before coding

The public seam is the approved compilation boundary: a compile request supplies
the fixed OpenAPI path, source-root path, output directory, and injected
semantic analyzer, and returns a compilation summary while writing the four
artifacts. The CLI is tested only as a thin adapter over that same boundary.

The highest practical deterministic acceptance test invokes this boundary with
the fixed fixture and fake analyzer, then asserts the externally visible summary
and artifact contents. It covers exact route matching, the golden counts,
delete-floor preservation, refund risk escalation, health relevance/risk
separation, blocker precedence, malformed semantic output isolation, and all
cross-artifact consistency invariants. Tests use the standard library and do not
assert private parser, policy-helper, renderer, or prompt implementation details.

## Out of scope

- A live analyzer invocation or probabilistic semantic correctness threshold.
- `capabilities.yaml`, endpoint-level capability hints, or multi-tool capability
  discovery.
- A deployable MCP server, MCP SDK, MCP Inspector demo, publication workflow,
  authentication/RBAC, or policy enforcement.
- Configurable policy/scoring systems, deterministic semantic keyword
  heuristics, richer reports, or a polished UI.
- YAML OpenAPI ingestion, general backend support, callee inspection, or broader
  static analysis.
- Additional runtime or development dependencies beyond the approved
  constraints.

## Status

`blocked`

## Implementation evidence placeholder

Not started. On completion, record the implementation summary, CLI demonstration
command/result, deterministic test and import-smoke results, golden artifact
counts, artifact consistency evidence, and known limitations here.
