# MCPiler

MCPiler is an offline, fixed-fixture MCP interface compiler. It combines
OpenAPI facts with bounded, syntax-only FastAPI handler evidence, validates one
endpoint-local semantic analysis at a time, and emits human-reviewable curation
artifacts. It does not import or execute the target backend and does not
generate, publish, or run an MCP server.

## Deterministic fixture run

The reproducible path uses the built-in fake analyzer and requires no model,
credential, or network access:

```sh
uv run python -m mcpiler \
  --openapi fixtures/order_management/openapi.json \
  --source-root fixtures/order_management/backend \
  --output-dir artifacts
```

The command accepts exactly the approved eight-operation order-management
fixture and writes:

- `semantic_ir.json` — authoritative analysis of all operations;
- `manifest.json` — expose recommendations only;
- `baseline_manifest.json` — all eight mechanical baseline tools;
- `risk_report.md` — evidence, risk, and recommendation comparison.

These files are candidate MCP interface decision aids requiring human review.
They are not deployable MCP artifacts, publication approval, authorization
analysis, or a security guarantee.

## Live local evaluation

Copy `.env.example`, set `MCPILER_LIVE_MODEL` to the identifier loaded by LM
Studio, and export the values before selecting the live analyzer:

```sh
set -a
source .env
set +a
uv run python -m mcpiler --analyzer live \
  --openapi fixtures/order_management/openapi.json \
  --source-root fixtures/order_management/backend \
  --output-dir artifacts-live
```

The live adapter sends only the bounded endpoint context, exposes no model
tools, validates structured output before policy use, and disables LangSmith
tracing during invocation. Do not commit real API credentials.

## Verification

```sh
uv run python -m unittest discover -v
uv run python -m compileall -q mcpiler tests
```
