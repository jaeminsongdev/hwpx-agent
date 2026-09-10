# P17 current workspace source qualification v44

Date: 2026-09-11

Decision: **PASS for the exact certificate-pinned TLS transport source successor only**

The canonical current-source runner passed all 11 checks against clean commit
`45426cac614a1da3fc3f69f10a49e7f7876d8c2f`. It recorded 28 exact source successors, the 27-member
locked/offline Cargo metadata projection and the unchanged immutable predecessor contracts.

The v44 qualification binds the independent remote TLS transport crate, its pinned dependencies,
private contract, migration, validator, tamper tests, bounded current-PC loopback evidence, v19
report and current ledger to that exact commit. The predecessor is the immutable frozen v43
contract; no v43 file or earlier durable push/pull and credential-custody evidence was rewritten.

Only ephemeral loopback TLS 1.3 with synthetic certificates is qualified. An external remote
network, real service certificate, real service credential, issuer/refresh/rotation lifecycle,
registered host, production, P17-06 completion, actual Hangul and product completion remain false.
