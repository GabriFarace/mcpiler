# Project Brief — MCP Interface Compiler

## Problem

Existing REST APIs are designed primarily for programmatic clients and
frontend applications, not autonomous LLM agents.

Mechanical OpenAPI-to-MCP conversion can expose too many operations,
including infrastructure-oriented, internal, or dangerous endpoints,
while failing to communicate business-level semantics such as purpose,
preconditions, side effects, and user-level outcomes.

## Product hypothesis

For conventional FastAPI routes, deterministic structural extraction followed
by endpoint-local LLM interpretation can produce a smaller, more semantically
useful candidate MCP interface for human review than mechanical OpenAPI-to-tool
conversion.

The claim is limited to evidence present in OpenAPI, route metadata, schemas,
bounded handler-local source/docstrings, and syntactically direct call names.
The MVP does not claim to recover arbitrary business rules, preconditions, or
side effects hidden in transitive service implementations.

## Target user

An AI/platform engineer who has access to an existing FastAPI source tree
and matching OpenAPI document, and needs a reviewable first draft of an
MCP tool interface without manually designing every candidate tool.

## MVP input

- FastAPI OpenAPI document
- local Python source tree

The MVP supports conventional routes declared with literal FastAPI method and
path decorators. It matches OpenAPI operations to source by normalized HTTP
method and literal path. Ambiguous, dynamic, or unmatched routes are reported
as unsupported rather than guessed.

For a matched operation, live semantic analysis may receive normalized facts
plus bounded raw handler source and docstring. A fixed documented source-size
limit and deterministic truncation rule apply; truncation is recorded as part
of evidence completeness.

The compiler records syntactically direct call names but does not inspect the
called implementations. One-hop resolution of a statically obvious local
callee is STRETCH.

## MVP output

- semantic_ir.json
- manifest.json
- risk_report.md

`semantic_ir.json` is the authoritative full analysis of every operation.
`manifest.json` is a project-defined candidate MCP interface containing only
expose recommendations; it is human-reviewable and MCP-shaped, not a standard
deployable MCP artifact.
`risk_report.md` is the human-review view over every operation, especially hide
and requires-review cases. The fair baseline manifest mechanically contains
every OpenAPI operation.

These are decision-support artifacts. A human reviews them before any tool is
published; the MVP does not claim that generated output is safe to publish
automatically.

## Core pipeline

OpenAPI + Python source
→ deterministic structural extraction
→ bounded endpoint context
→ endpoint-local LLM semantic analysis
→ semantic IR
→ deterministic curation policy
→ human-reviewable candidate interface artifacts

The compiler core depends on a provider-neutral `SemanticAnalyzer` interface.
The MVP supplies exactly one live model-backed implementation for end-to-end
demonstration and one deterministic fake/fixture implementation for normal
tests and deterministic compiler evaluation. Normal tests do not call an
external or local model.

Source, docstrings, and OpenAPI descriptions are quoted untrusted data, not
instructions. The live analyzer cannot browse the repository, use tools, or
execute code. Only typed structured output is accepted; validation failure
produces requires-review. The README states what source-derived content is sent
to the configured model.

## Responsibility of the LLM

The semantic model may infer user purpose, an agent-facing description,
handler-evidenced preconditions and possible side effects, relevance, semantic
risk signals, and uncertainty. Every claim is typed, validated, and linked to
evidence from the bounded endpoint context.

The deterministic curation layer preserves these invariants:
- relevance, effective risk, and recommendation remain separate
- HTTP method establishes an operational/action risk floor only
- semantic findings may elevate risk but never lower a floor or override a
  blocker
- unsupported, malformed, or uncertain analysis requires review
- high-risk user-facing operations require review rather than being hidden

Semantic risk signals use the compact financial, destructive, sensitive-data,
privileged, external-side-effect, or other categories with medium/high
severity. They are review signals, not security findings or guarantees.

## Failure model

Endpoint-local failures are isolated: the affected operation remains in the
semantic IR and review output as requires-review, is omitted from the proposed
manifest, and does not block unrelated operations. Invalid global input fails
the run. Rich provider diagnostics, partial-output recovery, and failure-report
infrastructure are not required for the core slice.

## Initial constraints

- FastAPI only
- REST/OpenAPI only
- static Python/source analysis
- bounded handler source/docstring and syntactically direct call names only
- no arbitrary target-code execution
- no dynamic route resolution, runtime dependency resolution, or transitive
  call-graph analysis
- no graph database
- no frontend analysis
- no traffic mining
- no production authorization system
- no automatic publication
- no configurable policy language or scoring engine
- no multiple live semantic-analysis providers in the MVP
- no multi-agent runtime

## Evaluation hypothesis

Compared with a naive one-endpoint-one-tool transformation, semantic
compilation should:
- expose fewer irrelevant/internal operations
- identify risky operations more effectively
- provide richer agent-facing descriptions

The MVP evaluates direct curation and semantic quality. Improved downstream
agent tool selection is a potential benefit, not a claim validated by the MVP.

The fair baseline exposes every OpenAPI operation and preserves its useful
OpenAPI metadata. The core evaluation is a single visible comparison on the
fixed demo: baseline-exposed operations versus compiler recommendations and
their reasons. A scoring framework, repeated model trials, per-field metrics,
and captured-run infrastructure are STRETCH.

## Demo shape

Use one fixed synthetic order-management fixture with eight OpenAPI operations:

| Operation | Intended case | Expected recommendation |
| --- | --- | --- |
| `GET /orders` | user-facing read | expose |
| `GET /orders/{order_id}` | user-facing read | expose |
| `POST /orders` | user-facing state change | expose |
| `PATCH /orders/{order_id}/address` | handler-local precondition | expose |
| `POST /orders/{order_id}/refund` | financial/external side effect | requires-review |
| `DELETE /orders/{order_id}` | destructive action | requires-review |
| `GET /internal/health` | internal/infrastructure | hide |
| `POST /orders/{order_id}/archive` | OpenAPI-only unmatched operation | requires-review |

The naive baseline exposes all eight. The compiler should propose four,
recommend review for three, and hide one, with evidence-linked reasons. The
refund and address handlers contain enough handler-local evidence to test
semantic enrichment without inspecting service implementations.

## Success criteria

An evaluator can run one vertical-slice command and immediately understand:
- what endpoints were discovered
- what semantics were inferred
- what was recommended expose, hide, or requires-review and why
- how the candidate MCP interface compares with a naive baseline
- how unsupported, insufficient, and malformed inputs are handled

The MVP succeeds by producing the complete comparison and inspectable
artifacts, not by meeting an arbitrary model score.
