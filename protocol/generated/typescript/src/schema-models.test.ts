import assert from "node:assert/strict";
import test from "node:test";

import {
    schemaIds,
    type AutomationBindingRegistryV1,
    type SourceRecordV1,
} from "./schema-models.js";

test("generated schema catalog is sorted and complete", () => {
    assert.equal(schemaIds.length, 7);
    assert.deepEqual(schemaIds, [...schemaIds].sort());
    assert.ok(
        schemaIds.includes(
            "https://hwpx-agent.local/schemas/windows/hancom-binding-bundle-v1.schema.json",
        ),
    );
    assert.ok(
        schemaIds.includes(
            "https://hwpx-agent.local/schemas/windows/hancom-signed-binding-envelope-v1.schema.json",
        ),
    );
});

test("generated automation binding registry keeps target and coverage", () => {
    const registry = {
        schema_version: "hwpx-agent.automation-binding-registry/v1",
        source_lock_id: "source-lock-synthetic-p02",
        generator: {},
        restricted_derivative: true,
        target: { profile_id: "hancom-hangul-2020-secondary" },
        inputs: {},
        runtime_qualification: { state: "not_run" },
        bindings: [],
        coverage: { runtime_qualified_count: 0 },
    } satisfies AutomationBindingRegistryV1;
    assert.equal(registry.target.profile_id, "hancom-hangul-2020-secondary");
    assert.equal(registry.coverage.runtime_qualified_count, 0);
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
