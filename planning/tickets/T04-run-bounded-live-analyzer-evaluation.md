# T04: Run the bounded live analyzer evaluation

## Goal

Demonstrate that one approved OpenAI-compatible live semantic analyzer can be
substituted behind the provider-neutral boundary and run through the same
validation, deterministic curation, and artifact pipeline as the fake, then
record honest qualitative evidence about the resulting candidate interface.

## User-visible outcome

An evaluator can run the complete fixed fixture with the live analyzer, inspect
its actual Semantic IR, proposed manifest, naive baseline, and risk report, and
read a concise account of useful and incorrect model inferences. The live run is
evidence about the product hypothesis, while deterministic fake-backed tests
remain the authority for software correctness.

## Dependencies

Blocked by **T03: Curate and render the complete review artifact set**.

Before the live run, the exact provider/model, base URL where applicable, and
credential convention must be explicitly selected and documented. This is an
in-ticket human decision gate; it does not add another implementation ticket or
broaden the approved dependency set.

## Acceptance criteria

- [x] Exactly one thin live implementation of the application-owned
      `SemanticAnalyzer` uses the approved `langchain-openai` integration and
      Pydantic contract; no second provider package, broad LangChain framework,
      MCP SDK, or live-evaluation framework is added.
- [x] Runtime configuration supplies model, optional OpenAI-compatible base URL,
      credential, timeout, and retry settings without writing secrets to source,
      artifacts, or evaluation notes.
- [x] The live analyzer accepts one bounded endpoint context at a time and sends
      only the normalized facts and bounded handler-local evidence approved by
      the spec.
- [x] Source, docstrings, and OpenAPI descriptions are delimited and treated as
      untrusted data; the analyzer receives no tools, browser, repository access,
      or code-execution capability.
- [x] Provider structured output passes through the same application-owned typed
      validation and evidence-reference validation as fake output before it can
      influence deterministic policy.
- [x] Provider errors are represented by a stable public category and concise
      sanitized message; endpoint call failures degrade only the affected
      operation, while impossible analyzer initialization remains a global
      compilation failure.
- [x] Raw prompts, raw provider responses, credentials, and rich provider
      payloads are neither logged nor emitted; artifacts retain only approved
      analyzer/provider/model and schema/prompt version provenance.
- [x] One live run over the fixed fixture uses the same compilation boundary,
      policy, and four artifact renderers as the deterministic golden path and
      records the actual recommendation counts and degraded endpoint count.
- [x] The live-run notes qualitatively review whether the address handler's
      visible precondition is evidence-linked, the refund handler's
      financial/external side effect is identified without becoming a security
      finding, the health endpoint is classified as internal/infrastructure,
      and absent or unsupported semantics are expressed as uncertainty rather
      than invented facts.
- [x] The notes identify useful and incorrect inferences honestly and compare
      the live curated surface with the fair naive baseline without changing
      deterministic expectations to accommodate model behavior.
- [x] No recommendation distribution, numeric score, accuracy metric, repeated
      trial, semantic pass threshold, or downstream natural-language
      tool-selection task is required or reported as MVP acceptance.
- [x] Normal automated tests remain deterministic, inject the fake analyzer, and
      require no live credential, network access, paid call, or local model; the
      synced environment receives an import smoke test for the approved live
      dependencies.

## Testing/evaluation seam

The public evaluation seam is the same compilation boundary used in T03, with
only the `SemanticAnalyzer` implementation substituted. The agreed evidence for
this ticket is one completed live run, its four emitted artifacts, its actual
summary counts, and concise qualitative notes against the four semantic cases
named in the approved spec.

The live run is not a deterministic test and has no semantic pass threshold.
Valid but semantically wrong output is recorded as model-quality evidence;
invalid output follows the already-tested endpoint-local failure path. Normal
software tests continue to use the fake and assert shared validation, curation,
and failure invariants rather than live predictions or provider SDK internals.

## Out-of-scope notes

- `capabilities.yaml`, multi-tool capability discovery, or workflow generation.
- Evaluation harnesses, captured-run infrastructure, repeated trials,
  per-field scoring, numeric accuracy, or downstream tool-selection evaluation.
- Multiple live providers, provider comparisons, or additional integration
  packages.
- Prompt-injection test suites, broad provider failure diagnostics, raw payload
  capture, logging/redaction infrastructure, or partial-output recovery.
- Changes to deterministic fake expectations based on live model performance.
- A deployable MCP server, publication, authorization analysis, vulnerability
  detection, compliance classification, or security guarantees.

## Status

`done`

## Implementation evidence

