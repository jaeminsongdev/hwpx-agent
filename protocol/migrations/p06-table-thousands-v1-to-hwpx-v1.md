# P06 table thousands migration: model v1 to HWPX v1

Before this profile, `hwpx-agent.table-thousands/v1` produced only a grouping-flag plan over typed
formula cells. It did not define how Hangul stores or displays the thousands separator.

## Required migration

1. Read the exact selected formula fields from a complete unmerged table grid.
2. Admit only the current-target `=SUM(LEFT)` profile with grouped `LastResult`, `%g,` result format
   and an exactly consistent packed command.
3. Bind the exact section, selected state, grid, document flow and domain plan SHA-256 values at
   request time and recheck them at build time.
4. Change only the selected visible-result text span; preserve formula metadata, AST, cache,
   decimal places, owners and every unowned section byte.
5. Reopen through the typed reader and return no output on any mismatch or limit failure.

The v1 HWPX adapter is not a general numeric formatter. Direct-output package save/reopen, render,
product automation routing and other-version compatibility require separately versioned oracle
evidence and may not be inferred from this migration.
