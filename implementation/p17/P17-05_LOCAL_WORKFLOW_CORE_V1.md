# P17-05 local workflow core v1

Date: 2026-09-06
Scope: current PC, private filesystem/Git-plan core
Decision: **first bounded increment implemented; P17-05 remains in progress**

`local-workflow` establishes the file-preservation boundary before any new MCP tool or Git process
is admitted. It materializes checksum-bound HWPX inputs into create-new private operation slots,
compares source/candidate identities without returning content, publishes a verified candidate to a
create-new output name and prepares a result-digest/current-HEAD-bound Git commit plan.

The core uses bounded streaming I/O up to the configured one-GiB product ceiling. It rejects
absolute paths, traversal, reserved Windows names, alternate data streams, links/reparse points,
wrong namespaces, zero or mismatched digests, oversized inputs, slot reuse and output overwrite.
Materialization failure removes only its newly created private target; input bytes are never
modified. Publication performs a second checksum-bound, create-new streaming copy into `output/`,
then removes the private candidate. Copy failures remove only the newly created output; cleanup
failure is reported separately as incomplete publication.

The Git helper reads only bounded local `.git/HEAD` and a `refs/heads/*` target and produces an exact
plan. It does not spawn Git, mutate the index or create a commit. Actual commit execution requires
the later P17-08 approval policy and therefore remains open. The core is not yet wired into the
private daemon or public MCP surface; P17-05 cannot be marked PASS from this increment alone.

Machine-readable boundaries are in `protocol/private/p17-local-workflow-v1.json`.
