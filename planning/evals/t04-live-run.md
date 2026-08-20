# T04 Live Analyzer Evaluation

## Captured configuration

- Provider: `openai-compatible` through LM Studio.
- Base URL: `http://127.0.0.1:1234/v1`.
- Model: `google/gemma-4-12b-qat`.
- Credential convention: non-secret `lm-studio` placeholder.
- Timeout: 30 seconds.
- Retries: 1.
- Analyzer provenance: `langchain-openai-semantic-analyzer`, semantic schema
  `v1`, prompt `t04-v1`.
- LangSmith tracing: disabled.

The one captured run used the unchanged compilation boundary and wrote the four
artifacts in `planning/evals/t04-live-run/artifacts/`.

## Observed result

- Expose: 0.
- Hide: 0.
- Requires review: 8.
- Degraded endpoints: 6.

The proposed candidate surface therefore contains no tools, while the existing
fair naive baseline contains all eight operations. Five uniquely matched
endpoints produced sanitized endpoint-local analyzer failures. Those failures
are preserved here as model/provider evaluation evidence; no provider diagnostic
or raw response was retained.

## Address update

- Model inference: none; analysis failed before a semantic result was returned.
- Supporting evidence references: none from the model.
- Useful behavior: the compiler retained the operation and its structural
  evidence instead of guessing a precondition.
- Incorrect or uncertain behavior: it did not identify the visible
  not-already-shipped precondition in `source.handler`.
- Resulting deterministic recommendation: `requires-review`
  (`CURATION_REVIEW_BLOCKER`, `semantic_analyzer_failed`).

## Refund

- Model inference: none; analysis failed before a semantic result was returned.
- Supporting evidence references: none from the model.
- Useful behavior: the deterministic pipeline did not turn an absent model
  inference into a financial or external-side-effect claim.
- Incorrect or uncertain behavior: it did not identify the handler's refund
  side effect or emit an evidence-linked financial/external-side-effect review
  signal.
- Resulting deterministic recommendation: `requires-review`
  (`CURATION_REVIEW_BLOCKER`, `semantic_analyzer_failed`).

## Internal health

- Model inference: correctly described an internal health check with no
  preconditions, side effects, or semantic risk signals, but classified its
  relevance as `unknown`.
- Supporting evidence references: `openapi.operation`, `source.docstring`,
  `source.handler`, and `openapi.response_schema.0`.
- Useful behavior: the purpose and agent description stayed within the supplied
  endpoint evidence, and it did not invent a side effect.
- Incorrect or uncertain behavior: `unknown` relevance missed the approved
  `internal/infrastructure` classification, so the compiler could not hide the
  endpoint.
- Resulting deterministic recommendation: `requires-review`
  (`CURATION_REVIEW_MATERIAL_UNCERTAINTY`, `unknown_relevance`).

## Unsupported or absent semantics

- Model inference: none for `POST /orders/{order_id}/archive`; it was not sent
  to the analyzer because no unique literal source handler exists.
- Supporting evidence references: none from the model; deterministic source
  evidence records `no_literal_route_match` and `source_unmatched`.
- Useful behavior: the archive operation remained explicitly skipped rather
  than gaining invented semantics. The live run also emitted no model claims for
  the failed address/refund analyses.
- Incorrect or uncertain behavior: no additional endpoint semantics were
  available for review because five matched calls failed locally.
- Resulting deterministic recommendation: `requires-review`
  (`CURATION_REVIEW_BLOCKER`, unmatched source evidence).

## Limitations

This is one local-model run, not a benchmark or pass/fail result. It has no
numeric score, repeated trial, gold label, or downstream tool-selection task.
The result is useful chiefly as evidence that the bounded, validated pipeline
contains low-quality or unavailable model output conservatively.
