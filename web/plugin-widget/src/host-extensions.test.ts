import assert from "node:assert/strict";
import test from "node:test";

import { detectOptionalHostExtensions } from "./host-extensions.js";

test("feature-detects optional host methods without using hostname or product identity", () => {
    assert.deepEqual(
        detectOptionalHostExtensions({ location: { hostname: "chatgpt.com" } }),
        {
            available: false,
            canRequestDisplayMode: false,
            canOpenExternal: false,
        },
    );
    assert.deepEqual(
        detectOptionalHostExtensions({
            openai: {
                requestDisplayMode: () => undefined,
                openExternal: "not-a-method",
            },
        }),
        {
            available: true,
            canRequestDisplayMode: true,
            canOpenExternal: false,
        },
    );
});
