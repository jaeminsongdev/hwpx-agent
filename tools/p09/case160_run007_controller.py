"""Bounded Native attempts using the whole qualified run006 implementation.

원 run006 소스와 기록은 보존한다. 실행 identity와 새 산출물 위치만
명시적으로 투영하고, 초기 qualified 입력 읽기 및 독립 체커를 유지한다.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from types import FunctionType


def native_attempt(argv):
    """Select once before imports; worker identity selects the same context."""
    values = []
    for index, value in enumerate(argv):
        if value == "--native-attempt":
            if index + 1 >= len(argv): raise ValueError("NATIVE_ATTEMPT_REQUIRED")
            values.append(argv[index + 1])
    if len(argv) == 3 and argv[:2] == ["--owned-worker", "--task"]:
        match = re.fullmatch(r"case160-current-r([0-9]{3})-tests", argv[2])
        if match is None: raise ValueError("EXACT_CASE160_WORKER_ATTEMPT")
        values.append(match[1])
    if len(values) > 1: raise ValueError("ONE_NATIVE_ATTEMPT")
    if not values: return 7
    value = values[0]
    if type(value) is not str or re.fullmatch(r"[0-9]{1,3}", value) is None:
        raise ValueError("TYPED_NATIVE_ATTEMPT")
    result = int(value)
    if not 7 <= result <= 14: raise ValueError("CLOSED_NATIVE_ATTEMPT")
    return result


NATIVE = native_attempt(sys.argv[1:])
import flat_current_queue_envelope_runtime_v25 as old

SELF = "tools/p09/case160_run007_controller.py"
TEST = "tools/p09/tests/test_case160_run007_controller.py"
STEM = f"implementation/p09/evidence/p09-361-case160-native{NATIVE:03}-controller-r391"
DATA = STEM+"-data001.v1.json"
QUAL = STEM+"-qualification001.v1.json"
PREFLIGHT = STEM+"-preflight002.v1.json"
# Existing run007 declarations remain immutable; later attempts get distinct pins.
CONFIG = ("implementation/p09/evidence/p09-361-case160-run007-graph-config-r388.v1.json"
    if NATIVE == 7 else STEM+"-graph-config.v1.json")
MANIFEST_PATH = f"implementation/p09/evidence/p09-361-case160-source-manifest{26+NATIVE:03}.v8.json"
CAPSULE_PATH = f"implementation/p09/evidence/p09-361-case160-worker-policy-capsule{3+NATIVE:03}.compact.v1.json"
ROOT = f"implementation/p09/evidence/p09-361-case160-current-runtime-run{NATIVE:03}.v1.json"
TASK = f"case160-current-r{NATIVE:03}-tests"
QUAL_STATE = f"PASS_RUN{NATIVE:03}_CONTROLLER_CONNECTION_NOT_WHOLE_PREFLIGHT_NATIVE_OR_GO"
SCHEMA = f"hwpx-agent.p09-case160-run{NATIVE:03}-controller/v1"
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
BOOTSTRAP_PIN = dict(path="implementation/p09/evidence/p09-361-case160-native010-bootstrap-requirements-r392-attempt002.v1.json",
    bytes=11842, sha256="ba628c316b3301d8b5165eb53af373fb966e9299af8dd8e8cc5754ec765fabfd")


def initial_requirements():
    with (old.c.ROOT/BOOTSTRAP_PIN["path"]).open("rb") as stream:
        raw = stream.read(262145)
    a.require(0 < len(raw) <= 262144, "BOUNDED_INITIAL_REQUIREMENTS")
    a.exact(dict(path=BOOTSTRAP_PIN["path"], bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
        BOOTSTRAP_PIN, "EXACT_PREPARED_INITIAL_REQUIREMENTS")
    row = json.loads(raw.decode("utf-8"), object_pairs_hook=old.base.unique)
    a.fields(row, dict(state="PREPARED_ALL50_INITIAL_REQUIREMENTS_NOT_NATIVE_OR_ORACLE_OR_ACCEPTANCE",
        bootstrap_requirement_schema="hwpx-agent.p09-case160-bootstrap-requirements/v1",
        bootstrap_required_count=50, current_candidate_scope_used_to_derive_requirements=False,
        requirement_paths_from_entire_unchanged_frozen_checker=True, cleanup_confirmed=True,
        product_or_Native_reexecuted=False, queue_acceptance_called=False), "ALL_ORIGINAL_INITIAL_REQUIREMENTS")
    a.require(row["fresh_inputs"] == row["final_fresh_hashes"] == 53, "FRESH_DECLARATION_AND_ALL50_TOOLS")
    pins = old.base.scope.pins(row["bootstrap_required_tool_pins"], 50)
    a.require(all(n.startswith("tools/p09/") for n in pins), "ONLY_DECLARED_ORIGINAL_TOOLS")
    producer = row["qualifier_source_pin"]
    old.base.scope.pins([producer], 1)
    a.exact(producer["path"], "tools/p09/qualify_case160_run004_readonly.py", "INITIAL_REQUIREMENT_PRODUCER")
    return list(pins.values()), producer


EXTRA_INITIAL_PINS, INITIAL_PRODUCER_PIN = initial_requirements()
LEGACY_PINS = LEGACY_PINS+EXTRA_INITIAL_PINS+[BOOTSTRAP_PIN, INITIAL_PRODUCER_PIN]

PREFLIGHT_SUFFIX = PREFLIGHT.removeprefix("implementation/p09/evidence/p09-361-case160")
MAPPING = {6:NATIVE, 27:32, original.TASK:TASK,
    "hwpx-agent.p09-run006-graph-config/v1":f"hwpx-agent.p09-run{NATIVE:03}-graph-config/v1",
    "-envelope-controller-preflight044.v1.json":PREFLIGHT_SUFFIX,
    "tools.p09.tests.test_case160_attempt_controller":"tools.p09.tests.test_case160_run007_controller"}
env = base.clone_family(original.read_config.__globals__, dict(SELF=SELF, TEST=TEST, DATA=DATA,
    QUAL=QUAL, PREFLIGHT=PREFLIGHT, CONFIG=CONFIG, MANIFEST_PATH=MANIFEST_PATH,
    CAPSULE_PATH=CAPSULE_PATH, ROOT=ROOT, TASK=TASK, QUAL_STATE=QUAL_STATE, SCHEMA=SCHEMA,
    LEGACY_PINS=LEGACY_PINS))
for name in ("connect_graph", "validate_config", "read_config", "publish", "prepare_artifacts", "initialize", "test_namespace"):
    # test_namespace already contains 31 as the inherited reader-count value,
    # not the suite size. Applying 27->31 there makes the inverse ambiguous.
    # Keep that independent count unchanged; initialize alone builds the suite.
    mapping = {k:v for k,v in MAPPING.items() if name != "test_namespace" or k != 27}
    env[name] = projected(getattr(original, name), env, mapping)
globals().update({name:env[name] for name in ("connect_graph", "validate_config", "read_config", "publish", "prepare_artifacts", "test_namespace")})
initialize_projection = env["initialize"]


def initialize():
    current = initialize_projection()
    # The preserved source's ordinary initializer read these original declarations.
    # They remain actual declared inputs rather than being hidden from Native scope.
    config, config_pin = original.read_config()
    inherited = [SOURCE_PIN, TEST_PIN, config_pin, config["manifest_pin"], config["capsule_pin"],
        BOOTSTRAP_PIN, INITIAL_PRODUCER_PIN]+EXTRA_INITIAL_PINS
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
    path = STEM+f"-preflight{attempt:03}.v1.json"
    suffix = path.removeprefix("implementation/p09/evidence/p09-361-case160")
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
    qual = STEM+f"-qualification{attempt:03}.v1.json"
    data = STEM+f"-data{attempt:03}.v1.json"
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
        parser.add_argument("--native-attempt", type=int, default=7)
        args = parser.parse_args()
        a.exact(args.native_attempt, NATIVE, "ONE_NATIVE_CONTEXT_BEFORE_IMPORTS")
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
