# Domain Context

This file defines shared project terminology.
Codex may update it after product grilling if terminology changes.

## Backend endpoint

One HTTP method + route from the source FastAPI application.

## Structural evidence

Facts extracted deterministically from OpenAPI or Python source.

Examples:
- method and path
- schemas
- handler symbol
- source location
- direct calls

## Endpoint context

The bounded evidence package assembled for one endpoint before
semantic analysis.

## Semantic analysis

LLM-based interpretation of already-extracted evidence.

Possible outputs include:
- user-level purpose
- preconditions
- side effects
- semantic risk
- capability association
- agent-facing description
- uncertainty/confidence

## Semantic IR

Typed intermediate representation combining:
- deterministic facts
- semantic interpretation
- evidence/provenance
- confidence
- later policy decisions

## Candidate tool

An endpoint that could potentially become an agent-facing tool.

## Curated tool

A candidate that passes the deterministic exposure policy.

## Capability

A user-level outcome that may involve one or more tools.

A capability is a descriptive recipe/hint, not a mandatory workflow graph.

## Exposure policy

Deterministic rules deciding whether an operation is exposed, hidden,
or requires special treatment.

## Naive baseline

A one-OpenAPI-operation-to-one-tool transformation used for comparison.
