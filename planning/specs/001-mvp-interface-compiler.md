# Specification — MCP Interface Compiler MVP

- Triage: `ready-for-agent`
- Scope: MUST slice only
- Timebox: 2–3 hours
- Decision basis: project brief, problem framing, MVP scope, and ADRs 0001–0003

## Problem Statement

An AI/platform engineer with a FastAPI source tree and its OpenAPI document
needs a smaller, semantically clearer candidate agent interface than a
mechanical one-operation-to-one-tool conversion. OpenAPI alone does not reliably
distinguish user-facing operations from infrastructure endpoints or make
handler-local preconditions and side effects obvious. A useful first draft must
remain inspectable and conservative: it must retain every backend endpoint,
show where each conclusion came from, isolate uncertainty and failures, and
leave publication to a human reviewer.

## Solution

Provide one offline MCP interface compiler command for the fixed synthetic
order-management fixture. It combines deterministic OpenAPI extraction and
bounded, non-executing FastAPI source inspection into an endpoint context,
passes each supported context through a provider-neutral semantic analyzer,
validates the typed result, and applies a deterministic curation policy.

One successful run emits an authoritative semantic IR artifact for all eight
operations, an expose-only proposed manifest, an all-operations naive baseline
manifest, and a risk report comparing the two. These artifacts are candidate
interface decision aids. They do not constitute an MCP server, publication
approval, authorization analysis, or a security guarantee.

## User Stories

1. As an AI/platform engineer, I want to compile a fixed FastAPI source tree and
   matching OpenAPI document in one command, so that I can inspect a candidate
   MCP tool surface without executing the target application.
2. As an interface reviewer, I want every backend endpoint retained with an
   expose, hide, or requires-review recommendation and evidence-linked reasons,
   so that curation is transparent rather than destructive.
3. As an interface safety reviewer, I want relevance, operational/action risk, semantic
   risk signals, uncertainty, and recommendation represented separately, so
   that a model inference cannot masquerade as a deterministic security fact.
4. As an evaluator, I want the proposed manifest compared with a fair naive
   baseline on the fixed eight-operation fixture, so that the product
   hypothesis is immediately inspectable.
5. As an MCP interface compiler maintainer, I want deterministic compiler tests
   to replace the live analyzer with a fake at one boundary, so that normal
   tests are reproducible and require no paid, networked, or local model call.

## Golden Path — Deterministic Acceptance

The golden path is the reproducible compiler acceptance path. It uses the fixed
fixture and deterministic fake analyzer; it does not make the live model's
probabilistic predictions part of software correctness.

1. The test supplies the fixed OpenAPI JSON document, the fixed local FastAPI
   source root, an output directory, and the deterministic fake analyzer.
2. The compiler validates global inputs and deterministically enumerates the
   eight OpenAPI operations in canonical method/path order.
3. Without importing or executing target code, it inspects Python syntax for
   literal FastAPI method/path decorators and matches them to OpenAPI operations
   by normalized HTTP method and literal path.
4. It creates one bounded endpoint context per operation. Matched operations
   include handler-local evidence; the unmatched archive operation records its
   evidence gap and is never guessed.
5. The fake analyzer receives one supported endpoint context at a time and
   returns the fixed, typed semantic results for that operation.
6. The compiler validates each semantic result and its evidence references,
   computes risk and recommendation using the fixed deterministic policy, and
   renders all four artifacts.
7. As a deterministic acceptance criterion, the resulting comparison exposes
   four operations, requires review for the refund, delete, and unmatched
   archive operations, and hides only the internal health operation:

| Operation | Recommendation | Governing reason |
| --- | --- | --- |
| `GET /orders` | expose | supported user-facing read |
| `GET /orders/{order_id}` | expose | supported user-facing read |
| `POST /orders` | expose | supported user-facing state change below high risk |
| `PATCH /orders/{order_id}/address` | expose | supported user-facing update with evidence-linked precondition |
| `POST /orders/{order_id}/refund` | requires-review | high financial/external-side-effect signal |
| `DELETE /orders/{order_id}` | requires-review | deterministic high operational/action risk floor |
| `GET /internal/health` | hide | supported internal/infrastructure operation below high risk |
| `POST /orders/{order_id}/archive` | requires-review | unmatched source evidence blocker |

