import assert from "node:assert/strict";
import test from "node:test";

import {
    boundedFixedClock,
    boundedLifetime,
    parseBearerHeader,
    validateOptionalKeyPairs,
} from "./server.js";

const tokenPart = "a".repeat(12);
const bearer = `Bearer ${tokenPart}.${tokenPart}.${tokenPart}`;

test("accepts exactly one bounded JWT bearer", () => {
    assert.equal(
        parseBearerHeader(bearer),
        `${tokenPart}.${tokenPart}.${tokenPart}`,
    );
    assert.equal(parseBearerHeader([bearer]), undefined);
    assert.equal(parseBearerHeader("Bearer malformed"), undefined);
});

test("bounds lifetime and optional server-owned fixture clock", () => {
    assert.equal(boundedLifetime(undefined), 300);
    assert.equal(boundedLifetime("30"), 30);
    assert.throws(() => boundedLifetime("29"));
    assert.equal(boundedFixedClock(undefined), undefined);
    assert.equal(boundedFixedClock("2000000000"), 2_000_000_000);
    assert.throws(() => boundedFixedClock("1"));
});

test("requires complete previous encryption key pairs", () => {
    assert.doesNotThrow(() => validateOptionalKeyPairs({}));
    assert.doesNotThrow(() =>
        validateOptionalKeyPairs({
            HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_REF: "kms.plan-v1",
            HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_B64: "x",
        }),
    );
    assert.throws(() =>
        validateOptionalKeyPairs({
            HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PREVIOUS_KEY_REF: "kms.review-v1",
        }),
    );
});