Approved live configuration on 2026-08-20:

- provider: `openai-compatible` through LM Studio;
- base URL: `http://127.0.0.1:1234/v1` via `MCPILER_LIVE_BASE_URL`;
- model: required `MCPILER_LIVE_MODEL`; the exact loaded Gemma identifier will
  be recorded only after the captured run;
- credential: `MCPILER_LIVE_API_KEY` is required for the default hosted endpoint;
  with a custom LM Studio-compatible base URL, absent/blank uses the documented
  non-secret `lm-studio` placeholder because the local endpoint does not require
  an OpenAI credential;
- timeout: `MCPILER_LIVE_TIMEOUT_SECONDS=30`;
- retries: `MCPILER_LIVE_MAX_RETRIES=1`.

Implemented the one `LangChainOpenAISemanticAnalyzer` adapter and its
environment validation. The thin `--analyzer live` CLI selection initializes it
before calling the unchanged T03 compilation boundary; `--analyzer fake` remains
the default. Missing or invalid initialization configuration fails globally with
a concise `analyzer_initialization_failed` diagnostic and no artifacts.

The live adapter accepts one T01 `EndpointContext` per invocation, serializes
only its approved normalized OpenAPI, handler-local, evidence, provenance, and
completeness fields into canonical JSON, and encloses it in an explicit untrusted
data block. It binds the existing `EndpointSemantics` Pydantic contract through
`langchain-openai` JSON-schema structured output without tools. Parsed data has
adapter-owned provenance substituted, then passes through the existing shared
`validate_endpoint_semantics(context, candidate)` schema and endpoint-local
evidence-reference validation. Provider invocation failures are sanitized as the
existing endpoint-local `analyzer_failed`; parsing failures become
`invalid_semantic_output`; no raw prompts, responses, credentials, provider
exceptions, or rich provider payloads are logged or emitted.

Verification completed before the live run:

- `uv run python -m unittest discover -v` — 27 deterministic fake-backed tests
  passed; none constructs or calls the live analyzer.
- `.venv/bin/python -m compileall -q mcpiler tests` — passed.
- `.venv/bin/python -c 'from langchain_openai import ChatOpenAI; from
  mcpiler.live import LangChainOpenAISemanticAnalyzer, LiveAnalyzerSettings'`
  — import smoke passed.
- Canonical bounded-context serialization smoke — passed with stable evidence ID
  preservation and no model call.

Captured LM Studio run on 2026-08-20:

```text
env MCPILER_LIVE_MODEL=google/gemma-4-12b-qat \
  MCPILER_LIVE_BASE_URL=http://127.0.0.1:1234/v1 \
  MCPILER_LIVE_API_KEY=lm-studio \
  MCPILER_LIVE_TIMEOUT_SECONDS=30 \
  MCPILER_LIVE_MAX_RETRIES=1 \
  LANGSMITH_TRACING=false \
  uv run python -m mcpiler --analyzer live \
    --openapi fixtures/order_management/openapi.json \
    --source-root fixtures/order_management/backend \
    --output-dir planning/evals/t04-live-run/artifacts
```

The exact LM Studio model identifier was `google/gemma-4-12b-qat`. The run
produced these preserved artifacts:

- `planning/evals/t04-live-run/artifacts/semantic_ir.json`;
- `planning/evals/t04-live-run/artifacts/manifest.json`;
- `planning/evals/t04-live-run/artifacts/baseline_manifest.json`;
- `planning/evals/t04-live-run/artifacts/risk_report.md`.

Observed results, taken from the emitted Semantic IR and risk report, were zero
expose, zero hide, eight requires-review, and six degraded endpoints. These are
actual live results, not modified to match the deterministic fake outcome.

`DELETE /orders/{order_id}` and `GET /internal/health` returned validated
semantic output; the other five uniquely matched contexts had sanitized
`analyzer_failed` results. Health was described as an internal health check but
classified `unknown`, so deterministic policy required review. Address and
refund had no model semantic result, so their visible precondition and financial
or external-side-effect signal were not inferred. Archive was correctly skipped
without analyzer invocation because its source evidence is unmatched. The full
four-case qualitative record, including useful and incorrect behavior, is in
`planning/evals/t04-live-run.md`.

Known limitations: this single Gemma run was substantially more conservative
than the fake-backed golden path and did not provide usable address/refund
inferences. The implementation intentionally retains no raw provider failure
diagnostics, so the local analyzer failures cannot be attributed beyond their
stable public category. This is model/provider evaluation evidence, not a
software failure or a reason to weaken fake expectations or deterministic
policy.