## Live Analyzer Evaluation Path

The live demonstration uses the same fixed OpenAPI/source fixture and the same
endpoint-context construction, output validation, risk calculation, curation
policy, and artifact renderers as the deterministic golden path. The only
substitution is the live implementation behind the semantic analyzer boundary.
Source-derived text remains delimited as untrusted data, and the analyzer has no
repository, tool, browser, or code-execution access.

The live run's actual semantic predictions, recommendations, and resulting
counts are captured in its semantic IR and risk report and discussed as
evaluation evidence. They are not required to reproduce the fake analyzer's
four expose / three requires-review / one hide outcome. A structurally valid,
evidence-linked result that is semantically wrong is a model-quality finding,
not a compiler or software-test failure. Invalid structured output still
follows the normal endpoint-local failure path and produces
`requires-review`.

## Implementation Decisions

### Public boundaries

The MVP has three public logical boundaries. Exact package names and dependency
choices are intentionally deferred.

1. **Compilation boundary.** A compile request contains an OpenAPI JSON file
   path, a readable local Python source-root path, an output-directory path, and
   a semantic analyzer. It returns a compilation summary and writes the four
   specified artifacts. The CLI is a thin adapter over this same boundary.
2. **Semantic analyzer boundary.** `analyze(endpoint context)` accepts exactly
   one bounded endpoint context and returns one typed semantic analysis or a
   typed endpoint-local failure. The compiler core knows no provider-specific
   request or response shape. The MVP has exactly one live implementation and
   one deterministic fake.
3. **Artifact boundary.** Rendering accepts the completed semantic IR and emits
   stable JSON/Markdown. The semantic IR, not either manifest or the report, is
   authoritative.

No framework, SDK, schema library, or test runner is selected by this spec.
The implementation should use the existing Python project and add a dependency
only when the selected live provider or a demonstrated contract requires it.

### Input contract

| Input | Required contract | Failure classification |
| --- | --- | --- |
| OpenAPI document | Readable JSON OpenAPI document containing the fixed eight operations. Each operation contributes method, path, operation ID when present, summary/description, parameters, request body schema, and response schemas when present. | Missing, unreadable, invalid JSON, or structurally unusable input is a compilation failure. |
| Source root | Readable local directory containing the fixed Python fixture. Analysis is syntax-only; target modules are never imported or executed. | Missing/unreadable root or inability to parse the fixture is a compilation failure. |
| Supported route | A literal FastAPI method decorator and literal full route path whose normalized method/path exactly matches an OpenAPI operation. Normalization uppercases the method, ensures a leading slash, and removes a trailing slash except for `/`. | Dynamic paths, composed router prefixes, ambiguity, and no match are endpoint-local unsupported evidence, never guessed matches. |
| Handler evidence | Handler identity and relative location, signature, docstring, bounded raw handler source, and syntactically direct call names. Callee implementations are not inspected. | Truncation is deterministic, explicitly recorded, and blocks automatic expose/hide. |
| Analyzer configuration | Enough configuration to initialize the single selected live analyzer; secrets come from runtime configuration and are never written to artifacts. | Missing or invalid initialization configuration is a compilation failure. |

The handler-source limit is one fixed implementation constant, measured in
characters with a deterministic prefix-preserving truncation rule. Its exact
value must be documented before implementation evidence is recorded. Every
semantic IR artifact records the applied limit.

### Endpoint context contract

Each endpoint context contains:

| Field | Meaning |
| --- | --- |
| `operation_key` | Canonical uppercase method plus normalized literal path. |
| `openapi_operation` | Deterministically copied operation ID, descriptions, parameters, request-body schema, and response schemas. |
| `source_match` | `matched`, `unmatched`, `ambiguous`, or `unsupported`, with deterministic reasons. |
| `handler` | Present only for a unique match; identity, relative file path, line range, signature, bounded source/docstring, direct call names, and truncation marker. |
| `evidence` | Stable endpoint-local evidence records addressable by ID. |
| `evidence_completeness` | Deterministic status and gaps; separate from all model confidence. |

