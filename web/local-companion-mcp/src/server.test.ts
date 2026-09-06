import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import test from "node:test";

import {
    APPROVAL_PROTOCOL,
    CONFIRM_COMMIT_TOOL_NAME,
    DIFF_TOOL_NAME,
    EFFECT_PROTOCOL,
    GIT_APPROVAL_RESOURCE_URI,
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
    confirmAndExecuteGitCommit,
    loadConfirmationIdentity,
    mintGitConfirmation,
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
import type {
    GitApprovalPlanResult,
    GitCommitEffectResult,
    GitCommitPlanResult,
    RuntimeConfig,
} from "./server.js";

const token = "A".repeat(43);
const daemon = "D:\\product\\local-companion-daemon.exe";
const config = "D:\\runtime\\config.json";
const widget = "D:\\runtime\\git-approval-widget-v1.html";
const gitProgram = "C:\\Program Files\\Git\\cmd\\git.exe";
const approvalStateRoot = "D:\\runtime\\approval-state";

function runtimeConfig(): RuntimeConfig {
    return {
        daemonPath: daemon,
        configPath: config,
        widgetPath: widget,
        widgetHtml: '<!doctype html><div id="root"></div>',
        gitProgram,
        approvalStateRoot,
        approvalSecret: Buffer.alloc(32, 7),
        actorSha256: "a".repeat(64),
        tenantSha256: "b".repeat(64),
    };
}

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

test("runtime arguments require exact absolute daemon, config and widget paths", () => {
    assert.deepEqual(
        parseRuntimeArguments([
            "--daemon",
            daemon,
            "--config",
            config,
            "--widget",
            widget,
            "--git",
            gitProgram,
            "--approval-state",
            approvalStateRoot,
        ]),
        {
            daemonPath: daemon,
            configPath: config,
            widgetPath: widget,
            gitProgram,
            approvalStateRoot,
        },
    );
    assert.throws(() => parseRuntimeArguments([]));
    assert.throws(() =>
        parseRuntimeArguments(["--config", config, "--daemon", daemon]),
    );
    assert.throws(() =>
        parseRuntimeArguments([
            "--daemon",
            "relative.exe",
            "--config",
            config,
            "--widget",
            widget,
            "--git",
            gitProgram,
            "--approval-state",
            approvalStateRoot,
        ]),
    );
    assert.throws(() =>
        parseRuntimeArguments([
            "--daemon",
            daemon,
            "--config",
            config,
            "--widget",
            widget,
            "--git",
            gitProgram,
            "--approval-state",
            approvalStateRoot,
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
        SHOULD_NOT_PASS: "private",
    };
    assert.deepEqual(childEffectEnvironment(token, runtimeConfig(), source), {
        HWPX_AGENT_LOCAL_SESSION_TOKEN: token,
        SystemRoot: "C:\\Windows",
        WINDIR: "C:\\Windows",
        HWPX_AGENT_GIT_PROGRAM: gitProgram,
        HWPX_AGENT_APPROVAL_STATE_ROOT: approvalStateRoot,
        HWPX_AGENT_APPROVAL_SECRET: Buffer.alloc(32, 7).toString("base64url"),
        TEMP: approvalStateRoot,
        TMP: approvalStateRoot,
    });
    assert.throws(() =>
        childEffectEnvironment(token, {
            ...runtimeConfig(),
            approvalSecret: Buffer.alloc(1),
        }),
    );
    assert.throws(() =>
        childEffectEnvironment(token, {
            ...runtimeConfig(),
            gitProgram: "git.exe",
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

test("trusted identity and token minting are exact, short-lived and HMAC bound", () => {
    const identity = loadConfirmationIdentity(runtimeConfig());
    const plan: GitApprovalPlanResult = {
        workspace_id: "primary",
        operation_id: "op_widget_01",
        output_id: "result_01",
        output_pathspec: "output/result_01.hwpx",
        expected_output_sha256: "c".repeat(64),
        expected_head: "d".repeat(40),
        expected_head_reference: "refs/heads/main",
        message: "Publish verified HWPX",
        approval: {
            effect: "git_commit",
            target_sha256: "e".repeat(64),
            plan_sha256: "f".repeat(64),
        },
        executed: false,
    };
    const confirmation = mintGitConfirmation(plan, identity, 100);
    const [prefix, encodedPayload, encodedSignature] = confirmation.split(".");
    assert.equal(prefix, "confirm_v1");
    const payload = Buffer.from(encodedPayload!, "base64url");
    const parsed = JSON.parse(payload.toString("utf8")) as Record<
        string,
        unknown
    >;
    assert.equal(parsed.operation_id, "op_widget_01");
    assert.equal(parsed.issued_at_unix_seconds, 100);
    assert.equal(parsed.expires_at_unix_seconds, 160);
    assert.match(String(parsed.token_id), /^cnf_[0-9a-f]{32}$/);
    assert.equal(parsed.user_confirmed, true);
    assert.equal(
        encodedSignature,
        createHmac("sha256", Buffer.alloc(32, 7))
            .update(payload)
            .digest("base64url"),
    );
    payload.fill(0);
    identity.secret.fill(0);
    assert.throws(() =>
        loadConfirmationIdentity({
            ...runtimeConfig(),
            approvalSecret: Buffer.alloc(1),
        }),
    );
});

test("app confirmation revalidates the displayed plan and never accepts a caller token", async () => {
    const runtime = runtimeConfig();
    const plan: GitApprovalPlanResult = {
        workspace_id: "primary",
        operation_id: "op_widget_01",
        output_id: "result_01",
        output_pathspec: "output/result_01.hwpx",
        expected_output_sha256: "c".repeat(64),
        expected_head: "d".repeat(40),
        expected_head_reference: "refs/heads/main",
        message: "Publish verified HWPX",
        approval: {
            effect: "git_commit",
            target_sha256: "e".repeat(64),
            plan_sha256: "f".repeat(64),
        },
        executed: false,
    };
    const confirmationParams = {
        workspace_id: plan.workspace_id,
        operation_id: plan.operation_id,
        output_id: plan.output_id,
        expected_sha256: plan.expected_output_sha256,
        message: plan.message,
        expected_head: plan.expected_head,
        expected_head_reference: plan.expected_head_reference,
        target_sha256: plan.approval.target_sha256,
        plan_sha256: plan.approval.plan_sha256,
    };
    let effectParams: Record<string, unknown> | null = null;
    const result = await confirmAndExecuteGitCommit(
        runtime,
        confirmationParams,
        async () => plan,
        async (_runtime, params) => {
            effectParams = params;
            return {
                workspace_id: plan.workspace_id,
                operation_id: plan.operation_id,
                output_id: plan.output_id,
                commit_oid: "1".repeat(40),
                previous_head: plan.expected_head,
                updated_reference: plan.expected_head_reference,
                output_sha256: plan.expected_output_sha256,
                target_sha256: plan.approval.target_sha256,
                plan_sha256: plan.approval.plan_sha256,
                approved_at_unix_seconds: 100,
                index_synchronized: true,
                executed: true,
            } satisfies GitCommitEffectResult;
        },
        () => 100,
    );
    assert.equal(result.executed, true);
    assert.match(
        String(effectParams!.confirmation_token),
        /^confirm_v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/,
    );
    assert.equal(effectParams!.actor_sha256, "a".repeat(64));
    assert.equal(effectParams!.tenant_sha256, "b".repeat(64));
    await assert.rejects(() =>
        confirmAndExecuteGitCommit(
            runtime,
            { ...confirmationParams, confirmation_token: "caller-token" },
            async () => plan,
            async () => result,
            () => 100,
        ),
    );
    await assert.rejects(() =>
        confirmAndExecuteGitCommit(
            runtime,
            confirmationParams,
            async () => ({ ...plan, expected_head: "2".repeat(40) }),
            async () => result,
            () => 100,
        ),
    );
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
            CONFIRM_COMMIT_TOOL_NAME,
        ],
        [
            "local_companion_health",
            "local_companion_materialize",
            "local_companion_diff",
            "local_companion_publish",
            "local_companion_prepare_git_commit",
            "local_companion_prepare_git_commit_approval",
            "local_companion_confirm_and_execute_git_commit",
        ],
    );
    assert.equal(
        GIT_APPROVAL_RESOURCE_URI,
        "ui://hwpx-agent/local-git-approval/v1.html",
    );
});
