# Codex session index

These are the Codex tasks used to plan and implement the project before the
final assessment review and demo-preparation task.

| Task | Thread ID | Public export |
|---|---|---|
| Set up repository planning workflow | `01a01e10-34e9-76d1-848c-5c6f77bf6760` | `01-planning-workflow.jsonl` |
| Review project scope assumptions | `01a01e1a-4935-74f3-bf72-8cd605af92e7` | `02-scope-review.jsonl` |
| Create MVP compiler spec | `01a01e4e-3880-7c31-9a77-f892df5a02cd` | `03-mvp-spec.jsonl` |
| Decompose MVP spec into tickets | `01a01e6a-a8e0-7cc2-b834-07991afdb761` | `04-ticket-decomposition.jsonl` |
| Propose T02 semantic analysis design | `01a01ecf-44ea-7191-9632-1dd5694b009a` | `05-t02-semantic-analysis.jsonl` |
| Define deterministic T03 design | `01a01ef9-1b2c-7511-b5b2-c7aec58c8f8e` | `06-t03-deterministic-compiler.jsonl` |
| Propose T04 live analyzer | `01a01f19-74af-78c0-861f-c0023ab23c8d` | `07-t04-live-analyzer.jsonl` |
| Review implementation | `01a01f38-cd3d-7d50-b29b-be67b776052b` | `08-implementation-review.jsonl` |

The public exports retain user messages, Codex messages, short reasoning
summaries, tool names, and delegated-agent lifecycle events. They omit system
and developer instructions, credentials, tool arguments, tool outputs, raw
patches, and full internal reasoning. Each record keeps its timestamp and the
root/agent thread IDs so the work remains traceable.

The current task, `01a01f5d-a6ae-7c31-856e-18f180edfe76`, is intentionally
excluded because it concerns final review and demo preparation rather than the
project build.

A complete raw export is generated locally under `raw-local/`. That directory
is gitignored because raw Codex records can contain local paths, injected
instructions, command output, and other material that should be reviewed before
sharing separately.

Local raw archive details:

- file: `raw-local/mcpiler-codex-logs-previous-tasks.zip`
- included rollouts: 29 (the eight main tasks plus delegated-agent runs)
- compressed size: 6,603,596 bytes
- SHA-256: `d2ea5eceb5026c03396a2c981fc2f0fffd47b9cd367bfe8dc5a6df3c8d752bb6`