An evidence record has an endpoint-local `id`, an origin of `openapi` or
`source`, a kind, a value/excerpt, and provenance. OpenAPI provenance uses a
JSON Pointer. Source provenance uses a relative path and line range. Evidence
IDs are stable for identical inputs and are the only references a semantic
claim may cite.

Unmatched, ambiguous, and unsupported contexts remain in the semantic IR but
are not sent to the analyzer because semantic output cannot remove their
deterministic blocker. A uniquely matched but truncated context may be analyzed
for reviewer value, but truncation still requires review.

### Semantic analyzer output contract

Only a validated structured result is accepted. It contains:

| Field | Shape and constraint |
| --- | --- |
| `purpose` | One semantic claim describing the user outcome. |
| `agent_description` | One semantic claim suitable for a candidate tool description. |
| `preconditions` | Zero or more semantic claims limited to conditions visible or suggested in supplied evidence. |
| `side_effects` | Zero or more semantic claims limited to effects visible or suggested in supplied evidence. |
| `relevance` | `user-facing`, `internal/infrastructure`, or `unknown`, with confidence and evidence references. |
| `semantic_risk_signals` | Zero or more signals categorized as `financial`, `destructive`, `sensitive-data`, `privileged`, `external-side-effect`, or `other`, each with `medium` or `high` severity, confidence, explanation, and evidence references. |
| `uncertainty_reasons` | Explicit limitations or ambiguities in the supplied evidence. |
| `analysis_provenance` | Analyzer implementation ID, provider/model ID when live, and semantic-output schema/prompt version; never raw prompt or response text. |

Every semantic claim contains text, one or more valid evidence references, and
model-reported confidence of `high`, `medium`, or `low`. Confidence is ordinal,
untrusted, and claim-local; the compiler does not create a numeric or aggregate
confidence score. Evidence completeness is computed independently. Any low
confidence on a decision-bearing field, any explicit uncertainty reason, an
unknown relevance, or any missing/invalid evidence reference is material
uncertainty and deterministically requires review.

Source, docstrings, and OpenAPI descriptions are serialized as delimited data,
not instructions. The analyzer receives no tools and cannot browse or execute
the repository. Provider-native free-form output, extra fields, wrong types,
invalid enum values, and invalid evidence references fail validation.

### Core semantic IR shape

The root semantic IR contains `schema_version`, deterministic run metadata,
the configured handler-source limit, analyzer and policy version identifiers,
and an ordered `operations` collection. It contains no volatile timestamp that
would prevent reproducible comparison.

Each operation record contains:

| Group | Required content |
| --- | --- |
| Identity | Canonical operation key, method, normalized path, and operation ID when supplied. |
| Structural evidence | The full endpoint context, including every evidence record and deterministic completeness/gap metadata. |
| Semantic analysis | Validated semantic output, or an explicit `skipped`/`failed` status and endpoint-local failure reason. |
| Relevance | The validated independent classification, confidence, and evidence references, or `unknown` when analysis is unavailable. |
| Risk | Deterministic operational/action floor, semantic risk signals, effective risk, and reasons. |
| Recommendation | `expose`, `hide`, or `requires-review`, plus stable policy rule IDs, human-readable reasons, and supporting evidence references. |

This record is the sole source for both manifests and the risk report. Every
OpenAPI operation appears exactly once, including unsupported and failed
operations.

### Risk and curation policy

The fixed fixture needs only these operational/action floors: `GET` is `low`,
`POST` and `PATCH` are `medium`, and `DELETE` is `high`. Any method outside the
supported set has `unknown` risk and requires review. This floor says only how
likely an operation is to change state; it is not a confidentiality,
authorization, business-impact, or overall security classification.

Effective risk is the maximum of the deterministic floor and validated
semantic risk-signal severity. Semantic analysis can raise but never lower the
floor. The deterministic curation policy is applied in this order:

1. Unmatched, ambiguous, unsupported, truncated, failed, malformed, or
   materially uncertain evidence/analysis produces `requires-review`.
2. `unknown` relevance or `high`/`unknown` effective risk produces
   `requires-review`.
