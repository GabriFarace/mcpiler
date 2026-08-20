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

- [ ] Exactly one thin live implementation of the application-owned
      `SemanticAnalyzer` uses the approved `langchain-openai` integration and
      Pydantic contract; no second provider package, broad LangChain framework,
      MCP SDK, or live-evaluation framework is added.
- [ ] Runtime configuration supplies model, optional OpenAI-compatible base URL,
      credential, timeout, and retry settings without writing secrets to source,
      artifacts, or evaluation notes.
- [ ] The live analyzer accepts one bounded endpoint context at a time and sends
      only the normalized facts and bounded handler-local evidence approved by
      the spec.
- [ ] Source, docstrings, and OpenAPI descriptions are delimited and treated as
      untrusted data; the analyzer receives no tools, browser, repository access,
      or code-execution capability.
- [ ] Provider structured output passes through the same application-owned typed
      validation and evidence-reference validation as fake output before it can
      influence deterministic policy.
- [ ] Provider errors are represented by a stable public category and concise
      sanitized message; endpoint call failures degrade only the affected
      operation, while impossible analyzer initialization remains a global
      compilation failure.
- [ ] Raw prompts, raw provider responses, credentials, and rich provider
      payloads are neither logged nor emitted; artifacts retain only approved
      analyzer/provider/model and schema/prompt version provenance.
- [ ] One live run over the fixed fixture uses the same compilation boundary,
      policy, and four artifact renderers as the deterministic golden path and
      records the actual recommendation counts and degraded endpoint count.
- [ ] The live-run notes qualitatively review whether the address handler's
      visible precondition is evidence-linked, the refund handler's
      financial/external side effect is identified without becoming a security
      finding, the health endpoint is classified as internal/infrastructure,
      and absent or unsupported semantics are expressed as uncertainty rather
      than invented facts.
- [ ] The notes identify useful and incorrect inferences honestly and compare
      the live curated surface with the fair naive baseline without changing
      deterministic expectations to accommodate model behavior.
- [ ] No recommendation distribution, numeric score, accuracy metric, repeated
      trial, semantic pass threshold, or downstream natural-language
      tool-selection task is required or reported as MVP acceptance.
- [ ] Normal automated tests remain deterministic, inject the fake analyzer, and
      require no live credential, network access, paid call, or local model; the
      synced environment receives an import smoke test for the approved live
      dependencies.

## Public testing/evaluation seam to agree before coding

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

## Out of scope

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

`blocked`

## Implementation evidence placeholder

Not started. On completion, record the approved live configuration without
secrets, implementation summary, import and fake-backed test results, live run
command/result, artifact locations and actual counts, qualitative useful and
incorrect inferences, and known limitations here.
