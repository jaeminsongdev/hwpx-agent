import assert from "node:assert/strict";
import test from "node:test";

import {
    APPROVAL_PROTOCOL,
    DIFF_TOOL_NAME,
    EFFECT_PROTOCOL,
    EXECUTE_COMMIT_TOOL_NAME,
    MATERIALIZE_TOOL_NAME,
    PRIVATE_PROTOCOL,
    PREPARE_APPROVAL_TOOL_NAME,
    PREPARE_COMMIT_TOOL_NAME,
    PUBLISH_TOOL_NAME,
    TARGET_PROFILE,
    TOOL_NAME,
    WORKFLOW_PROTOCOL,
    childEffectEnvironment,
    childEnvironment,
    parseRuntimeArguments,
    privateApprovalRequest,
    privateEffectRequest,
    privateHealthRequest,
    privateWorkflowRequest,
    validateApprovalEnvelope,
    validateEffectEnvelope,
    validateHealthEnvelope,
    validateWorkflowEnvelope,
} from "./server.js";
import type { GitCommitPlanResult } from "./server.js";

const token = "A".repeat(43);
const daemon = "D:\\product\\local-companion-daemon.exe";
const config = "D:\\runtime\\config.json";

function validEnvelope(): Record<string, unknown> {
    return {
        protocol_version: PRIVATE_PROTOCOL,
        request_id: "mcp-health",
        ok: true,
        result: {
            status: "ready",
            target_profile: TARGET_PROFILE,
            automation_enabled: false,
            network_enabled: false,
            workspace_count: 1,
            config_sha256: "a".repeat(64),
        },
    };
}

test("runtime arguments require exact absolute daemon and config paths", () => {
    assert.deepEqual(
        parseRuntimeArguments(["--daemon", daemon, "--config", config]),
        { daemonPath: daemon, configPath: config },
    );
    assert.throws(() => parseRuntimeArguments([]));
    assert.throws(() =>
        parseRuntimeArguments(["--config", config, "--daemon", daemon]),
    );
    assert.throws(() =>
        parseRuntimeArguments(["--daemon", "relative.exe", "--config", config]),
    );
    assert.throws(() =>
        parseRuntimeArguments([
            "--daemon",
            daemon,
            "--config",
            config,
            "extra",
        ]),
    );
});

test("private health request is exact and token-bound", () => {
    assert.deepEqual(privateHealthRequest(token), {
        protocol_version: PRIVATE_PROTOCOL,
        request_id: "mcp-health",
        session_token: token,
        method: "health",
        params: {},
    });
    assert.throws(() => privateHealthRequest("short"));
});

test("child environment contains only token and bounded Windows roots", () => {
    const environment = childEnvironment(token);
    assert.equal(environment.HWPX_AGENT_LOCAL_SESSION_TOKEN, token);
    for (const key of Object.keys(environment)) {
        assert.ok(
            ["HWPX_AGENT_LOCAL_SESSION_TOKEN", "SystemRoot", "WINDIR"].includes(
                key,
            ),
            key,
        );
    }
    assert.equal(environment.PATH, undefined);
});

test("effect child environment is all-or-none, bounded, and allowlisted", () => {
    const source = {
        SystemRoot: "C:\\Windows",
        WINDIR: "C:\\Windows",
        PATH: "D:\\untrusted-bin",
        HWPX_AGENT_GIT_PROGRAM: "C:\\Program Files\\Git\\cmd\\git.exe",
        HWPX_AGENT_APPROVAL_STATE_ROOT: "D:\\runtime\\approval-state",
        HWPX_AGENT_APPROVAL_SECRET: "A".repeat(43),
        SHOULD_NOT_PASS: "private",
    };
    assert.deepEqual(childEffectEnvironment(token, source), {
        HWPX_AGENT_LOCAL_SESSION_TOKEN: token,
        SystemRoot: "C:\\Windows",
        WINDIR: "C:\\Windows",
        HWPX_AGENT_GIT_PROGRAM: "C:\\Program Files\\Git\\cmd\\git.exe",
        HWPX_AGENT_APPROVAL_STATE_ROOT: "D:\\runtime\\approval-state",
        HWPX_AGENT_APPROVAL_SECRET: "A".repeat(43),
        TEMP: "D:\\runtime\\approval-state",
        TMP: "D:\\runtime\\approval-state",
    });
    assert.throws(() =>
        childEffectEnvironment(token, {
            ...source,
            HWPX_AGENT_APPROVAL_SECRET: undefined,
        }),
    );
    assert.throws(() =>
        childEffectEnvironment(token, {
            ...source,
            HWPX_AGENT_GIT_PROGRAM: "git.exe",
        }),
    );
});