3. A sufficiently supported `internal/infrastructure` operation below high
   risk produces `hide`.
4. A sufficiently supported `user-facing` operation with low or medium
   effective risk produces `expose`.
5. Any unhandled state produces `requires-review`.

No policy outcome publishes, authorizes, or enforces an operation.

### Output contracts

| Artifact | Contract |
| --- | --- |
| `semantic_ir.json` | Authoritative, stable-order record of all eight operations and the complete structural, semantic, provenance, confidence, risk, failure, and recommendation data described above. |
| `manifest.json` | Project-defined candidate interface containing only `expose` operations. Each tool is structurally MCP-like as specified below, but the artifact is not a deployable standard MCP artifact. |
| `baseline_manifest.json` | Fair mechanical one-operation-to-one-tool output containing all eight operations. Its tools use the same MCP-like structural fields while preserving useful OpenAPI names, descriptions, parameters, and schemas, but it performs no semantic filtering or enrichment. |
| `risk_report.md` | Human-review table with every operation, source/evidence status, baseline exposure, relevance, operational floor, semantic signals, effective risk, compiler recommendation, and evidence-linked reasons. The fake-backed golden path visibly summarizes four expose, three requires-review, and one hide; a live run reports its actual outcomes. |

The proposed manifest document contains one ordered `tools` array. Each tool
uses MCP-like standard fields where applicable:

- `name`: a deterministic unique tool name;
- `description`: the validated enriched agent description;
- `inputSchema`: the OpenAPI-derived JSON Schema for tool arguments;
- `outputSchema`: included only when a useful response schema is available;
- `annotations`: included only when an MCP-like annotation is appropriate and
  supported by deterministic evidence or validated policy output; annotations
  remain non-authoritative hints;
- `_meta.mcpiler`: the sole home for project-specific compiler metadata,
  including source operation identity, preconditions, possible side effects,
  evidence references, relevance/risk/recommendation context, and analysis
  provenance.

No project-specific semantic or provenance field is added alongside the
MCP-like top-level tool fields. Baseline tools use the same standard fields and
may use `_meta.mcpiler` only for deterministic source operation identity; they
contain no semantic-analysis metadata.

Tool naming uses a unique OpenAPI operation ID when available and otherwise a
deterministic method/path-derived fallback. Naming collisions use the same
deterministic fallback rather than semantic invention. Operations and tools
are sorted by canonical operation key. Derived strings are serialized as data;
raw prompts, raw model responses, and credentials are never logged or emitted.

On success, the CLI exits zero and reports artifact locations plus counts by
recommendation. A run with isolated endpoint failures still exits zero when it
successfully emits internally consistent review artifacts, and it reports the
degraded endpoint count. A compilation failure exits non-zero with a concise
diagnostic and does not present a partial artifact set as successful.

### Failure behavior and invariants

- Invalid global input, an unreadable source root, impossible analyzer
  initialization, or artifact serialization/write failure is a compilation
  failure.
- Unmatched/ambiguous routes, truncation, analyzer call failures, malformed
  semantic output, invalid evidence references, and material uncertainty are
  endpoint-local. The operation remains in semantic IR and risk report as
  `requires-review`, is omitted from the proposed manifest, and does not block
  unrelated operations.
- A provider error is represented by a stable public category and concise
  sanitized message; rich provider diagnostics and raw payload capture are not
  required.
- The proposed manifest is always exactly the subset of semantic IR operations
  recommended `expose`; the baseline manifest always contains every OpenAPI
  operation; the risk report always contains every semantic IR operation.
- A high deterministic floor or blocker cannot be reduced by semantic output.
- A semantic claim with no valid evidence reference cannot influence policy.

## Testing Decisions

### Deterministic testing seam

Use one highest practical seam: invoke the compilation boundary with the fixed
OpenAPI/source fixture and deterministic fake analyzer, then assert the
externally visible compilation summary and artifact contents. Tests should
assert contracts and invariants, not parser classes, prompt wording, renderer
helpers, private function calls, or provider SDK details.

The small deterministic suite covers:

