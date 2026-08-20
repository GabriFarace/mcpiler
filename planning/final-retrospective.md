# Final Assessment Retrospective

## Verdict

The repository is a credible technical-assessment result for the approved
2–3 hour vertical slice. It works end to end, keeps deterministic and
probabilistic behavior separate, preserves failures honestly, and provides
inspectable planning and security decisions. The strongest evidence is the
reproducible compiler boundary and conservative failure model. The weakest
evidence is the live semantic result: it demonstrated containment, but not yet
the product's hoped-for semantic quality.

## Alignment from idea to MVP

The initial compiler idea included transitive source analysis, capability and
workflow discovery, and an MCP server. Product
grilling intentionally narrowed the assessment to endpoint-local curation over
one fixed FastAPI fixture. The approved scope and ADRs make those cuts explicit,
so their absence is not implementation drift:

| Initial direction | Assessment decision |
| --- | --- |
| Recover service behavior and workflows | Bound evidence to OpenAPI plus local handler syntax. |
| Generate and run an MCP server | Emit human-reviewable MCP-shaped artifacts only. |
| Let semantics decide exposure | Apply deterministic blockers and risk floors; require human publication review. |
| Broad benchmark or agent task | Preserve one qualitative live run and use fake-backed deterministic acceptance tests. |

## Final verification

Completed on 2026-08-20 after the evaluator-readiness audit:

- `uv sync --locked` completed successfully;
- `uv run python -m unittest discover -v` passed all 34 tests;
- `.venv/bin/python -m compileall -q mcpiler tests` passed;
- `git diff --check` passed;
- the deterministic CLI emitted eight IR records, four proposed tools, eight
  baseline tools, and the expected `4 expose / 3 requires-review / 1 hide`
  distribution with one intentionally degraded unmatched operation.

## What the AI-assisted workflow showed

AI assistance was used for problem grilling, scope/spec/ticket creation,
implementation, review, and remediation. The repository records the resulting
artifacts rather than treating chat output as authority. One real documentation
overproduction mistake and its correction are preserved in
`planning/agent-mistakes.md`. Later approved artifacts override brainstorming
and historical ticket state.

## Honest weaknesses

- The captured Gemma run returned validated structured results for only two
  matched endpoints and exposed no tools. This is strong failure-containment
  evidence but weak validation of the semantic-value hypothesis.
- The implementation is intentionally fixture-specific; the fixed operation
  set is rejected globally rather than presented as general API support.
- `mcpiler/compiler.py` is large because the time-boxed slice kept policy,
  projections, invariant checks, and artifact publication together.
- A dynamic FastAPI decorator is conservatively labeled unmatched rather than
  receiving the more precise unsupported reason deferred by T05.
- Raw Codex session exports are not present in the repository.

## Submission preparation

Before submitting:

1. publish the repository without `.env`, credentials, or local artifacts;
2. include a short screen recording of dependency sync, tests, deterministic
   compilation, the risk report, and the live-evaluation limitation;
3. export coding-agent session logs if available, or explicitly state that the
   export was unavailable;
4. lead the demo with the fair baseline-versus-candidate comparison;
5. name the live model result as the weakest part and explain the next
   experiment rather than presenting the fake analyzer as model quality.
