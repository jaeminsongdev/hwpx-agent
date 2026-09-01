import assert from "node:assert/strict";
import test from "node:test";

import { summarizeArtifact } from "./index.js";

test("renders explicit unverified state", () => {
    assert.equal(
        summarizeArtifact({
            artifactSha256: "a".repeat(64),
            validation: "unverified",
        }),
        "unverified:aaaaaaaaaaaa",
    );
});

test("rejects a non-checksum artifact identity", () => {
    assert.throws(
        () =>
            summarizeArtifact({
                artifactSha256: "user-document.hwpx",
                validation: "passed",
            }),
        /SHA-256/,
    );
});
