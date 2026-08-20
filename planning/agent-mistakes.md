# Agent Mistakes

## 2026-08-20 — ADR proliferation during product grilling

The agent initially created fourteen small ADRs while capturing the grilling
decisions. Many recorded reversible scope details and did not satisfy the
repository skill's requirement that an ADR be hard to reverse, surprising
without context, and the result of a real trade-off. This added documentation
complexity while the task was explicitly reducing product complexity.

The correction consolidated the durable decisions into three ADRs and kept the
remaining agreed boundaries in the brief, problem framing, and scope. Future
grilling should apply all three ADR criteria before creating a decision file.
