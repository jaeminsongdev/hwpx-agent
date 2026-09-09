# P06 TABLE-005 table-to-text HWPX v0 to v1 migration

V1 introduces `hwpx-agent.table-table-to-text-hwpx.hancom-2020-plain-grid/1` as a new private
current-PC adapter profile. There is no compatible V0 payload to rewrite.

Callers must reread the exact top-level table wrapper, bind the complete typed source state/grid,
plain text grid, pagination, table/wrapper bytes and current document flow, then rebuild the exact deterministic plan immediately before lowering. They must provide an output text-block identity that
does not alias the table, a master cell or a cell payload.

Merged cells, formula/cache flattening, multiple cell paragraphs, dynamic/opaque content, captions,
nested tables and noncanonical wrappers have no reviewed exact native mapping and fail closed. LF and
CRLF remain distinct in returned bytes but map to the same typed HWPX line-break semantics.

Existing documents are not rewritten in place. A caller creates an isolated output and publishes it
only after exact paragraph/flow/table-count reopen succeeds. Static component or HWPX tests may not promote licensed Hangul, render, rollback, automation, differential, release, production or product
evidence.
