# Problem Framing

## User problem

AI/platform engineers with access to an existing FastAPI source tree and
matching OpenAPI document face a design problem when preparing APIs for LLM
agents: API operations are optimized for software clients, while agents
benefit from a smaller and semantically clearer action surface.

Straightforward OpenAPI-to-MCP conversion solves protocol translation but
does not necessarily solve agent-interface design.

## Failure modes of naive conversion

- too many tools
- infrastructure/internal endpoints exposed to the model
- weak operation descriptions
- handler-local preconditions absent from OpenAPI descriptions
- side effects not obvious from route/schema information
- destructive or financial operations insufficiently distinguished
- weak user-level purpose descriptions

## Product hypothesis

Combining deterministic API/source analysis with bounded semantic LLM
reasoning can produce a useful candidate MCP interface for human review.

This hypothesis is limited to evidence available from OpenAPI, route metadata,
schemas, bounded handler-local source/docstrings, and syntactically direct call
names. It does not claim to recover arbitrary business rules, preconditions, or
side effects hidden in deeper service implementations.

The MCP interface compiler retains every operation in its authoritative
semantic IR. Its candidate manifest contains only expose recommendations and is
MCP-shaped rather than a standard deployable artifact. Hidden and
requires-review operations remain visible in the full IR and review report.

## Why deterministic analysis first

Facts available from OpenAPI and source should be extracted directly rather
than inferred by a model.

The LLM should interpret already-extracted evidence rather than roam through
the repository without structure.

The compiler core reaches semantic analysis through a provider-neutral
`SemanticAnalyzer` interface. One live implementation demonstrates actual
model-backed behavior; a deterministic fake keeps normal compiler tests
independent of model access.

For the MVP, source evidence is deliberately narrow: literal FastAPI route
decorators, exact normalized method/path matching, handler identity and
location, signature, bounded source/docstring, and syntactically direct call
names. Ambiguous, dynamic, or unmatched patterns are reported rather than
guessed.

The matched handler source and docstring may be included in live analysis
because semantic interpretation is central to the hypothesis. They are bounded
by a fixed documented size limit and deterministic truncation rule, and any
truncation is recorded in evidence completeness.

## Why an LLM is useful

Business meaning can be implicit in:
- route and handler names
- handler-local validation logic
- docstrings and schemas
- syntactically direct call names that suggest possible side effects
- domain terminology

These signals can require semantic interpretation that is difficult to
encode completely with deterministic rules.

A direct call name is only a clue. The MVP does not inspect the callee and must
express deeper behavior as uncertainty rather than recovered fact. Resolving
one statically obvious local callee is a possible stretch feature.

Endpoint-level capability hints and multi-tool workflow discovery are stretch
work. They are not needed to validate endpoint curation.

## Safety boundary

LLM output is advisory, typed, and evidence-linked. Deterministic method-based
action-risk floors and blockers are applied before semantic elevation; model
findings cannot lower them. Relevance, effective risk, and recommendation stay
separate.

The fixed policy recommends expose for supported user-facing operations, hide
for supported internal/infrastructure operations, and requires-review for high
or unknown risk and every unsupported, malformed, or uncertain case. Thus a
financial refund can remain relevant while requiring review, and an unmatched
operation remains visible rather than being guessed or discarded.

A human owns publication and security-sensitive decisions. The output is not a
vulnerability report, authorization analysis, compliance classification, or
security guarantee.

## Failure handling

Unparseable OpenAPI, a missing source root, or impossible configuration fails
the compilation clearly. Ambiguous or unmatched source, materially truncated
evidence, malformed semantic output, invalid evidence references, and
per-endpoint provider errors are isolated to that endpoint: it remains visible
as requires-review and other endpoints continue. Rich provider-wide
diagnostics, recovery, logging, and failure-report infrastructure are stretch.
The governing invariant is that a local analysis failure reduces trust in that
endpoint, not availability of the entire compilation.

## Evaluation question

On the fixed eight-operation order-management fixture, does the compiler make
the difference from a fair one-operation-one-tool baseline immediately
inspectable?

The baseline exposes all eight operations. The expected candidate interface
exposes four user-facing operations, hides `GET /internal/health`, and requires
review for refund, deletion, and the unmatched archive operation. The report
must show the recommendation and evidence-linked reason for each endpoint.

A few fake-backed tests verify route matching and policy invariants. One live
demo run is described qualitatively to show whether handler-local evidence adds
useful semantics. Generic scoring, repeated trials, and downstream agent tool
selection are potential later evaluation work, not MVP claims.

## Fundamental limitation

Backend source alone cannot reveal every business workflow. Some semantics
may exist only in frontend code, documentation, tests, or runtime traces.

Even within the backend, the MVP does not resolve dynamic route registration,
runtime dependency-injection behavior, service implementations reached through
transitive calls, transaction boundaries, or actual external side effects.
Semantic analysis may infer possibilities from visible evidence, but those
inferences are not structural facts.

One-hop resolution of a statically obvious local callee may be explored as
stretch work; arbitrary transitive analysis remains excluded.

Normal software tests do not require paid, networked, or local model calls.
Cross-provider comparison is not needed to validate the MVP hypothesis.

Analyzed source, docstrings, and OpenAPI descriptions are untrusted data. They
are presented as quoted data to a tool-less analyzer that cannot browse or
execute the repository. Only typed validated output is accepted; invalid
output requires review. Dedicated prompt-injection, logging, and redaction
infrastructure is stretch work for this time-boxed slice.

The MVP does not attempt to solve that broader problem.
