# Problem Framing

## User problem

Developers exposing existing enterprise APIs to LLM agents face a design
problem: API operations are optimized for software clients, while agents
benefit from a smaller and semantically clearer action surface.

Straightforward OpenAPI-to-MCP conversion solves protocol translation but
does not necessarily solve agent-interface design.

## Failure modes of naive conversion

- too many tools
- infrastructure/internal endpoints exposed to the model
- weak operation descriptions
- business preconditions hidden in service logic
- side effects not obvious from route/schema information
- destructive or financial operations insufficiently distinguished
- no user-level capability grouping

## Product hypothesis

Combining deterministic API/source analysis with bounded semantic LLM
reasoning can automate a useful first-pass curation step.

## Why deterministic analysis first

Facts available from OpenAPI and source should be extracted directly rather
than inferred by a model.

The LLM should interpret already-extracted evidence rather than roam through
the repository without structure.

## Why an LLM is useful

Business meaning can be implicit in:
- route and handler names
- validation logic
- called services
- external side effects
- domain terminology

These signals can require semantic interpretation that is difficult to
encode completely with deterministic rules.

## Safety boundary

LLM output is advisory structured data.

Final expose/hide/approval decisions are deterministic.

Possible conservative rules include:
- low confidence → hide
- internal/infrastructure operation → hide
- destructive operation → high deterministic risk floor

## Evaluation question

Does the curated interface outperform a naive one-operation-one-tool
baseline on:
- irrelevant/internal exposure
- risk identification
- semantic description quality
- representative tool-selection tasks?

## Fundamental limitation

Backend source alone cannot reveal every business workflow. Some semantics
may exist only in frontend code, documentation, tests, or runtime traces.

The MVP does not attempt to solve that broader problem.
