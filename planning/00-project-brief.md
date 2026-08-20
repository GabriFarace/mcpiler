# Project Brief — Agent Interface Compiler

## Problem

Existing REST APIs are designed primarily for programmatic clients and
frontend applications, not autonomous LLM agents.

Mechanical OpenAPI-to-MCP conversion can expose too many operations,
including infrastructure-oriented, internal, or dangerous endpoints,
while failing to communicate business-level semantics such as purpose,
preconditions, side effects, and user-level capabilities.

## Product hypothesis

Deterministic structural analysis combined with bounded LLM semantic
reasoning can compile a FastAPI backend into a smaller, safer, and more
semantically useful agent-facing interface.

## Target user

An AI/platform engineer who needs to expose an existing enterprise backend
to LLM agents without manually designing every MCP tool.

## MVP input

- FastAPI OpenAPI document
- local Python source tree

## MVP output

- semantic_ir.json
- manifest.json
- capabilities.yaml
- risk_report.md

## Core pipeline

OpenAPI + Python source
→ deterministic structural extraction
→ bounded endpoint context
→ LLM semantic analysis
→ semantic IR
→ deterministic exposure policy
→ generated interface artifacts

## Responsibility of the LLM

The semantic model may infer:
- user-level purpose
- likely preconditions
- side effects
- semantic risk
- capability association
- agent-facing description
- uncertainty/confidence

The LLM does not own final security or exposure decisions.

## Initial constraints

- FastAPI only
- REST/OpenAPI only
- static Python/source analysis
- no arbitrary target-code execution
- no graph database
- no frontend analysis
- no traffic mining
- no production authorization system
- no multi-agent runtime

## Evaluation hypothesis

Compared with a naive one-endpoint-one-tool transformation, semantic
compilation should:
- expose fewer irrelevant/internal operations
- identify risky operations more effectively
- provide richer agent-facing descriptions
- improve tool selection on representative user tasks

## Demo shape

Use one small synthetic order-management backend with roughly 8–10
endpoints containing both user-facing and internal/risky operations.

## Success criteria

An evaluator can run one command and understand:
- what endpoints were discovered
- what semantics were inferred
- what was exposed or hidden and why
- what capabilities were discovered
- how the curated interface compares with a naive baseline
