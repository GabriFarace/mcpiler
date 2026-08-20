# Issue tracker: Repository-local Markdown

Specifications and implementation tickets for this repository are tracked as
Markdown files under `planning/`.

## Locations

- Specifications: `planning/specs/`
- Implementation tickets: `planning/tickets/`

All planning, task, and handoff artifacts remain under `planning/`. Do not use
`.scratch/` for issue or task tracking.

## Ticket conventions

- Create one file per implementation ticket.
- Name tickets `TNN-short-description.md`, where `NN` is a zero-padded number.
- Each ticket contains these sections:
  - Goal
  - User-visible outcome
  - Dependencies
  - Acceptance criteria
  - Testing/evaluation seam
  - Out-of-scope notes
  - Status
  - Implementation evidence
- The permitted statuses are: `proposed`, `ready`, `in-progress`, `done`, and
  `blocked`.

## When a skill says “publish to the issue tracker”

Write the appropriate specification to `planning/specs/` or implementation
ticket to `planning/tickets/`, following the conventions above.

## When a skill says “fetch the relevant ticket”

Read the referenced ticket under `planning/tickets/`. The user will normally
provide its path or ticket identifier.
