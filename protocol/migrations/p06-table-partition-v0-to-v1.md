# P06 whole-table partition v0 to v1 migration

`hwpx-agent.table-partition/v1` introduces a backend-neutral component contract for whole-table
split and join. Existing documents and HWPX packages are not rewritten by this migration.

The generated v0 catalog shape reused generic cell split/merge arguments such as `rows`, `columns`,
`direction` and `preserve_content`. Those fields do not define Hancom whole-table behavior and are
not silently reinterpreted. Callers must construct a v1 request from an exact table state and
document-flow binding:

- split uses the current cell coordinate, a distinct second-table ID and separator-paragraph ID;
- join uses exact leading/trailing states and an intervening token sequence restricted to spaces
  and paragraph breaks;
- formulas require an explicit reject or rebase-and-clear-cache policy;
- states carry exact grid, table-property, physical column-width, payload and cell-property
  identities.

Adapters remain separately versioned. A v0 payload receives an unsupported-version error until an
explicit semantic migrator supplies the missing state and flow evidence. Invalid or ambiguous input
returns no partial plan or receipt. HWPX lowering and actual Hangul behavior remain separate Gates.
