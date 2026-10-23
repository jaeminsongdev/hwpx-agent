# P09 native-form package public exports: source bridge v3 to v4

P09-31 adds real package reader/binder and global output exports. Its four exact
spans recover P09-28/r02 lib raw SHA
`d39fd55db3e98dc3130ca8aca8f35d1dd67557b4bb2f127b9e7ee2c439daa987`.
Unchanged v3/v2/v1 exact projections retain the full P08 authority.

Named raw archives are under
`implementation/p09/source-archive/p09-31-pre-package-export/`. Lib and migrated
tests are preserved, not overwritten; the three source capsules P09-28/r02,
P09-29 and P09-30 keep original bytes. Older current verifiers must actually
fail after this export. Historical checked archive sources are not live PASS.

Both current pending test targets keep byte-exact bodies but explicit local
imports resolve genuine glob-import collisions caused by new public symbols.
New public test targets use the library only and preserve those same bodies.
The two previously nested lowerer checks run in the real library unit target;
17 + 19 public integration cases and 2 library checks are separate real results.

Current Python tests distinguish historical capsule claims from v4 current public
execution. Original mutants stay; obsolete full source qualification correctly
rejects current lib rather than having its expected hashes refreshed. Four
current generated package cases are compared by unchanged independent oracles.
No new native execution/route/render/differential or phase/product Gate is claimed.
