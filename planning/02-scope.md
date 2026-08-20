# MVP Scope

## Time box

The MUST scope is a complete 2–3 hour vertical slice over one fixed synthetic
fixture. It proves the hypothesis; it is not a reusable static-analysis or
evaluation platform.

## Fixed demo fixture

The supplied OpenAPI document contains exactly these eight operations:

| Operation | Evidence case | Naive baseline | Expected compiler result |
| --- | --- | --- | --- |
| `GET /orders` | user-facing read | expose | expose |
| `GET /orders/{order_id}` | user-facing read | expose | expose |
| `POST /orders` | user-facing state change | expose | expose |
| `PATCH /orders/{order_id}/address` | handler-local precondition | expose | expose |
| `POST /orders/{order_id}/refund` | financial/external side effect | expose | requires-review |
| `DELETE /orders/{order_id}` | destructive action | expose | requires-review |
| `GET /internal/health` | internal/infrastructure | expose | hide |
| `POST /orders/{order_id}/archive` | OpenAPI-only unmatched operation | expose | requires-review |

## MUST — smallest credible implementation slice

- parse the fixed OpenAPI document and enumerate all eight operations
- inspect conventional literal FastAPI route decorators in the supplied source
- match routes by normalized HTTP method and literal path
- extract only route/OpenAPI metadata, schemas, handler identity/location,
  bounded handler-local source/docstring, and syntactically direct call names
- record unsupported or unmatched operations without guessing; do not inspect
  called service implementations
- build one bounded endpoint context per operation with a simple fixed source
  size limit and truncation marker
- define a provider-neutral `SemanticAnalyzer` boundary with one live analyzer
  and one deterministic fake used by normal tests
- accept only typed, validated endpoint-local semantic output containing
  purpose/description, visible or suggested preconditions and side effects,
  relevance, semantic risk signals, evidence references, and uncertainty
- keep relevance, effective risk, and curation recommendation independently
  inspectable
- apply the fixed operational/action risk floors and three-outcome curation
  policy; model findings cannot lower a floor or override a blocker
- map uncertainty, unsupported evidence, invalid semantic output, and
  endpoint-local analyzer failure to requires-review while continuing unrelated
  endpoints
- generate `semantic_ir.json` for all operations, an MCP-shaped `manifest.json`
  containing expose recommendations only, a naive baseline manifest containing
  all operations, and a simple `risk_report.md` comparison table
- provide one CLI path that runs the complete fixed fixture
- include a few deterministic tests covering route matching, the curation
  invariants, and malformed semantic output without calling a model
- run and briefly document one live-analyzer demo on the fixture; report useful
  and incorrect inferences qualitatively, with no scoring framework or pass
  threshold
- document that artifacts are candidate MCP interface decision aids requiring
  human review, not a deployable MCP server or automatic publication output
- send only bounded endpoint context to the live analyzer, treat all supplied
  text as untrusted data, provide no model tools/code execution, and validate
  output before policy use; serialize derived strings as data and do not add
  raw prompt/response logging

## STRETCH

- generalize beyond the fixed fixture or conventional literal route patterns
- resolve one statically obvious local callee and include its bounded source
- inspect tests or other repository files as semantic evidence
- endpoint-level capability hints, multi-tool capability discovery, or
  `capabilities.yaml`
- evaluation harnesses, per-field scoring, repeated trials, captured-run
  infrastructure, or downstream tool-selection evaluation
- prompt-injection/security test suites, logging/redaction infrastructure,
  provider-wide failure diagnostics, partial-output recovery, or a broad
  failure matrix
- richer human-readable reports or interactive comparison output
- additional semantic-analysis providers or cross-provider comparison
- source/OpenAPI revision-consistency checks
- generic manifest-backed MCP server and MCP Inspector demo
- broader deterministic test coverage beyond the core invariants

## EXCLUDED

- arbitrary backend frameworks/languages or GraphQL/RPC support
- dynamic route registration, runtime dependency resolution, or full static
  call/data-flow analysis
- transitive service and side-effect analysis beyond the optional one-hop
  stretch
- claims to recover arbitrary business rules hidden outside bounded endpoint
  evidence
- frontend workflow mining or API trace mining
- production authentication/RBAC, approval workflow, or automatic publication
- production MCP server generation, deployment, or Kubernetes
- configurable policy DSL, scoring engine, or deterministic semantic keyword
  heuristics
- vulnerability detection, authorization analysis, compliance classification,
  or security guarantees
- graph database, multi-agent runtime, production observability, or polished UI
