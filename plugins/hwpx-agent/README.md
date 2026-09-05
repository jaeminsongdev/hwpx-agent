# HWPX Agent universal package base

This directory is the immutable, registration-free P16-02 package base. It contains only the
validated plugin manifest and bounded local assets.

The base deliberately omits `apps`, `.app.json`, `mcpServers`, `.mcp.json` and `skills`:

- a registered app mapping is injected only from a user-confirmed Developer mode registration
  receipt;
- the nine workflow skills are validated and composed by P16-03;
- widget resources are implemented by P16-04 and later cards;
- public URLs, privacy/terms metadata and screenshots wait for real production ownership and review.

Do not put credentials, endpoint secrets, Windows paths, user documents, raw HWPX XML or
HAction/COM identifiers in this directory. Release composition writes a new no-overwrite artifact;
it never edits this source package in place.
