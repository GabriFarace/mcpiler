# MCPiler Risk and Curation Report

Candidate MCP interface decision aids requiring human review; not a deployable MCP server, authorization result, publication approval, or security guarantee.

Operational/action floors estimate likely state change only; they are not confidentiality, authorization, business-impact, or security classifications.

Naive baseline: 8 tools. Curated candidate: 0 tools. Recommendations: 0 expose, 8 requires-review, 0 hide.

| Operation | Baseline | Evidence | Semantic | Relevance | Floor | Signals | Effective | Recommendation | Policy | Gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DELETE /orders/{order_id}` | yes | matched/complete | succeeded | unknown | high | none | high | requires-review | CURATION_REVIEW_MATERIAL_UNCERTAINTY: explicit_semantic_uncertainty: The semantic analysis reports explicit uncertainty., unknown_relevance [openapi.operation]: The operation relevance is unknown. | none |
| `GET /internal/health` | yes | matched/complete | succeeded | unknown | low | none | low | requires-review | CURATION_REVIEW_MATERIAL_UNCERTAINTY: unknown_relevance [openapi.response_schema.0, source.handler]: The operation relevance is unknown. | none |
| `GET /orders` | yes | matched/complete | failed | unknown | low | none | low | requires-review | CURATION_REVIEW_BLOCKER: semantic_analyzer_failed: The semantic analyzer did not return an analysis. | none |
| `GET /orders/{order_id}` | yes | matched/complete | failed | unknown | low | none | low | requires-review | CURATION_REVIEW_BLOCKER: semantic_analyzer_failed: The semantic analyzer did not return an analysis. | none |
| `PATCH /orders/{order_id}/address` | yes | matched/complete | failed | unknown | medium | none | medium | requires-review | CURATION_REVIEW_BLOCKER: semantic_analyzer_failed: The semantic analyzer did not return an analysis. | none |
| `POST /orders` | yes | matched/complete | failed | unknown | medium | none | medium | requires-review | CURATION_REVIEW_BLOCKER: semantic_analyzer_failed: The semantic analyzer did not return an analysis. | none |
| `POST /orders/{order_id}/archive` | yes | unmatched/incomplete | skipped | unknown | medium | none | medium | requires-review | CURATION_REVIEW_BLOCKER: source_match_unmatched: The operation does not have one supported, unique source match., evidence_gap_source_unmatched: No exact literal route match. | source_unmatched |
| `POST /orders/{order_id}/refund` | yes | matched/complete | failed | unknown | medium | none | medium | requires-review | CURATION_REVIEW_BLOCKER: semantic_analyzer_failed: The semantic analyzer did not return an analysis. | none |