test("daemon health requires the exact bounded redacted envelope", () => {
    assert.deepEqual(validateHealthEnvelope(validEnvelope()), {
        status: "ready",
        target_profile: TARGET_PROFILE,
        automation_enabled: false,
        network_enabled: false,
        workspace_count: 1,
        config_sha256: "a".repeat(64),
    });
    assert.throws(() =>
        validateHealthEnvelope({ ...validEnvelope(), private_path: config }),
    );
    const enabled = validEnvelope();
    (enabled.result as Record<string, unknown>).network_enabled = true;
    assert.throws(() => validateHealthEnvelope(enabled));
    const expanded = validEnvelope();
    (expanded.result as Record<string, unknown>).extra = "invented";
    assert.throws(() => validateHealthEnvelope(expanded));
});

test("workflow requests are path-free exact and protocol-v2 bound", () => {
    const params = {
        workspace_id: "primary",
        operation_id: "operation-01",
        slot: "source",
        fixture_id: "fixture-01",
        expected_sha256: "a".repeat(64),
    };
    assert.deepEqual(privateWorkflowRequest(token, "materialize", params), {
        protocol_version: WORKFLOW_PROTOCOL,
        request_id: "mcp-workflow-materialize",
        session_token: token,
        method: "materialize",
        params,
    });
    assert.throws(() =>
        privateWorkflowRequest(token, "materialize", {
            ...params,
            fixture_id: "../fixture",
        }),
    );
    assert.throws(() =>
        privateWorkflowRequest(token, "materialize", {
            ...params,
            expected_sha256: "A".repeat(64),
        }),
    );
    assert.throws(() =>
        privateWorkflowRequest(token, "materialize", {
            ...params,
            path: "D:\\private.hwpx",
        }),
    );
});

test("workflow envelopes bind results to each exact request", () => {
    const materialize = {
        workspace_id: "primary",
        operation_id: "operation-01",
        slot: "candidate",
        fixture_id: "fixture-01",
        expected_sha256: "a".repeat(64),
    };
    assert.deepEqual(
        validateWorkflowEnvelope(
            {
                protocol_version: WORKFLOW_PROTOCOL,
                request_id: "mcp-workflow-materialize",
                ok: true,
                result: {
                    workspace_id: "primary",
                    operation_id: "operation-01",
                    slot: "candidate",
                    sha256: "a".repeat(64),
                    size_bytes: 17,
                },
            },
            "materialize",
            materialize,
        ),
        {
            workspace_id: "primary",
            operation_id: "operation-01",
            slot: "candidate",
            sha256: "a".repeat(64),
            size_bytes: 17,
        },
    );
    const publish = {
        workspace_id: "primary",
        operation_id: "operation-01",
        output_id: "result-01",
        expected_sha256: "b".repeat(64),
    };
    assert.throws(() =>
        validateWorkflowEnvelope(
            {
                protocol_version: WORKFLOW_PROTOCOL,
                request_id: "mcp-workflow-publish",
                ok: true,
                result: {
                    workspace_id: "primary",
                    operation_id: "operation-01",
                    output_id: "other",
                    sha256: "b".repeat(64),
                    size_bytes: 17,
                },
            },
            "publish",
            publish,
        ),
    );
});

test("diff consistency and Git non-execution are mandatory", () => {
    const diff = {
        workspace_id: "primary",
        operation_id: "operation-01",
    };
    const inconsistent = {
        protocol_version: WORKFLOW_PROTOCOL,
        request_id: "mcp-workflow-diff",
        ok: true,
        result: {
            workspace_id: "primary",
            operation_id: "operation-01",
            identical: true,
            source: { sha256: "a".repeat(64), size_bytes: 4 },
            candidate: { sha256: "b".repeat(64), size_bytes: 4 },
        },
    };
    assert.throws(() => validateWorkflowEnvelope(inconsistent, "diff", diff));

    const commit = {
        workspace_id: "primary",
        output_id: "result-01",
        expected_sha256: "b".repeat(64),
        message: "Publish verified HWPX",
    };
    const envelope = {
        protocol_version: WORKFLOW_PROTOCOL,
        request_id: "mcp-workflow-prepare_git_commit",
        ok: true,
        result: {
            workspace_id: "primary",
            output_id: "result-01",
            output_pathspec: "output/result-01.hwpx",
            expected_output_sha256: "b".repeat(64),
            expected_head: "c".repeat(40),
            message: "Publish verified HWPX",
            executed: false,
        },
    };
    const plan = validateWorkflowEnvelope(
        envelope,
        "prepare_git_commit",
        commit,
    ) as GitCommitPlanResult;
    assert.equal(plan.executed, false);
    envelope.result.executed = true;
    assert.throws(() =>
        validateWorkflowEnvelope(envelope, "prepare_git_commit", commit),
    );
});

