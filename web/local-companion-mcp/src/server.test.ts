import assert from "node:assert/strict";
import test from "node:test";

import {
    PRIVATE_PROTOCOL,
    TARGET_PROFILE,
    childEnvironment,
    parseRuntimeArguments,
    privateHealthRequest,
    validateHealthEnvelope,
} from "./server.js";

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
