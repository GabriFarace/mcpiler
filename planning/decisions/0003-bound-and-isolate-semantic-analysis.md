# Bound and isolate semantic analysis

The compiler depends on a provider-neutral `SemanticAnalyzer` with one live
model implementation and one deterministic fake. The live analyzer may receive
normalized facts plus size-bounded, deterministically truncated handler source
and docstring because this evidence is central to the hypothesis, but all text
is untrusted data: the analyzer cannot browse, use tools, or execute code, and
only typed validated output is accepted. This preserves semantic value and
testability while containing disclosure and prompt-injection risk.
