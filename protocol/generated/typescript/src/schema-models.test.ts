import assert from "node:assert/strict";
import test from "node:test";

import { schemaIds, type SourceRecordV1 } from "./schema-models.js";

test("generated schema catalog is sorted and complete", () => {
    assert.equal(schemaIds.length, 4);
    assert.deepEqual(schemaIds, [...schemaIds].sort());
});

test("generated SourceRecord model keeps identity and locator fields", () => {
    const record = {
        schema_version: "hwpx-agent.source-record/v1",
        record_id: "synthetic.help.file-open",
        source_lock_id: "source-lock-synthetic-p02",
        source_id: "synthetic-help",
        source_sha256: "1".repeat(64),
        source_kind: "help",
        locator: { kind: "anchor", value: "menu.file.open" },
        original_name: "문서 열기",
        description_ko: null,
        parameters: [],
        availability: {},
        extraction: {},
    } satisfies SourceRecordV1;
    assert.equal(record.locator.kind, "anchor");
});
