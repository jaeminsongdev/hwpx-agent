"""Distinct run007 using the whole qualified run006 implementation.

원 run006 소스와 기록은 보존한다. 실행 identity와 새 산출물 위치만
명시적으로 투영하고, 초기 qualified 입력 읽기 및 독립 체커를 유지한다.
"""
import argparse
import json
from pathlib import Path
import re
import sys
from types import FunctionType
import flat_current_queue_envelope_runtime_v25 as old

SELF = "tools/p09/case160_run007_controller.py"
TEST = "tools/p09/tests/test_case160_run007_controller.py"
DATA = "implementation/p09/evidence/p09-361-case160-envelope-controller-data047.v1.json"
QUAL = "implementation/p09/evidence/p09-361-case160-run007-controller-r390.v1.json"
PREFLIGHT = "implementation/p09/evidence/p09-361-case160-envelope-controller-preflight046.v1.json"
CONFIG = "implementation/p09/evidence/p09-361-case160-run007-graph-config-r388.v1.json"
MANIFEST_PATH = "implementation/p09/evidence/p09-361-case160-source-manifest033.v8.json"
CAPSULE_PATH = "implementation/p09/evidence/p09-361-case160-worker-policy-capsule010.compact.v1.json"
ROOT = "implementation/p09/evidence/p09-361-case160-current-runtime-run007.v1.json"
TASK = "case160-current-r007-tests"
QUAL_STATE = "PASS_RUN007_CONTROLLER_CONNECTION_NOT_WHOLE_PREFLIGHT_NATIVE_OR_GO"
SCHEMA = "hwpx-agent.p09-case160-run007-controller/v1"
SOURCE_PIN = dict(path="tools/p09/case160_attempt_controller.py", bytes=16064,
    sha256="e9b0dc870cd25a65a8b5f5ba1b0dd8195cf08c8f9f36c59185a9cdf0592a5613")
TEST_PIN = dict(path="tools/p09/tests/test_case160_attempt_controller.py", bytes=2370,
    sha256="f9f5fd96693a9758a1d6c365d5adf7a089efa729ebc7cc61e420aaf6f3970d49")
names, SOURCE_PROOF = old.namespace_bundle.load(old.c.ROOT, [SOURCE_PIN],
    {"flat_current_queue_envelope_runtime_v25":old})
original = names.case160_attempt_controller
base = original.base
a = old.a
LEGACY_PINS = original.LEGACY_PINS
projected = original.projected

MAPPING = {6:7, 27:31, original.TASK:TASK,
    "hwpx-agent.p09-run006-graph-config/v1":"hwpx-agent.p09-run007-graph-config/v1",
    "-envelope-controller-preflight044.v1.json":"-envelope-controller-preflight046.v1.json",
    "tools.p09.tests.test_case160_attempt_controller":"tools.p09.tests.test_case160_run007_controller"}
env = base.clone_family(original.read_config.__globals__, dict(SELF=SELF, TEST=TEST, DATA=DATA,
    QUAL=QUAL, PREFLIGHT=PREFLIGHT, CONFIG=CONFIG, MANIFEST_PATH=MANIFEST_PATH,
    CAPSULE_PATH=CAPSULE_PATH, ROOT=ROOT, TASK=TASK, QUAL_STATE=QUAL_STATE, SCHEMA=SCHEMA))
for name in ("connect_graph", "validate_config", "read_config", "publish", "prepare_artifacts", "initialize", "test_namespace"):
    env[name] = projected(getattr(original, name), env, MAPPING)
globals().update({name:env[name] for name in ("connect_graph", "validate_config", "read_config", "publish", "prepare_artifacts", "test_namespace")})
initialize_projection = env["initialize"]


def initialize():
    current = initialize_projection()
    # The preserved source's ordinary initializer read these original declarations.
    # They remain actual declared inputs rather than being hidden from Native scope.
    config, config_pin = original.read_config()
    inherited = [SOURCE_PIN, TEST_PIN, config_pin, config["manifest_pin"], config["capsule_pin"]]
    family = current.binding.__globals__
    family["RAW_PINS"] = family["RAW_PINS"]+inherited
    family["SOURCE_PROOFS"] = family["SOURCE_PROOFS"]+SOURCE_PROOF
    current.RAW_PINS = family["RAW_PINS"]
    current.SOURCE_PROOFS = family["SOURCE_PROOFS"]
    return current


