# MVP Scope

## MUST

- FastAPI/OpenAPI input
- local Python source input
- deterministic OpenAPI parsing
- static Python AST/source inspection
- route-to-handler/source matching
- bounded endpoint context construction
- provider-neutral semantic LLM adapter
- typed/validated semantic output
- evidence/provenance references
- confidence
- deterministic exposure policy
- semantic_ir.json
- manifest.json
- capabilities.yaml
- risk_report.md
- naive OpenAPI-to-tool baseline
- small deterministic test suite
- small semantic/tool-selection evaluation
- CLI entry point
- clear README and planning artifacts

## STRETCH

- inspect tests/docstrings as extra evidence
- generic manifest-backed MCP runtime
- MCP Inspector demo
- compare local LM Studio model with one cloud model
- richer human-readable risk report

## EXCLUDED

- arbitrary backend frameworks/languages
- GraphQL/RPC support
- graph database
- full static call/data-flow analysis
- frontend workflow mining
- API trace mining
- production authentication/RBAC
- real approval workflow
- deployment/Kubernetes
- multi-agent runtime
- production observability platform
- polished web UI
