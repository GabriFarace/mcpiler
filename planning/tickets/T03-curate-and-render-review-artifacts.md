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

- [x] The deterministic operational/action floor is low for `GET`, medium for
      `POST` and `PATCH`, high for `DELETE`, and unknown for unsupported methods;
      it is described only as a likelihood-of-state-change floor.
- [x] Effective risk is the maximum of the deterministic floor and validated
      semantic risk-signal severity; semantic output cannot lower a floor or
      override a deterministic blocker.
- [x] The fixed policy applies the approved ordering: blockers and material
      uncertainty require review; unknown relevance or high/unknown effective
      risk requires review; sufficiently supported internal/infrastructure
      operations below high risk are hidden; sufficiently supported user-facing
      operations at low/medium risk are exposed; all unhandled states require
      review.
- [x] Material uncertainty follows the approved ordinal rule: low confidence on
      a decision-bearing field, an explicit uncertainty reason, unknown
      relevance, or a missing/invalid evidence reference requires review. No
      numeric or aggregate confidence score is introduced.
- [x] Endpoint-local unmatched, ambiguous, unsupported, truncated, analyzer
      failure, malformed output, and invalid-reference cases remain in the run
      as `requires-review`, are omitted from the proposed manifest, and do not
      block unrelated operations.
- [x] `semantic_ir.json` is the authoritative stable-order record of all eight
      operations and contains complete structural evidence, semantic status,
      relevance, risk, recommendation, policy reasons, evidence references, and
      deterministic run metadata without a volatile timestamp.
- [x] `manifest.json` contains exactly the expose recommendations and uses the
      approved MCP-like tool fields, with project-specific semantics and
      provenance confined to `_meta.mcpiler`.
- [x] `baseline_manifest.json` contains all eight operations, preserves useful
      OpenAPI names, descriptions, parameters, and schemas, and contains no
      semantic filtering or enrichment.
- [x] `risk_report.md` covers every operation and compares baseline exposure,
      evidence status, relevance, operational floor, semantic signals,
      effective risk, compiler recommendation, policy reasons, and evidence
      gaps.
- [x] The fake-backed golden run produces eight Semantic IR records, four
      proposed tools, eight baseline tools, exactly four expose, three
      requires-review, and one hide recommendation, with the operation outcomes
      specified by the approved MVP spec.
- [x] The proposed manifest is exactly the expose subset of Semantic IR; the
      baseline and report cover every Semantic IR operation; operations and
      tools use canonical stable ordering and deterministic names.
- [x] The CLI is a thin adapter over the compilation boundary, reports artifact
      locations and recommendation/degraded counts, exits zero after isolated
      endpoint failures when consistent review artifacts were emitted, and
      exits non-zero with a concise diagnostic for global compilation failure.
- [x] Artifact write/serialization failure is global and never presents a
      partial artifact set as a successful run; credentials, raw prompts, and
      raw model responses are never emitted.
- [x] The output documentation states that the artifacts are candidate MCP
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

`done`

## Implementation evidence

Implemented T03 as a deterministic completion and rendering layer over the
existing T01 `EndpointContext` and T02 `EndpointSemanticRecord` contracts. The
new compiler boundary applies fixed method risk floors, monotonic effective-risk
calculation, claim-level material uncertainty, and the six approved ordered
curation rule IDs. It retains the original structural context and semantic stage
result in each authoritative Semantic IR operation instead of introducing
parallel structural or semantic models.

All four renderers consume the same completed Semantic IR. The proposed manifest
contains expose recommendations only; the baseline mechanically contains every
OpenAPI operation without semantic enrichment; and the risk report contains one
canonical row per operation. JSON serialization is stable and rejects non-JSON
numeric values, tool naming has a deterministic method/path collision fallback,
and global invariant, serialization, and staged-write failures never return a
successful compilation result. The CLI only parses paths, injects the
deterministic fake analyzer, calls the compilation boundary, and formats the
result.

Deterministic CLI demonstration on 2026-08-20:

```text
uv run python -m mcpiler \
  --openapi fixtures/order_management/openapi.json \
  --source-root fixtures/order_management/backend \
  --output-dir /tmp/mcpiler-t03-demo.yntZ20/artifacts

status=degraded expose=4 hide=1 requires-review=3 degraded=1
semantic_ir.json=/tmp/mcpiler-t03-demo.yntZ20/artifacts/semantic_ir.json
manifest.json=/tmp/mcpiler-t03-demo.yntZ20/artifacts/manifest.json
baseline_manifest.json=/tmp/mcpiler-t03-demo.yntZ20/artifacts/baseline_manifest.json
risk_report.md=/tmp/mcpiler-t03-demo.yntZ20/artifacts/risk_report.md
```

The one degraded endpoint is the deliberately unmatched archive operation; the
command exits zero because it emitted a complete review artifact set.

Verification completed on 2026-08-20:

- `uv run python -m unittest discover -v` — 26 tests passed.
- `uv run python -m compileall -q mcpiler tests` — passed.
- Public-boundary import smoke for the compiler, Semantic IR, risk helpers, and
  CLI module — passed.
- Independent artifact verification — `operations=8 proposed=4 baseline=8`,
  with `expose=4`, `requires-review=3`, `hide=1`.
- Cross-artifact verification — proposed manifest equals the ordered expose
  subset, baseline covers every IR operation, report covers every IR operation,
  operation order is canonical, and repeated identical runs are byte-identical.
- Policy evidence — archive uses `CURATION_REVIEW_BLOCKER`; delete remains high
  from its HTTP-method floor; refund rises from medium to high through its
  validated financial signal; health remains low-risk and hides only because it
  is internal/infrastructure; the fake analyzer is called for exactly seven
  supported contexts.
- No linter or static type checker is configured. No dependency was added for
  T03, and no live analyzer or model call was made.
- The required two-axis review found no documented-standards violations or
  scope creep. Review findings for authoritative semantic-claim traversal,
  unique-operation-ID precedence, and explicit cross-artifact name/IR checks
  were fixed and covered by regression tests. The time-boxed single T03 module
  remains a documented judgement-call limitation rather than a correctness
  issue.

Known limitations are deliberate T03 scope boundaries: the CLI uses only the
fixed fake analyzer; manifests are project-defined MCP-like review artifacts,
not deployable MCP artifacts; input-schema construction remains bounded to the
approved fixture conventions; artifact installation stages all files before
publication but is not a transactional filesystem protocol; and there is no
configurable policy, score, capability discovery, live provider integration,
MCP runtime, authorization workflow, or broader static analysis.
