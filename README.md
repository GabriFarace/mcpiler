# MCPiler

MCPiler is an offline, fixed-fixture compiler that combines OpenAPI facts with bounded FastAPI source evidence to propose a smaller, semantically richer MCP-like tool surface for human review.

## Problem

A mechanical OpenAPI-to-MCP conversion turns every operation into a tool. That
preserves protocol shape but can expose internal endpoints, understate dangerous
actions, and omit handler-local business context. MCPiler tests a narrower
hypothesis: deterministic extraction plus bounded endpoint-local LLM analysis
can produce a more useful candidate interface without trusting the model to
publish or enforce it.

## Quick start

The reproducible path needs [uv](https://docs.astral.sh/uv/) and no model,
credential, or running FastAPI application. The first dependency sync may use
the network; the tests and fake-backed compiler path make no model or API call.
From the repository root:

```sh
uv sync --locked
uv run python -m unittest discover -v
uv run python -m mcpiler \
  --openapi fixtures/order_management/openapi.json \
  --source-root fixtures/order_management/backend \
  --output-dir artifacts
```

Expected summary:

```text
status=degraded expose=4 hide=1 requires-review=3 degraded=1
semantic_ir.json=artifacts/semantic_ir.json
manifest.json=artifacts/manifest.json
baseline_manifest.json=artifacts/baseline_manifest.json
risk_report.md=artifacts/risk_report.md
```

`degraded=1` is intentional: the OpenAPI-only archive operation has no matching
source handler, so it is retained for review instead of guessed. There is no web
application or MCP server to start; the CLI compiles review artifacts.

To exercise the optional live analyzer, load an OpenAI-compatible model in LM
Studio, copy `.env.example` to `.env`, set `MCPILER_LIVE_MODEL`, then run:

```sh
set -a
source .env
set +a
uv run python -m mcpiler --analyzer live \
  --openapi fixtures/order_management/openapi.json \
  --source-root fixtures/order_management/backend \
  --output-dir artifacts-live
```

## Example compiler output

The naive baseline exposes all eight operations. The deterministic candidate
exposes four, hides the internal health endpoint, and sends refund, deletion,
and unmatched archive operations to review:

| Operation | Baseline | MCPiler | Why |
| --- | --- | --- | --- |
| `GET /orders` | expose | expose | supported user-facing read |
| `PATCH /orders/{order_id}/address` | expose | expose | enriched with the handler-local precondition |
| `POST /orders/{order_id}/refund` | expose | requires-review | evidence-linked high financial signal |
| `DELETE /orders/{order_id}` | expose | requires-review | deterministic high action-risk floor |
| `GET /internal/health` | expose | hide | supported internal/infrastructure operation |
| `POST /orders/{order_id}/archive` | expose | requires-review | no literal source match |

An abridged proposed-manifest excerpt shows the evidence-linked enrichment:

```json
{
  "name": "update_order_address",
  "description": "Update an order delivery address before shipment.",
  "_meta": {
    "mcpiler": {
      "preconditions": [
        {
          "text": "The order must not already be shipped.",
          "confidence": "high",
          "evidence_refs": ["source.handler"]
        }
      ],
      "risk": {"operational_floor": "medium", "effective_risk": "medium"}
    }
  }
}
```

## Architecture

```text
OpenAPI + Python source
        |
        v
structural.py  -- deterministic JSON/AST extraction; target code is never run
        |
        v
semantic.py    -- typed endpoint-local analyzer boundary and validation
     /     \
fake fixture   live.py (one OpenAI-compatible adapter, no model tools)
     \     /
        v
compiler.py    -- deterministic risk floors, curation policy, and rendering
        |
        v
Semantic IR + proposed manifest + naive baseline + risk report
```

The Semantic IR is authoritative. Model claims can raise caution but cannot
lower deterministic risk floors, override incomplete evidence, or publish a
tool. Endpoint-local failures become `requires-review`; invalid global input
fails the run.

## Generated artifacts

| Artifact | Purpose |
| --- | --- |
| `semantic_ir.json` | Full structural evidence, validated semantics, provenance, risk, and recommendation for every operation. |
| `manifest.json` | MCP-shaped candidate tools for `expose` recommendations only. It is not a deployable MCP manifest. |
| `baseline_manifest.json` | Fair one-operation-to-one-tool OpenAPI baseline containing all eight operations. |
| `risk_report.md` | Human-readable comparison of evidence status, relevance, risk, policy reasons, and gaps. |

## Evaluation results

| Evaluation | Expose | Review | Hide | Degraded | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Deterministic fake-backed golden path | 4 | 3 | 1 | 1 | Reproducible compiler acceptance result; 34 tests pass. |
| Captured LM Studio / Gemma run | 0 | 8 | 0 | 6 | Conservative failure containment worked, but the model/provider produced little usable semantic value. |

The captured live run is a single qualitative observation, not a benchmark.
Its checked-in artifacts use the historical Semantic IR v1 contract and were
not regenerated after T05; the [evaluation note](planning/evals/t04-live-run.md)
explains the later v2 remediation and the model's useful and incorrect behavior.

## AI-assisted development process

The repository vendors the `mattpocock/skills` workflows under `.agents/skills`
and keeps the development record under `planning/`: problem framing, frozen
scope, an approved spec, vertical tickets, ADRs, dependency research, a captured
model evaluation, and a real agent correction in
[`planning/agent-mistakes.md`](planning/agent-mistakes.md). The commit history
keeps planning, implementation, evaluation, and remediation steps inspectable.

Raw Codex session exports are not checked in. Include them with the submission
if export is available; otherwise state that export was unavailable.

## Key trade-offs

- Fixed eight-operation fixture over a misleading claim of general FastAPI support.
- Syntax-only, handler-local evidence over importing target code or following a transitive call graph.
- One endpoint per model call over repository-wide context and workflow discovery.
- Deterministic policy and a human publication decision over model-controlled exposure.
- Qualitative live evidence plus deterministic tests over a rushed scoring framework.

## Known limitations

- Only JSON OpenAPI and the approved conventional literal FastAPI route shapes are supported.
- Dynamic or composed routes, dependencies, callee implementations, tests, frontend workflows, and runtime traces are not analyzed.
- Dynamic route decorators are conservatively reported as unmatched rather than with a more specific unsupported reason.
- The generated manifest is project-defined and MCP-shaped; no MCP server, authentication, approval workflow, or policy enforcement is generated.
- The fake analyzer proves deterministic software behavior, not LLM semantic quality; the one captured live run was weak and used the pre-T05 v1 IR.
- `compiler.py` intentionally keeps policy and rendering together for the time-boxed slice and would benefit from separation before broader development.

## Next steps

1. Diagnose the live structured-output failures and rerun the same bounded evaluation with a model that reliably follows the schema.
2. Add a small labeled endpoint set and repeated, per-field semantic evaluation without weakening deterministic expectations.
3. Generalize route extraction and report dynamic/composed route limitations precisely.
4. Split policy, artifact rendering, and filesystem publication as the compiler grows.
5. Only after the compiler evidence is credible, prototype a separate manifest-backed MCP runtime with explicit authorization and approval controls.
