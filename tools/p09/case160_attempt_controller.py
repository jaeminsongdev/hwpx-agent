"""Case160 attempt controller; preserve prior receipts and the complete checker.

기존 실행 코드 전체를 유지하고 identity만 바꾼다. 초기 qualified pin
읽기를 복원하며, 새 입력 선언·wire·CODE·preflight가 없으면 실행하지 않는다.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF = "tools/p09/case160_attempt_controller.py"
TEST = "tools/p09/tests/test_case160_attempt_controller.py"
DATA = "implementation/p09/evidence/p09-361-case160-envelope-controller-data044.v1.json"
QUAL = "implementation/p09/evidence/p09-361-case160-run006-controller-r376-run002.v1.json"
PREFLIGHT = "implementation/p09/evidence/p09-361-case160-envelope-controller-preflight044.v1.json"
CONFIG = "implementation/p09/evidence/p09-361-case160-run006-graph-config-r376.v1.json"
MANIFEST_PATH = "implementation/p09/evidence/p09-361-case160-source-manifest032.v8.json"
CAPSULE_PATH = "implementation/p09/evidence/p09-361-case160-worker-policy-capsule009.compact.v1.json"
ROOT = "implementation/p09/evidence/p09-361-case160-current-runtime-run006.v1.json"
TASK = "case160-current-r006-tests"
QUAL_STATE = "PASS_RUN006_CONTROLLER_CONNECTION_NOT_WHOLE_PREFLIGHT_NATIVE_OR_GO"
SCHEMA = "hwpx-agent.p09-case160-run006-controller/v1"
BASE_PIN = dict(path="tools/p09/case160_run004_controller.py", bytes=23669,
    sha256="98df79bf8de03390d9b9fba9f7cfcad5e30ddc646213cf7188fb2bf35827705f")
BASE_TEST_PIN = dict(path="tools/p09/tests/test_case160_run004_controller.py", bytes=6867,
    sha256="4ff102281c9566de85bbd05d9ceefc66774af63a1f5aa3e2e5bc619dcd56293d")
raw, BASE_PROOF = old.namespace_bundle.load(old.c.ROOT, [BASE_PIN],
    {"flat_current_queue_envelope_runtime_v25":old})
base = raw.case160_run004_controller
a = old.a
LEGACY_PINS = a.CODE_PINS + list(a.native.SOURCES)


def project(code, mapping):
    def value(x):
        if type(x) is CodeType: return project(x, mapping)
        if type(x) is tuple: return tuple(value(v) for v in x)
        return mapping.get(x, x) if type(x) in (int, str) else x
    return code.replace(co_consts=tuple(value(x) for x in code.co_consts))


def projected(fn, env, mapping):
    code = project(fn.__code__, mapping)
    inverse = {v:k for k,v in mapping.items()}
    a.require(project(code, inverse) == fn.__code__, "RUN005_ENTIRE_BODY_METADATA_INVERSE")
    result = FunctionType(code, env, argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result


def connect_graph(graph, bound):
    factory = base.NEXT.successor_runtime_graph_v7.connect
    return projected(factory, dict(factory.__globals__, TASK=TASK), {})(graph, bound)


def validate_config(row):
    a.require(type(row) is dict and set(row) == {"schema_version", "index", "before", "physical_product_run",
        "manifest_pin", "capsule_pin"}, "CLOSED_RUN005_GRAPH_CONFIG")
    a.fields(row, dict(schema_version="hwpx-agent.p09-run006-graph-config/v1", index=160, before=153,
        physical_product_run=6), "ONLY_EXACT_RUN005_CONFIG")
    a.exact(row["manifest_pin"]["path"], MANIFEST_PATH, "ONLY_MANIFEST031")
    a.exact(row["capsule_pin"]["path"], CAPSULE_PATH, "ONLY_CAPSULE008")
    old.base.scope.pins([row["manifest_pin"], row["capsule_pin"]], 2)
    a.require(row["manifest_pin"]["bytes"] <= 2048 and row["capsule_pin"]["bytes"] <= 16384, "ORIGINAL_WIRE_BOUNDS")
    return row


def read_config():
    path = old.c.ROOT/CONFIG
    with path.open("rb") as stream: data = stream.read(2049)
    a.require(0 < len(data) <= 2048, "BOUNDED_CONFIG_BYTES")
    row = validate_config(json.loads(data.decode("utf-8"), object_pairs_hook=old.base.unique))
    return row, dict(path=CONFIG, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def publish(path, raw, checkpoint):
    for parent in (path.parent, *path.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DIRECT_RUN005_ANCESTORS")
        if parent == old.c.ROOT: break
    pacer = old._namespaces.runtime_envelope_physical_io_v1.bytes_policy.OwnedPacer()
    pacer.select(path.relative_to(old.c.ROOT).as_posix())
    with path.open("xb") as stream:
        for offset in range(0, len(raw), 65536):
            block = raw[offset:offset+65536]; pacer.reserve(checkpoint)
            count = stream.write(block); a.exact(count, len(block), "ALL_RUN005_METADATA_BYTES"); pacer.refund(count)
        stream.flush(); os.fsync(stream.fileno())
    return dict(path=path.relative_to(old.c.ROOT).as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def prepare_artifacts():
    guard = base.FIRST.terminal_metadata_pressure_v1.guard_type(base.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    paths = [old.c.ROOT/p for p in (MANIFEST_PATH, CAPSULE_PATH, CONFIG)]
    a.require(all(not p.exists() and not p.is_symlink() for p in paths), "EXCLUSIVE_RUN005_ARTIFACTS")
    try:
        guard.acquire(); old.base.configure(160)
        q = a.AcceptanceReader(old.c.ROOT, guard.check)
        source = q.pin(SELF); a.exact(q.pin(BASE_PIN["path"]), BASE_PIN, "EXACT_PRESERVED_RUN004_CONTROLLER")
        graph, proof = base.bootstrap.load(old, q.checkpoint)
        for p in proof["reader_source_pins"]: a.exact(q.pin(p["path"]), p, "EXACT_ORIGINAL_BOUNDED_GRAPH")
        original = a.read_exact(q, base.MANIFEST)
        row = dict(original, physical_product_run=6)
        manifest_module = base.NEXT.runtime_successor_manifest_v8
        check = projected(manifest_module.validate, manifest_module.validate.__globals__, {4:6})
        check(row, a, base.bootstrap.original.MANIFEST)
        raw_manifest = (json.dumps(row, ensure_ascii=True, indent=2, allow_nan=False)+"\n").encode("utf-8")
        manifest_pin = dict(path=MANIFEST_PATH, bytes=len(raw_manifest), sha256=hashlib.sha256(raw_manifest).hexdigest())
        bound = graph.binding_module.Binding(graph.binding.descriptors(), manifest_pin, next_case=160)
        changed, _ = connect_graph(graph, bound)
        successor = base.predecessor._env["current_binding"].successor
        wire, capsule_pin = changed.worker.encode(bound, successor.AUTHORITY, successor.ROOT, q.checkpoint)
        decoded, _ = changed.worker.decode(wire, capsule_pin, q.checkpoint)
        a.exact(decoded.descriptors(), bound.descriptors(), "ALL34_RUN005_WIRE_DESCRIPTORS")
        a.exact(dict(decoded.manifest_pin), manifest_pin, "ACTUAL_RUN005_MANIFEST_WIRE")
        capsule_pin = dict(path=CAPSULE_PATH, **capsule_pin)
        config = validate_config(dict(schema_version="hwpx-agent.p09-run006-graph-config/v1", index=160,
            before=153, physical_product_run=6, manifest_pin=manifest_pin, capsule_pin=capsule_pin))
        q.finish(); guard.check(force=True)
        publish(paths[0], raw_manifest, guard.check)
        publish(paths[1], wire, guard.check)
        publish(paths[2], (json.dumps(config, ensure_ascii=True, indent=2, allow_nan=False)+"\n").encode("utf-8"), guard.check)
        print(json.dumps(dict(state="PREPARED_RUN006_DECLARATION_AND_WIRE_NOT_PREFLIGHT_OR_GO", source_pairs=34,
            capsule_bytes=len(wire), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)))
    finally:
        guard.close(); a.require(guard.cleanup, "RUN005_ARTIFACT_CLEANUP")
    return 0


def initialize():
    config, config_pin = read_config()
    manifest_pin = config["manifest_pin"]; capsule_pin = config["capsule_pin"]
    manifest_env = dict(base.NEXT.runtime_successor_manifest_v8.validate.__globals__, PATH=MANIFEST_PATH)
    manifest_env["validate"] = projected(base.NEXT.runtime_successor_manifest_v8.validate, manifest_env, {4:6})
    manifest_env["load"] = projected(base.NEXT.runtime_successor_manifest_v8.load, manifest_env, {})
    manifest = NS(**manifest_env)

    def bounded(m, checkpoint):
        captured = []
        original = base.bootstrap.original
        class Reader(original.original.Reader):
            def __init__(self, *args):
                super().__init__(*args)
                self.allowed.update({p["path"]:dict(p) for p in (config_pin, manifest_pin, capsule_pin)})
                captured.append(self)
        old_base = NS(**{**vars(original.original), "Reader":Reader})
        old_boot = NS(**{**vars(original), "original":old_base})
        execute = projected(base.bootstrap.load, dict(base.bootstrap.load.__globals__, original=old_boot), {})
        graph, prefix = execute(m, checkpoint)
        a.require(len(captured) == 1, "ONE_RUN005_BOUNDED_READER")
        q = captured[0]
        a.exact(q.json(CONFIG), config, "CURRENT_CONFIG_EQUALS_QUALIFIED_DECLARATION")
        row = q.json(MANIFEST_PATH); manifest.validate(row, m.a, original.MANIFEST)
        a.exact(row["extra_prior_producer_pin"], base.bootstrap.PRODUCER, "REAL_ALL34_PRODUCER_PRESERVED")
        bound = graph.binding_module.Binding(graph.binding.descriptors(), manifest_pin, next_case=160)
        current, linked = connect_graph(graph, bound)
        actual, wire = q._read(CAPSULE_PATH, parse=True); q._bind(CAPSULE_PATH, actual)
        a.exact(actual, capsule_pin, "ACTUAL_RUN005_CAPSULE_BYTES")
        decoded, decoder = current.worker.decode(bytes(wire), {k:capsule_pin[k] for k in ("bytes", "sha256")}, checkpoint)
        a.exact(decoded.descriptors(), bound.descriptors(), "ALL34_BOUNDED_RUN005_DESCRIPTORS")
        a.exact(dict(decoded.manifest_pin), manifest_pin, "ACTUAL031_MANIFEST")
        return current, dict(prefix, bounded_reader_reads=q.reads, bounded_reader_bytes=q.bytes_read,
            reader_source_pins=list(q.snapshots.values()), run005_graph_proof=linked, run005_decoder_proof=decoder,
            current_controller_engine_worker_Native_or_GO_qualified=False)

    bootstrap = NS(**{**vars(base.bootstrap), "MANIFEST":manifest_pin, "CAPSULE":capsule_pin, "load":bounded})
    binding_env = dict(base.binding_module.bind.__globals__, bootstrap=bootstrap, manifest=manifest)
    binding_module = NS(**{**vars(base.binding_module), "bootstrap":bootstrap,
        "bind":projected(base.binding_module.bind, binding_env, {base.attempt.TASK:TASK})})
    attempt_env = dict(base.attempt.identity.__globals__, PHYSICAL_RUN=6, TASK=TASK, ROOT=ROOT)
    identity = projected(base.attempt.identity, attempt_env, {4:6})
    attempt_env["identity"] = identity
    template = projected(base.attempt.connect_template, attempt_env, {4:6})
    attempt = NS(**{**vars(base.attempt), "identity":identity, "connect_template":template,
        "PHYSICAL_RUN":6, "TASK":TASK, "ROOT":ROOT})
    distinct_template, retry, attempt_proof = attempt.connect_template(old.prior)
    prior = NS(**{**vars(old.prior), "template":distinct_template})
    module_env = base.clone_family(base.binding.__globals__, {})
    module_env.update(SELF=SELF, TEST=TEST, DATA=DATA, QUAL=QUAL, PREFLIGHT=PREFLIGHT, QUAL_STATE=QUAL_STATE,
        SCHEMA=SCHEMA, RAW_PINS=base.RAW_PINS+[BASE_PIN, BASE_TEST_PIN, config_pin], SOURCE_PROOFS=base.SOURCE_PROOFS+BASE_PROOF,
        MANIFEST=manifest_pin, CAPSULE=capsule_pin, bootstrap=bootstrap, binding_module=binding_module,
        prior=prior, RETRY=retry, attempt=attempt, ATTEMPT_PROOF=attempt_proof, CONFIG_PIN=config_pin)
    for name in ("validate_data", "own_inputs", "run_owned"):
        module_env[name] = projected(getattr(base, name), module_env, {4:6, 22:27})
    module_env["qualify"] = projected(base.qualify, module_env,
        {4:6, 22:27, "tools.p09.tests.test_case160_run004_controller":"tools.p09.tests.test_case160_attempt_controller"})
    env = base.clone_family(base._env, dict(SELF=SELF, TEST=TEST, DATA=DATA, QUAL=QUAL, PREFLIGHT=PREFLIGHT,
        QUAL_STATE=QUAL_STATE, SCHEMA=SCHEMA, bootstrap=bootstrap, CAPSULE=capsule_pin, MANIFEST=manifest_pin,
        RETRY=retry, prior=prior, _graph=None, _checkpoint=None, _execution_requested=False, PARENT_STATES=[]))
    module_env["_env"] = env

    # These exact qualified pins must be actually read before bootstrap returns.
    raw_own = module_env["own_inputs"]
    def qualified_bootstrap(q):
        for p in LEGACY_PINS: a.exact(q.pin(p["path"]), p, "ALL_ORIGINAL_BOOTSTRAP_CONTROLLER_PINS")
        return raw_own(q)
    owned, counts = old.admission_once.connect(qualified_bootstrap)
    module_env.update(owned=owned, ADMISSION_COUNTS=counts)
    env.update(own_inputs=owned, validate_data=module_env["validate_data"], binding=module_env["binding"])
    env["worker"] = projected(base._env["worker"], env, {base.attempt.TASK:TASK})
    env["preflight_projection"] = projected(base._env["preflight_projection"], env,
        {"-envelope-controller-preflight041.v1.json":"-envelope-controller-preflight044.v1.json"})
    source_projection = prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,
        root_path=retry.root_path, validate_candidate=env["validate_candidate"], runtime=NS(context=env["context"]))
    source = NS(**{**vars(prior.CURRENT_SOURCE), "prepare_projection":source_projection, "validate_candidate":env["validate_candidate"]})
    env["CURRENT_SOURCE"] = source
    api_env = base.clone_family(base._api_env, dict(SELF=SELF, TEST=TEST, FILES=(SELF, TEST), QUAL_PATH=QUAL,
        source=source, own_inputs=owned, validator=env["validator"], context=env["context"], template=env["template"],
        binding=module_env["binding"], binding_attempt=env["binding_attempt"]))
    api = NS(**api_env); env["API"] = api
    module_env.update(API=api, M=NS(**env), source=source, _api_env=api_env,
        after="-envelope-controller-preflight044.v1.json")
    api.prepare = module_env["prepare_candidate"]; api.accept = module_env["accept_not_qualified"]
    return NS(**module_env)


def test_namespace():
    current = initialize()
    ns, proof = old.namespace_bundle.load(old.c.ROOT, [BASE_TEST_PIN], {"case160_run004_controller":current})
    module = ns.test_case160_run004_controller
    config, pin = read_config()
    bytes_read = 133296 + pin["bytes"] + config["manifest_pin"]["bytes"] + config["capsule_pin"]["bytes"]
    mapping = {4:6, base.attempt.TASK:TASK, 28:31, 133296:bytes_read}
    for name, fn in tuple(vars(module.Tests).items()):
        target = fn.__func__ if type(fn) is classmethod else fn
        if type(target) is FunctionType:
            replacement = projected(target, target.__globals__, mapping)
            setattr(module.Tests, name, classmethod(replacement) if type(fn) is classmethod else replacement)
    return module, proof, current


CURRENT = initialize() if (old.c.ROOT/CONFIG).is_file() else None


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
            a.require(CURRENT is not None, "RUN005_CONFIG_REQUIRED")
            CURRENT.M.base.configure(CURRENT.M.base.task_index(sys.argv[3]))
            raise SystemExit(CURRENT.M.worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--prepare-artifacts", action="store_true")
        mode.add_argument("--qualify", action="store_true")
        mode.add_argument("--preflight", action="store_true")
        mode.add_argument("--run", type=int)
        args = parser.parse_args()
        if args.prepare_artifacts: raise SystemExit(prepare_artifacts())
        a.require(CURRENT is not None, "RUN005_CONFIG_REQUIRED")
        if args.qualify: raise SystemExit(CURRENT.qualify())
        CURRENT.M.base.configure(160)
        raise SystemExit(CURRENT.M.preflight() if args.preflight else CURRENT.run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        label = str(error) if isinstance(error, ValueError) and re.fullmatch("[A-Za-z0-9_]{1,160}", str(error)) else "REDACTED_RUN005_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED", error_code=label)))
        raise SystemExit(2) from None