1. With the fixed fake analyzer, the golden fixture must produce eight semantic
   IR records, a four-tool proposed manifest, an eight-tool baseline, and a
   report with exactly four expose, three requires-review, and one hide result.
2. Exact normalized literal route matching associates the seven supported
   handlers and retains the unmatched archive operation without guessing.
3. The policy preserves the delete risk floor, allows the refund signal to
   raise effective risk, separates health relevance from risk, and never lets
   model output override a blocker.
4. A fake result with malformed shape or an invalid evidence reference makes
   only that endpoint `requires-review`; unrelated endpoints and all artifact
   consistency invariants remain intact.

Normal tests never instantiate the live analyzer and require no credential,
network access, paid call, or local model. There is no existing test suite or
prior testing convention in the repository; implementation must not select a
test dependency merely by preference.

### LLM evaluation seam

Use the provider-neutral semantic analyzer boundary for one documented live
run over the fixed fixture. The live implementation must pass through the same
validation, deterministic curation, and artifact pipeline as the fake. Review
the emitted IR and report qualitatively and record the actual recommendations,
counts, useful inferences, and incorrect inferences, especially:

- whether the address handler's visible precondition is described and linked
  only to supplied handler evidence;
- whether the refund handler's financial/external side effect is identified
  with evidence and raises review rather than being presented as a security
  finding;
- whether the health endpoint is classified as internal/infrastructure;
- whether unsupported or absent semantics are expressed as uncertainty rather
  than invented facts.

This live demonstration has no required recommendation distribution, numeric
score, repeated-trial requirement, or semantic pass threshold. A valid but
semantically incorrect prediction is recorded as evaluation evidence rather
than hidden, used to weaken an expectation, or reported as a software failure.
Software correctness covers the shared validation/curation pipeline and its
failure invariants; deterministic fake-backed tests remain its authority.

## Out of Scope

- General support beyond the fixed fixture, JSON OpenAPI input, conventional
  literal FastAPI decorators, and exact normalized route matching.
- YAML ingestion, dynamic route registration, composed router-prefix
  resolution, runtime dependency resolution, arbitrary imports/execution, or
  full call/data-flow analysis.
- Callee implementation inspection, transitive side-effect recovery, frontend
  or trace mining, arbitrary business-rule recovery, or multi-tool capability
  discovery.
- A deployable MCP server, MCP runtime execution, MCP SDK dependency, MCP
  Inspector demonstration, automatic publication, production approval
  workflow, authentication/RBAC, or policy enforcement.
- Configurable policy/scoring systems, deterministic semantic keyword
  heuristics, graph databases, orchestration systems, multi-agent runtimes,
  deployment infrastructure, observability platforms, or polished UI.
- Vulnerability detection, authorization analysis, compliance classification,
  or security guarantees.
- Multiple live providers, provider comparison, repeated trials, per-field
  scoring, captured-run infrastructure, downstream tool-selection evaluation,
  or a dedicated prompt-injection suite.
- One-hop callee inspection, richer reports, source/OpenAPI revision checks,
  partial model-output recovery, and broad failure-matrix coverage; these remain
  stretch work and are not prerequisites for the MVP.

## Further Notes

### Deferred implementation selections (non-blocking for ticketing)

- The live provider/model, its SDK or transport, and credential convention need
  explicit human approval before a dependency is added. They do not change the
  provider-neutral analyzer contract.
- The fixed handler-source character limit must be chosen against the supplied
  fixture and documented. The contract already fixes prefix-preserving
  truncation and conservative failure behavior.
- Exact CLI spelling, Python module layout, validation mechanism, and test
  runner are implementation choices subordinate to the public contracts; no
  current repository convention resolves them.

There is no unresolved product, public-contract, or acceptance decision that
blocks implementation ticket generation. Tickets may sequence the selections
above and preserve the required human approval before adding a significant
dependency.

### Timebox guardrail

Nothing in the MUST behavior above intentionally expands beyond the approved
2–3 hour vertical slice. Robust generalization, one-hop source resolution,
evaluation harnesses, security test infrastructure, additional providers, and
deployable MCP generation exceed that timebox and must not be pulled into the
implementation ticket.