test("approval preparation is path-free, exact, and protocol-v3 bound", () => {
    const params = {
        workspace_id: "primary",
        operation_id: "operation-02",
        output_id: "result-01",
        expected_sha256: "b".repeat(64),
        message: "Publish verified HWPX",
    };
    assert.deepEqual(privateApprovalRequest(token, params), {
        protocol_version: APPROVAL_PROTOCOL,
        request_id: "mcp-approval-prepare_git_commit_approval",
        session_token: token,
        method: "prepare_git_commit_approval",
        params,
    });
    assert.throws(() =>
        privateApprovalRequest(token, { ...params, path: "D:\\private.hwpx" }),
    );
    assert.throws(() =>
        privateApprovalRequest(token, {
            ...params,
            expected_sha256: "B".repeat(64),
        }),
    );

    const envelope = {
        protocol_version: APPROVAL_PROTOCOL,
        request_id: "mcp-approval-prepare_git_commit_approval",
        ok: true,
        result: {
            workspace_id: "primary",
            operation_id: "operation-02",
            output_id: "result-01",
            output_pathspec: "output/result-01.hwpx",
            expected_output_sha256: "b".repeat(64),
            expected_head: "c".repeat(40),
            expected_head_reference: "refs/heads/main",
            message: "Publish verified HWPX",
            approval: {
                effect: "git_commit",
                target_sha256: "d".repeat(64),
                plan_sha256: "e".repeat(64),
            },
            executed: false,
        },
    };
    assert.equal(
        validateApprovalEnvelope(envelope, params).approval.effect,
        "git_commit",
    );
    envelope.result.expected_head_reference = "refs/heads/feature.LOCK";
    assert.throws(() => validateApprovalEnvelope(envelope, params));
});

test("effect request and result require the exact protocol-v4 binding", () => {
    const params = {
        workspace_id: "primary",
        operation_id: "operation-02",
        output_id: "result-01",
        expected_sha256: "b".repeat(64),
        message: "Publish verified HWPX",
        actor_sha256: "a".repeat(64),
        tenant_sha256: "f".repeat(64),
        requested_at_unix_seconds: 100,
        confirmation_token: "confirm_v1.payload.signature",
    };
    assert.deepEqual(privateEffectRequest(token, params), {
        protocol_version: EFFECT_PROTOCOL,
        request_id: "mcp-effect-execute_git_commit",
        session_token: token,
        method: "execute_git_commit",
        params,
    });
    assert.throws(() =>
        privateEffectRequest(token, {
            ...params,
            confirmation_token: "not-a-confirmation",
        }),
    );
    assert.throws(() =>
        privateEffectRequest(token, { ...params, extra: "invented" }),
    );

    const envelope = {
        protocol_version: EFFECT_PROTOCOL,
        request_id: "mcp-effect-execute_git_commit",
        ok: true,
        result: {
            workspace_id: "primary",
            operation_id: "operation-02",
            output_id: "result-01",
            commit_oid: "d".repeat(40),
            previous_head: "c".repeat(40),
            updated_reference: "refs/heads/main",
            output_sha256: "b".repeat(64),
            target_sha256: "e".repeat(64),
            plan_sha256: "f".repeat(64),
            approved_at_unix_seconds: 101,
            index_synchronized: true,
            executed: true,
        },
    };
    assert.equal(validateEffectEnvelope(envelope, params).executed, true);
    envelope.result.operation_id = "other-operation";
    assert.throws(() => validateEffectEnvelope(envelope, params));
    envelope.result.operation_id = "operation-02";
    const leaked = structuredClone(envelope) as Record<string, unknown>;
    (leaked.result as Record<string, unknown>).confirmation_token =
        params.confirmation_token;
    assert.throws(() => validateEffectEnvelope(leaked, params));
});

test("all seven tool names are fixed and distinct", () => {
    assert.deepEqual(
        [
            TOOL_NAME,
            MATERIALIZE_TOOL_NAME,
            DIFF_TOOL_NAME,
            PUBLISH_TOOL_NAME,
            PREPARE_COMMIT_TOOL_NAME,
            PREPARE_APPROVAL_TOOL_NAME,
            EXECUTE_COMMIT_TOOL_NAME,
        ],
        [
            "local_companion_health",
            "local_companion_materialize",
            "local_companion_diff",
            "local_companion_publish",
            "local_companion_prepare_git_commit",
            "local_companion_prepare_git_commit_approval",
            "local_companion_execute_git_commit",
        ],
    );
});
