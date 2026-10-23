# P09-24 complete note package preparation policy

## 2026년 10월 19일 문단 ID 할당 수정

이전 생성기의 고정 body ID 101/102는 혼합 사례의 두 본문에서 충돌했다. 현재 생성기는 원본 section과 기존 note body의 실제 nonzero paragraph ID 최댓값 뒤에서 새 u32 ID를 할당한다. 삽입 plan과 lower도 원본·payload 중복 및 상호 충돌을 거부한다. 기존 IdIndex v1~v8, zero sentinel 및 저수준 source의 ID 부재 의미는 변경하지 않는다. 기존 source receipt/원본 fixture/P26 실패 기록과 아래 최초 준비 정책은 보존한다.

새 output은 `fixtures/target-build/p09-note-id-allocation-20261019-r01/output`이다. 원 생성기·삽입 관련14개 시험과 새3종의 기존 ID 검사/종류 변환이 통과했다. 별도 bounded 검사에서 문단 ID의 연속 할당, 원본 section 역복원, 모든 다른 expanded part와 body/style/intermediate-operation digest 보존을 확인했다. 과거9개는6변환/3기존ID거부이며 모두 변환됐다는 뜻이 아니다. 기존 oracle의 fixed101/102 기대와 frozen-source 검사는 역사적 profile에 남기고, 새 검사 기록011을 별도로 사용한다. `actual_hangul=false`, `save_reopen=NOT_RUN`, `green_rows=0`을 유지한다.

공식 [PType 모델](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/PType.h)은 ID의 unsigned integer 속성을 확인하는 근거이며, 주석마다 ID 범위가 독립이라는 근거로 확대하지 않는다.

## 최초 fixture 준비 정책

Use the unchanged P09-15 typed note engine and production preserving note adapter
to create complete disposable footnote, endnote and combined footnote/endnote HWPX
fixtures. Do not rewrite the older source receipt, contract, policy, report or
matrix. Do not edit user documents or source packages in place. This is preparation
for the missing complete-package/actual-target campaign, not a replacement Gate.

Require a deterministic generated Hancom2020Vs0 seed and immutable source identity.
Bind source document metadata to actual seed bytes and expanded package inventory,
not invented ambient hashes. Derive prospective insertion bytes before sealing the
final typed plan to the actual resulting section digest; final output must exactly
reproduce the prospective bytes. Independently reject stale section/payload inputs,
reread the complete ordered note inventory and preserve every unrelated expanded
package part. In the mixed case the second insertion must preserve the first note.

The named closed fixtures use existing header paragraph/character/style definitions
and multi-paragraph/multi-run plain text with XML escaping, Korean and non-BMP
characters. Marker number 1 is input state/model hypothesis only. The existing
plain-text profile does not support body objects or auto-number fields, so native
note appearance and application numbering remain unqualified pending actual runs.

The independent bounded read-only oracle validates exact filenames/identities,
duplicate/alias/path/bounds rules, package manifest/spine targets, note wrappers,
kind/IDs/anchors, raw body/text/length-framed style bindings and existing style
references. Remove note wrappers to recover the exact seed section and every
intermediate section. Reject mutated source, styles, bodies, unrelated parts,
claim coercion and broken state/section operation chains. Preserve old raw source
locks and never publish raw body text or private paths in qualification JSON.

New output must be exclusive and a direct child of the repository target-fixture
boundary, with no symlink/Junction/reparse ancestors. SecureWorkspace stages and
publishes only validated bytes. Repeat output and receipt generation must match.

The user's offline-only boundary remains in force: no Hangul/COM, access-allow
prompts, UI input, registry/trust edits, external network or user-document scans.
Static complete packages cannot prove actual Hangul, numbering, save/reopen,
render, automation/differential, note style/convert/export, production routing,
matrix green rows, P09 completion or full product readiness. Keep these NOT_RUN
or false until independently established; no new P10 work before the P09 Gate.
