# MVP Dependency Proposal Research

Date: 2026-08-20

## Recommendation

Assume the MVP cloud target is OpenAI or another service implementing the
OpenAI Chat Completions contract. Declare only these direct runtime
dependencies:

- `pydantic>=2.13.4,<3`
- `langchain-openai>=1.4.1,<2`

Declare no development dependencies. Use `unittest`, `tempfile`, and
`unittest.mock` for fake-backed deterministic tests.

After approval, add the requirements with `uv`; let `uv.lock` capture exact
direct and transitive versions. No dependency was installed during this
research.

## Dependency assessment

| Dependency | Exact MVP requirement | Why the standard library is insufficient | Placement | Simplest alternative | Status |
| --- | --- | --- | --- | --- | --- |
| `pydantic>=2.13.4,<3` | Define the nested typed semantic-analysis contract, reject wrong types/enums/unknown fields, validate untrusted model JSON, serialize accepted results, and generate the JSON Schema supplied for structured output. | `json` parses bytes and `typing`/dataclasses describe shapes, but the standard library has no declarative recursive runtime validator or schema generator. A manual validator would duplicate required-field, enum, nested-list, extra-field, and error-reporting logic at the most security-sensitive boundary. | Runtime | Dataclasses/TypedDict plus a hand-written strict validator and hand-authored JSON Schema. | Essential to the proposed validation design. |
| `langchain-openai>=1.4.1,<2` | Provide one thin `ChatOpenAI` adapter whose model, base URL, API key, timeout, and retry settings can select OpenAI cloud or the OpenAI-compatible LM Studio server, and bind the Pydantic schema for structured output. The application-owned `SemanticAnalyzer` remains the public boundary. | `urllib` is only an HTTP transport. It does not provide a maintained OpenAI protocol client, structured-output binding/parsing, provider error normalization, or standard timeout/retry behavior. Those could be implemented manually, but that is extra protocol code outside the timebox. | Runtime | Use the official `openai` SDK directly. It is leaner, but provides less model-level abstraction; the application would still own configuration and validation. | Essential if the approved implementation uses the permitted thin LangChain adapter; otherwise replace it rather than installing both. |

## Provider conclusion

LangChain documents that `ChatOpenAI` accepts a custom `base_url` and supports
model-level structured output with Pydantic schemas. LM Studio documents an
OpenAI-compatible `/v1/chat/completions` endpoint and the same JSON Schema
`response_format`. Therefore, using one configured `ChatOpenAI` adapter for LM
Studio and OpenAI cloud is a reasonable inference from their shared documented
protocol. It is not a guarantee that every local model will follow the schema;
LM Studio explicitly says structured-output capability is model-dependent.
The MVP already handles malformed output as endpoint-local `requires-review`
and treats valid semantic mistakes as evaluation evidence.

If the intended cloud target does not implement the OpenAI protocol, select it
explicitly before adding exactly one corresponding LangChain integration. Do
not pre-install multiple provider packages.

## No development dependency

`pytest` would improve fixture and assertion ergonomics, but it is
convenience-only. Python 3.14's `unittest` supports discovery and, together
with `tempfile` and `unittest.mock`, covers the single high compilation seam.
Tests inject the deterministic fake analyzer and never construct
`ChatOpenAI`, so normal tests have no live model or network requirement.

## Standard-library coverage

No package is needed for:

- OpenAPI JSON parsing or stable artifact serialization: `json`;
- non-executing Python syntax inspection and source locations: `ast`;
- the thin CLI: `argparse`;
- paths and file discovery: `pathlib`;
- environment configuration: `os.environ`;
- Markdown rendering: deterministic string formatting;
- deterministic testing: `unittest`, `tempfile`, and `unittest.mock`.

Consequently, do not add FastAPI, an OpenAPI validator, `jsonschema`, PyYAML,
Requests, HTTPX directly, python-dotenv, Click/Typer, an MCP SDK, pytest,
`langchain`, LangGraph, an agent framework, or an LM Studio SDK. Transitive
packages required by `langchain-openai` should remain transitive unless
application code imports their public APIs directly.

## Compatibility and package-management notes

The approved lower bounds advertise Python 3.14 support. On 2026-08-20, `uv`
resolved `langchain-openai` 1.6.0 and Pydantic 2.13.4 for this project. Package
metadata and successful resolution are not substitutes for tests, so the
synced Python 3.14 environment still needs an import smoke test and the
deterministic test suite.

## Primary sources

- [LangChain `ChatOpenAI` integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [LangChain model base URL guidance](https://docs.langchain.com/oss/python/langchain/models#base-url-and-proxy-settings)
- [LM Studio OpenAI-compatible API](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Pydantic package metadata](https://pypi.org/project/pydantic/)
- [`langchain-openai` package metadata](https://pypi.org/project/langchain-openai/)
- [Python 3.14 `unittest`](https://docs.python.org/3.14/library/unittest.html)
- [Python 3.14 `ast`](https://docs.python.org/3.14/library/ast.html)
- [Python 3.14 `json`](https://docs.python.org/3.14/library/json.html)
- [uv dependency management](https://docs.astral.sh/uv/concepts/projects/dependencies/)