# test_namespace must initialize the same complete source-declared connection.
env["initialize"] = initialize
CURRENT = initialize() if (old.c.ROOT/CONFIG).is_file() else None


def select_preflight(current, attempt):
    """Closed metadata selection; no automatic retry or source edits."""
    a.require(type(attempt) is int and 2 <= attempt <= 8, "CLOSED_RUN007_PREFLIGHT_ATTEMPT")
    path = f"implementation/p09/evidence/p09-361-case160-envelope-controller-preflight{44+attempt:03}.v1.json"
    suffix = "-envelope-controller-preflight"+f"{44+attempt:03}.v1.json"
    before = current.after
    fn = current._env["preflight_projection"]
    a.require(sum(type(v) is str and v == before for v in fn.__code__.co_consts) == 1, "ONE_ORIGINAL_PREFLIGHT_DESTINATION")
    # project() proves that inverse metadata substitution restores every code body.
    changed = projected(fn, current._env, {before:suffix})
    family = current.binding.__globals__
    family.update(PREFLIGHT=path, after=suffix)
    current._env.update(PREFLIGHT=path, preflight_projection=changed)
    current.M.PREFLIGHT = path
    current.M.preflight_projection = changed
    current.PREFLIGHT = path
    current.after = suffix
    return path


def select_qualification(current, attempt):
    """Preserve failed CODE receipts without changing source for a retry."""
    a.require(type(attempt) is int and 1 <= attempt <= 8, "CLOSED_RUN007_QUALIFICATION_ATTEMPT")
    qual = QUAL if attempt == 1 else "implementation/p09/evidence/p09-361-case160-run007-controller-r390-run"+f"{attempt:03}.v1.json"
    data = "implementation/p09/evidence/p09-361-case160-envelope-controller-data"+f"{46+attempt:03}.v1.json"
    family = current.binding.__globals__
    family.update(QUAL=qual, DATA=data)
    current._env.update(QUAL=qual, DATA=data)
    current.M.QUAL, current.M.DATA = qual, data
    current.QUAL, current.DATA = qual, data
    current._api_env["QUAL_PATH"] = qual
    current.API.QUAL_PATH = qual
    return qual, data


def inherited_tests():
    ns, proof = old.namespace_bundle.load(old.c.ROOT, [TEST_PIN], {"case160_attempt_controller":sys.modules[__name__]})
    module = ns.test_case160_attempt_controller
    for name, fn in tuple(vars(module.Tests).items()):
        if type(fn) is FunctionType:
            setattr(module.Tests, name, projected(fn, fn.__globals__, MAPPING))
    return module, proof


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
            a.require(CURRENT is not None, "RUN007_CONFIG_REQUIRED")
            CURRENT.M.base.configure(CURRENT.M.base.task_index(sys.argv[3]))
            raise SystemExit(CURRENT.M.worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--prepare-artifacts", action="store_true")
        mode.add_argument("--qualify", action="store_true")
        mode.add_argument("--preflight", action="store_true")
        mode.add_argument("--run", type=int)
        parser.add_argument("--preflight-attempt", type=int, default=2)
        parser.add_argument("--qualification-attempt", type=int, default=1)
        args = parser.parse_args()
        if args.prepare_artifacts: raise SystemExit(prepare_artifacts())
        a.require(CURRENT is not None, "RUN007_CONFIG_REQUIRED")
        select_qualification(CURRENT, args.qualification_attempt)
        if args.qualify: raise SystemExit(CURRENT.qualify())
        select_preflight(CURRENT, args.preflight_attempt)
        CURRENT.M.base.configure(160)
        raise SystemExit(CURRENT.M.preflight() if args.preflight else CURRENT.run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        label = str(error) if isinstance(error, ValueError) and re.fullmatch("[A-Za-z0-9_]{1,160}", str(error)) else "REDACTED_RUN007_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=label)))
        raise SystemExit(2) from None
