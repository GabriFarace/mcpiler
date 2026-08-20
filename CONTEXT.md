# Domain Context

This file defines shared project terminology.
Codex may update it after product grilling if terminology changes.

## MCP interface compiler

An offline agent-interface curator that proposes a human-reviewable MCP tool
surface from API and bounded source evidence. It does not generate, publish, or
run an MCP server.

## Backend endpoint

One HTTP method + route from the source FastAPI application.

## Structural evidence

Facts extracted deterministically from OpenAPI, route metadata, schemas, or
bounded handler-local Python source. It excludes inferred semantics and
transitive runtime behavior.

## Endpoint context

The bounded evidence package assembled for one endpoint before semantic
analysis. It preserves the distinction between facts and later inferences.

## Semantic analysis

LLM-based interpretation limited to one endpoint context. It does not recover
business rules hidden outside the supplied evidence.

## Semantic analyzer

A provider-neutral boundary that accepts one endpoint context and returns typed
semantic analysis.

## Semantic IR

A typed intermediate representation combining structural evidence, semantic
claims and provenance, evidence completeness, uncertainty, relevance, risk,
and the curation recommendation.

## Evidence completeness

Deterministic metadata describing whether expected evidence is present and
usable. It is distinct from model confidence.

## Relevance

An independently inspectable classification of an endpoint as user-facing,
internal/infrastructure, or unknown. It describes usefulness to an agent, not
safety.

## Risk

An independently inspectable combination of an operational/action risk floor
and semantic review signals. It is separate from endpoint relevance and is not
an overall security classification.

## Operational/action risk floor

A deterministic minimum describing likely state-changing behavior from the
HTTP method. It does not classify confidentiality, authorization, or business
impact.

## Semantic risk signal

An evidence-linked semantic claim that may raise effective risk. It is a review
signal, not a vulnerability finding, authorization analysis, compliance
classification, or security guarantee.

## Curation recommendation

An expose, hide, or requires-review result derived by the curation policy from
relevance, risk, evidence completeness, and claim-level uncertainty.

## Candidate tool

An endpoint that could potentially become an agent-facing tool.

## Curated tool

A candidate that the curation policy recommends to a human reviewer for
inclusion. It is not automatically published or authorized.

## Capability hint

An endpoint-level semantic inference describing the user outcome that one
candidate tool may support, such as "refund an eligible order." It is not a
discovered or validated workflow.

## Multi-tool capability

A proposed user-level workflow involving more than one tool. Discovering and
validating multi-tool capabilities requires global analysis and is outside the
MVP.

## Curation policy

Deterministic rules deriving expose, hide, or requires-review from evidence,
relevance, and risk. The result is a review aid, not a publication or
authorization decision.

## Semantic IR artifact

The authoritative full analysis of every OpenAPI operation, including
unmatched operations, evidence, inferences, relevance, risk, and curation
recommendation.

## Proposed manifest

A project-defined candidate MCP interface containing only operations with an
expose recommendation. It is human-reviewable and MCP-shaped, not a standard
deployable MCP artifact.

## Risk report

A human-review view covering every operation, with particular visibility for
hide and requires-review recommendations, their reasons, and evidence gaps.

## Compilation failure

A global input or configuration failure that prevents a trustworthy run. An
endpoint-local analysis failure instead reduces trust in that endpoint, which
is retained as requires-review while unrelated endpoints continue.

## Naive baseline

A one-OpenAPI-operation-to-one-tool transformation used for comparison. It
exposes every operation and preserves all useful names, descriptions,
parameters, schemas, and other metadata available in OpenAPI; it is not
intentionally weakened.
