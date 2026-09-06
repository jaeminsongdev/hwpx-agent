# P17 current workspace source qualification v9

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact remote-sync mirror binding sources; no phase or product PASS**

The v1-v8 qualification contracts remain byte-for-byte unchanged. This v9 layer composes the exact
v8 contract and advances the source view to clean commit
`4be56eaf3f5b5eaf29233ba56f0769e25b99c503`.

Current-host source acceptance run `bec4941448134e6e99f8b0c4cc393eb3` passed all 11 checks. Its
canonical receipt SHA-256 is
`fc8c2fd42fcf38326108f1efb5b2890d6c43eeb19c8a5218935926ee18919f67`.
The fourteen composed predecessor successors remain exact. Locked/offline Cargo metadata remains
`d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d`
for 23 workspace members.

This successor binds fifty-two implementation files as exact regular-file bytes and exact Git blobs
at the base commit. It retains the forty-seven v8 implementation entries, replaces the changed
`local-sync` core identity, and adds the adapter, adapter regression test, v2 private contract,
migration note and implementation report. All 37 `local-sync` tests and all-target Clippy with
warnings denied passed before the implementation commit.

The new sources prove only that every private pull, push and checkpoint request carries the exact
opaque mirror identity and that the response digest binds those bytes. They do not prove a
credential provider, a host transport, a remote service, registration of
`project_conflict_resolve`, a concurrent Web/Codex conflict, an actual Hangul operation, P17-06 or
P17-07 completion, another PC/version, phase completion or product completion. All corresponding
claims remain false.
