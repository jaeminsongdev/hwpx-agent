import assert from "node:assert/strict";
import test from "node:test";

import {
    CONFIRM_GIT_APPROVAL_TOOL_NAME,
    confirmationArguments,
    inputMatchesPlan,
    parseGitApprovalInput,
    parseGitApprovalPlan,
    parseGitEffectReceipt,
} from "./git-approval-model.js";

const input = {
    workspace_id: "primary",
    operation_id: "op_widget_01",
    output_id: "result_01",
    expected_sha256: "a".repeat(64),
    message: "Publish verified HWPX",
};
const plan = {
    workspace_id: input.workspace_id,
    operation_id: input.operation_id,
    output_id: input.output_id,
    output_pathspec: "output/result_01.hwpx",
    expected_output_sha256: input.expected_sha256,
    expected_head: "b".repeat(40),
    expected_head_reference: "refs/heads/main",
    message: input.message,
    approval: {
        effect: "git_commit",
        target_sha256: "c".repeat(64),
        plan_sha256: "d".repeat(64),
    },
    executed: false,
} as const;

test("approval input and plan parsers require exact path-free bindings", () => {
    const parsedInput = parseGitApprovalInput(input);
    const parsedPlan = parseGitApprovalPlan(plan);
    assert.notEqual(parsedInput, null);
    assert.notEqual(parsedPlan, null);
    assert.equal(inputMatchesPlan(parsedInput!, parsedPlan!), true);
    assert.equal(parseGitApprovalInput({ ...input, path: "D:\\private.hwpx" }), null);
    assert.equal(parseGitApprovalPlan({ ...plan, confirmation_token: "secret" }), null);
    assert.equal(
        parseGitApprovalPlan({ ...plan, output_pathspec: "../result.hwpx" }),
        null,
    );
});

test("confirmation arguments contain displayed bindings and no token", () => {
    const parsed = parseGitApprovalPlan(plan)!;
    const argumentsValue = confirmationArguments(parsed, "z".repeat(43));
    assert.deepEqual(argumentsValue, {
        workspace_id: "primary",
        operation_id: "op_widget_01",
        output_id: "result_01",
        expected_sha256: "a".repeat(64),
        message: "Publish verified HWPX",
        expected_head: "b".repeat(40),
        expected_head_reference: "refs/heads/main",
        target_sha256: "c".repeat(64),
        plan_sha256: "d".repeat(64),
        approval_challenge: "z".repeat(43),
    });
    assert.equal(CONFIRM_GIT_APPROVAL_TOOL_NAME.includes("confirm"), true);
    assert.equal("confirmation_token" in argumentsValue, false);
    assert.equal("actor_sha256" in argumentsValue, false);
    assert.equal("tenant_sha256" in argumentsValue, false);
    assert.throws(() => confirmationArguments(parsed, "short"));
});

test("effect receipt must match every plan digest and identity", () => {
    const parsed = parseGitApprovalPlan(plan)!;
    const receipt = {
        workspace_id: "primary",
        operation_id: "op_widget_01",
        output_id: "result_01",
        commit_oid: "e".repeat(40),
        previous_head: "b".repeat(40),
        updated_reference: "refs/heads/main",
        output_sha256: "a".repeat(64),
        target_sha256: "c".repeat(64),
        plan_sha256: "d".repeat(64),
        approved_at_unix_seconds: 100,
        index_synchronized: true,
        executed: true,
    };
    assert.equal(parseGitEffectReceipt(receipt, parsed)?.executed, true);
    assert.equal(
        parseGitEffectReceipt({ ...receipt, plan_sha256: "f".repeat(64) }, parsed),
        null,
    );
    assert.equal(
        parseGitEffectReceipt({ ...receipt, confirmation_token: "secret" }, parsed),
        null,
    );
});
