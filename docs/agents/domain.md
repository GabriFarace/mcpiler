# Domain Docs

How engineering skills should consume this repository's domain documentation.

## Before exploring, read these

- `CONTEXT.md` at the repository root for shared terminology.
- Relevant ADRs under `planning/decisions/`.

If a relevant file does not exist, proceed without creating placeholder
documentation. Create or update domain documentation only when work resolves a
real terminology or architecture decision.

## File structure

This is a single-context repository:

```
/
├── CONTEXT.md
├── planning/
│   └── decisions/
└── mcpiler/
```

## Use the glossary's vocabulary

When naming a domain concept in a specification, ticket, code change, test, or
evaluation, use the terminology defined in `CONTEXT.md`. If a needed concept is
missing, reconsider whether existing terminology applies or record the genuine
gap for domain modeling.

## Flag ADR conflicts

If proposed work contradicts an existing ADR, surface the conflict explicitly
rather than silently overriding the decision.
