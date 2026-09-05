# P16-04 widget shell design specification

## Visual source

- Desktop concept: `implementation/p16/design/p16-04-widget-shell-desktop-concept.png`
- Narrow concept: `implementation/p16/design/p16-04-widget-shell-narrow-concept.png`
- The images are design references only. All visible text, controls, icons and state are implemented
  as HTML, CSS, SVG and React.

The desktop board shows ready, approval-pending and recoverable-error states together so their
relationship can be reviewed. The production widget renders only the current state. The narrow board
defines the single-column collapse and full-width action.

## Allowed visible copy

Korean is the primary locale and English is the tested fallback. No filename, document text, local
path, raw XML, COM/HAction name, account data or unbounded server message may become visible.

| Meaning            | `ko-KR`     | `en-US`             |
| ------------------ | ----------- | ------------------- |
| Product            | HWPX Agent  | HWPX Agent          |
| Surface            | 문서 작업   | Document work       |
| Connecting         | 연결 중     | Connecting          |
| Approval pending   | 승인 대기   | Approval pending    |
| Ready              | 준비됨      | Ready               |
| Recoverable error  | 복구 필요   | Recovery needed     |
| Closed             | 종료됨      | Closed              |
| Project            | 프로젝트    | Project             |
| Current revision   | 현재 리비전 | Current revision    |
| Validation         | 검증 상태   | Validation          |
| Validated          | 검증됨      | Validated           |
| Validation queued  | 검증 대기   | Validation queued   |
| Validation running | 검증 중     | Validating          |
| Validation partial | 부분 검증   | Partially validated |
| Validation failed  | 검증 실패   | Validation failed   |
| Not validated      | 검증 전     | Not validated       |
| Continue           | 계속        | Continue            |
| Retry              | 다시 시도   | Retry               |

The visible sentence and error catalogs are closed as well. They are never populated from server
text, exception messages or document content.

| State or error        | `ko-KR`                                        | `en-US`                                        |
| --------------------- | ---------------------------------------------- | ---------------------------------------------- |
| Connecting message    | 안전한 작업 환경을 연결하고 있습니다.          | Connecting a safe work environment.            |
| Approval message      | 호스트의 승인된 작업 입력을 기다리고 있습니다. | Waiting for approved tool input from the host. |
| Ready message         | 현재 프로젝트 정보를 확인했습니다.             | The current project information is available.  |
| Recovery message      | 연결을 새로 시작하면 다시 시도할 수 있습니다.  | Start a fresh connection to try again.         |
| Closed message        | 이 작업 화면의 연결이 종료되었습니다.          | This work view is no longer connected.         |
| `CONNECT_FAILED`      | 연결을 완료하지 못했습니다.                    | The connection could not be completed.         |
| `INVALID_TOOL_INPUT`  | 승인된 입력을 확인할 수 없습니다.              | Approved input could not be verified.          |
| `INVALID_TOOL_RESULT` | 안전한 결과 형식이 아닙니다.                   | The result did not match the safe format.      |
| `TOOL_CANCELLED`      | 작업이 취소되었습니다.                         | The operation was cancelled.                   |
| `TOOL_CALL_FAILED`    | 프로젝트를 다시 열지 못했습니다.               | The project could not be reopened.             |

Opaque IDs are displayed only as a six-character prefix plus an ellipsis. Missing values display an
em dash. Error detail is selected from a bounded local code catalog; raw exception text is excluded.

## Design tokens

- Canvas and light surface: true white `#ffffff`.
- Ink: `#172033`; muted text: `#5f6b7a`; hairline: `#d8dee8`.
- Primary blue: `#1769e0`; focus ring: `#8ab8f8`.
- Success: `#117a4b`; approval: `#9a5800`; error: `#c62d2d`. The three status colors meet
  WCAG AA against the light surface at small-text size.
- Dark theme uses host theme detection with `#111722` canvas, `#171f2c` surface, `#f4f7fb` ink and
  `#344054` hairlines. Dark status variants are `#5bd19a`, `#f0ad4e` and `#ff7b7b`; the light-blue
  primary control uses dark ink. Host-provided MCP Apps theme and CSS variables are applied when
  present. Arbitrary host font CSS is not injected while the resource CSP has no external domains.
- Typography: host sans variables first, then `system-ui`, `Segoe UI`, `Apple SD Gothic Neo`,
  `Noto Sans KR`, sans-serif. Chrome text is explicitly sized; browser defaults are not used.
- Spacing scale: 4, 8, 12, 16, 24 and 32 pixels. Radius is 12 pixels for the outer inline surface
  and 8 pixels for controls. Shadows are not used.
- Motion is limited to a 160 ms opacity/translate state transition and is disabled under
  `prefers-reduced-motion: reduce`.

## Component inventory

- `WidgetShell`: bounded inline application container and current-state composition.
- `StatusMark`: four small `currentColor` SVG variants: progress, document-check, clock and alert.
- `MetadataRows`: project, revision and validation values with definition-list semantics.
- `PrimaryAction`: one focus-visible button; disabled until the bridge is connected and input is
  approved. Retry reconnects only after an explicit click.
- `StateMessage`: short local copy selected by state and locale.

There is no navigation, sidebar, menu, fake document preview, card grid, toolbar or marketing layer in
P16-04. P16-05 through P16-08 add their own workflow surfaces without changing this shell contract.

## Container and responsive rules

- Start in MCP Apps `inline` mode and do not request a larger display mode in P16-04.
- At 720 px and above, status copy and metadata share one open two-column layout inside the single
  widget surface. Below 720 px, every region becomes one column and the action spans the width.
- Minimum supported CSS viewport is 320 px. Text wraps; identifiers truncate without horizontal
  scrolling. Touch targets are at least 44 px high.
- The host owns the iframe. The widget never reads a hostname or product name to choose behavior.

## Interaction and state ownership

- `connecting`: MCP Apps initialization is in progress; no server call is allowed.
- `approval_pending`: initialization succeeded but approval-gated tool input has not arrived. This is
  an expected state, not an error.
- `ready`: approved input arrived first and a schema-valid bounded snapshot with the same
  surface/project identity is present. Continue may call only the fixed read-only `project_open`
  tool; the server must re-authorize it.
- `recoverable_error`: malformed input/result, cancellation or connection failure is represented by
  a local error code. Retry creates a fresh bridge session.
- `closed`: teardown removed listeners and no interaction remains enabled.

Authoritative project and revision data stays on the server. React owns only ephemeral presentation
state. No localStorage, sessionStorage, cookie or `window.openai` state is used by this shell.

## Icon inventory

Every icon is a code-native SVG with a 24x24 view box, 1.8 px rounded stroke and `currentColor`.
Document-check is used for ready, clock for approval pending, alert-circle for recoverable error and a
small spinner ring for connecting. There are no brand marks or third-party icon dependencies.

## Implementation deviations

- The design boards show all states simultaneously for review; production shows exactly one state.
- The concept uses a large decorative document illustration. Production reduces it to a restrained
  48 px status mark so the widget remains useful at the minimum inline size.
- Concept placeholder bars are replaced with bounded opaque-ID prefixes or an em dash.

These deviations preserve the concept's hierarchy, palette, copy and container model while meeting
the security and inline-size requirements.
