# P17 frozen current workspace source qualification v47

The v47 current-source qualification is frozen at commit
`e736c62f309f77b77680e71c9ad334dda047e372`. The verifier reads its contract, current-host
document, receipt, 22 implementation sources, five current-PC evidence sources, 28 successors and
three guards only from exact committed Git history.

The result preserves the exact all-operation pure model, append-only reconciliation, pinned
loopback TLS 1.3 transport and actual current-PC Windows issue/write/read/revoke/delete evidence
without making mutable worktree files authoritative. The issuer and signing keys remain synthetic.
Client-assertion signature/freshness, external issuer/network access, a real credential, cross-system
atomicity, Windows power-loss durability, actual Windows refresh/rotate, registered-host lifecycle,
production, Hangul, other PC/version, `P17-06`, and product completion remain false.
