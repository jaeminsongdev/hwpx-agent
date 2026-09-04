import assert from "node:assert/strict";
import test from "node:test";

import {
    boundedLifetime,
    parseBearerHeader,
    validateCatalog,
} from "./server.js";

const tokenPart = "a".repeat(12);
const bearer = `Bearer ${tokenPart}.${tokenPart}.${tokenPart}`;

test("parseBearerHeader accepts exactly one bounded JWT bearer", () => {
    assert.equal(
        parseBearerHeader(bearer),
        `${tokenPart}.${tokenPart}.${tokenPart}`,
    );
    assert.equal(parseBearerHeader([bearer]), undefined);
    assert.equal(
        parseBearerHeader(`bearer ${tokenPart}.${tokenPart}.${tokenPart}`),
        undefined,
    );
    assert.equal(parseBearerHeader("Bearer malformed"), undefined);
});

test("boundedLifetime accepts only the staging interval", () => {
    assert.equal(boundedLifetime(undefined), 300);
    assert.equal(boundedLifetime("30"), 30);
    assert.equal(boundedLifetime("900"), 900);
    assert.throws(() => boundedLifetime("29"));
    assert.throws(() => boundedLifetime("901"));
    assert.throws(() => boundedLifetime("30.5"));
});

test("validateCatalog requires eighteen unique bounded descriptors", () => {
    const tools = Array.from({ length: 18 }, (_, index) => ({
        name: `tool_${String(index).padStart(2, "0")}`,
        description: "fixture",
        inputSchema: { type: "object" },
        outputSchema: { type: "object" },
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
        _meta: {},
    }));
    const catalog = validateCatalog({
        schema_version: "hwpx-agent.mcp-public-tools/v1",
        descriptor_count: 18,
        tools,
    });
    assert.equal(catalog.tools.length, 18);
    assert.throws(() =>
        validateCatalog({
            schema_version: "hwpx-agent.mcp-public-tools/v1",
            descriptor_count: 18,
            tools: [...tools.slice(0, 17), tools[0]],
        }),
    );
});
