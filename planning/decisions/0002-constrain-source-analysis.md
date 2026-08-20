# Constrain source analysis to literal routes and local handler evidence

The MVP supports literal FastAPI method/path decorators, exact normalized
method/path matching, and local handler evidence: identity, location,
signature, bounded source/docstring, and syntactically direct call names.
Ambiguous, dynamic, and unmatched patterns are reported instead of guessed,
and the compiler does not resolve runtime dependencies or transitive service
behavior. Optional one-hop resolution of a statically obvious local callee is
stretch work. This boundary preserves useful source-aware differentiation
while avoiding a partial program-analysis project whose apparent certainty
would exceed its evidence.
