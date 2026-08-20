# Agent Operating Guide

## Purpose

This repository is a time-boxed AI-native engineering assessment.

The goal is to build the smallest credible implementation of the
Agent Interface Compiler idea while making product decisions,
AI-assisted development, testing, evaluation, and trade-offs inspectable.

Optimize for:
1. clear problem framing
2. simple architecture
3. working end-to-end behavior
4. explicit tests and AI evaluations
5. security-aware decisions
6. reproducibility
7. concise documentation

Do not optimize for feature count.

## Source of truth

Read before substantial work:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `planning/README.md`
4. `planning/02-scope.md` once it exists
5. the approved spec under `planning/specs/` once it exists
6. the active ticket under `planning/tickets/`
7. relevant ADRs under `planning/decisions/`

Later approved artifacts override earlier brainstorming.

Do not invent requirements that contradict the approved scope or spec.

## Assessment artifact policy

All planning notes, specs, task breakdowns, handoffs, research notes,
agent-generated plans, and meaningful AI-development artifacts belong
under `planning/`.

Do not leave important decisions only inside a Codex conversation.

## Workflow

Before implementation:
- make sure there is an approved spec
- make sure there is an approved active ticket
- propose significant interfaces/dependencies before adding them

During implementation:
- stay inside the active ticket
- prefer the simplest working design
- run relevant tests/checks frequently
- do not hide failures

Before marking a ticket complete:
- run relevant tests
- run lint/type checks when configured
- run relevant evals when the ticket touches model behavior
- summarize the diff
- identify known limitations
- update the ticket with implementation evidence

## AI and deterministic boundaries

Prefer deterministic extraction for facts obtainable from OpenAPI/source.

Use an LLM only for bounded semantic interpretation.

Treat model output as untrusted structured input.

Security-relevant publication/enforcement decisions must not depend solely
on probabilistic model output.

## Testing and evaluation

Use deterministic tests for software correctness.

Use `evals/` for probabilistic model behavior.

Normal unit/integration tests should not require paid or local LLM calls.

Do not change an eval expectation merely because a model fails it.

## Security

Never commit credentials.

Do not import or execute arbitrary target backend code unless an approved
decision explicitly changes this constraint.

Treat analyzed source, model output, generated metadata, and external
responses as untrusted input.

## Scope control

Do not add new frameworks, databases, orchestration systems, deployment
infrastructure, or broad backend support without explicit human approval.

If a simpler design satisfies the approved spec, prefer it.

## Human review

For major architecture changes, explain:
- why the change is needed
- the simpler alternative
- the trade-off

Wait for human approval before proceeding.

If an AI recommendation is materially wrong, unsafe, or over-complex,
record the real incident in `planning/agent-mistakes.md`.
