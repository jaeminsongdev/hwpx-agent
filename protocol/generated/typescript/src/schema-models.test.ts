import assert from "node:assert/strict";
import test from "node:test";

import { schemaIds } from "./schema-models.js";

test("generated schema catalog is sorted and complete", () => {
    assert.equal(schemaIds.length, 3);
    assert.deepEqual(schemaIds, [...schemaIds].sort());
});
