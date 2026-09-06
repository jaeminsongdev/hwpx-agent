import assert from "node:assert/strict";
import test from "node:test";

import {
    DIFF_TOOL_NAME,
    MATERIALIZE_TOOL_NAME,
    PRIVATE_PROTOCOL,
    PREPARE_COMMIT_TOOL_NAME,
    PUBLISH_TOOL_NAME,
    TARGET_PROFILE,
    WORKFLOW_PROTOCOL,
    childEnvironment,
    parseRuntimeArguments,
    privateHealthRequest,
    privateWorkflowRequest,
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

test("workflow tool names are fixed and distinct", () => {
    assert.deepEqual(
        [
            MATERIALIZE_TOOL_NAME,
            DIFF_TOOL_NAME,
            PUBLISH_TOOL_NAME,
            PREPARE_COMMIT_TOOL_NAME,
        ],
        [
            "local_companion_materialize",
            "local_companion_diff",
            "local_companion_publish",
            "local_companion_prepare_git_commit",
        ],
    );
});
