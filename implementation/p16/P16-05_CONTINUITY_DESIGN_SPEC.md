# P16-05 project continuity design specification

## Visual source and product boundary

- Concept: `implementation/p16/design/p16-05-continuity-concept.png`.
- Final captures: `implementation/p16/visual-qa/p16-05-*.png`.
- The concept is a design reference. Every production element is implemented as React, semantic
  HTML, CSS and code-native SVG. The image is never loaded by the widget.

P16-05 adds a separate project-continuity resource. It does not change the P16-04 shell resource or
the eighteen UI-independent P15 workflow tools. The view exposes a bounded current-head summary,
recent immutable revision nodes, warning count, conflict state, refresh and an explicitly confirmed
checkpoint action. It is not a document viewer, file browser or revision-content inspector.

## Information hierarchy

1. Product and surface identity.
2. Current connection state and a closed conflict badge.
3. A three-row project/head/warning summary using opaque identifier prefixes only.
4. At most six recent revision nodes. Each node shows a closed local change-kind label, an opaque
   identifier prefix and a UTC calendar date. Raw revision summaries are classified and discarded.
5. One primary and at most one secondary action. There is no navigation, nested scrolling, menu or
   expandable detail.

The generated concept proposed a larger two-pane history/detail view. The inline implementation
keeps its timeline, head emphasis, conflict banner and checkpoint hierarchy while removing raw notes,
detail navigation and a separate conflict action. This preserves the design direction within the
official inline action budget.

## State and action model

- `connecting` and `approval_pending` behave like P16-04 and allow no tool call.
- `ready/view` with no conflict exposes secondary Refresh and primary Create checkpoint.
- `ready/view` with `locked`, `stale` or `diverged` disables every write and exposes only Refresh.
- `ready/confirm_checkpoint` replaces the action row with Cancel and Confirm and create. Entering
  this mode makes no server call. The second explicit click calls `project_checkpoint`; the host and
  server must still authenticate, authorize and confirm it.
- A successful checkpoint result is accepted only when its request and revision identities match.
  `replayed` is displayed separately from a newly saved checkpoint.
- Malformed input, malformed result, cancellation, refresh failure and checkpoint failure clear
  authoritative data and map to bounded local copy. Raw errors are never rendered.

Refresh calls exact read-only `project_open`, followed by exact read-only `project_history`. Both
response request IDs must match. The project must match the approved render input, and the newest
returned revision must match the open result's head. No partial refresh becomes visible.

## Data minimization

- Render input: schema version, client surface, locale and one project ID.
- Render result: project/head identifiers, warning count, closed conflict state, at most twelve
  normalized revision entries and an opaque cursor. The view renders at most six entries.
- Public history `summary` strings are bounded, classified into `created`, `edited`, `transformed`,
  `validated`, `imported` or `unknown`, then discarded before UI state is updated.
- Filenames, paths, document text, revision notes, raw XML, HAction/COM identifiers, URLs,
  credentials, account data and raw server messages are not accepted by the continuity schema.

## Visual and responsive rules

- The P16-04 light/dark token family is retained. Success, warning and error colors meet 4.5:1
  contrast against their intended surfaces.
- The 720 px breakpoint collapses metadata and history into one column. At 500 px, confirmation and
  conflict notices remain visible without horizontal or nested scrolling.
- Buttons are at least 44 px high, focus-visible, keyboard-native controls. Status changes use
  `aria-live`; conflict uses `role=alert`; checkpoint completion uses `role=status`.
- Motion is limited to the connecting spinner and is disabled under reduced-motion preference.

## Evidence boundary

The real `@modelcontextprotocol/ext-apps` `App` and `AppBridge` execute a local browser iframe
round-trip for approved render input/result, refresh and checkpoint. This is strong component E2E,
but it is not an actual ChatGPT or Codex host, registered plugin, Developer mode, remote MCP,
Hangul/COM or production acceptance. Those claims remain open.
