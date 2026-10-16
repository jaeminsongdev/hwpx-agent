"""Production75 entry with original worker/launch and preparation bodies.

The entire73 preparation body is retained with one typed count and one
explicit transport namespace slot, both with exact inverses. Only current
metadata/source pins change. No diagnostic denial or Native dispatch here.
"""
import sys
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/native009_full75_worker_entry_v1.py'
TASK = 'case165-current-r009-tests'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
PREVIOUS = dict(path='tools/p09/native009_full73_worker_entry_v1.py', bytes=5924,
    sha256='ddfef95245bf2ffc3f345aa2ddfcac28a8a876961148f36824b4153bd56535fc')
OLD_ENTRY = dict(path='tools/p09/native009_worker_entry_v1.py', bytes=5740,
    sha256='0124e1c8bd05363be0fe8194d4d67778d74ab0d494af7e69b3f621c8a138d602')
OLD_LAUNCH = dict(path='tools/p09/native009_worker_launch_v1.py', bytes=4057,
    sha256='30088c308a7294dec10c295bcaba1d396382a7194541e5e21bd599dc03762f4b')
TRANSPORT = dict(path='tools/p09/native009_full75_transport_v1.py', bytes=23830,
    sha256='31d1eae0c6983a705bfba60b8160fe513f50822b0e74c2ab88c80a68963459ad')
HINT = dict(path=PREFIX+'successor-worker-bootstrap009.v5.json', bytes=15106,
    sha256='49fe9e963bb3de69471aa5922557d837054445a08bf1c6ff87b64fb015a892ca')
WIRE = dict(path=PREFIX+'successor-worker-capsule009.compact.v5.json', bytes=10747,
    sha256='f7caa9580a3c3fcd3519695714f984b788a3b63ec3d2c6f43110b7c1b7597a89')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
STEP = dict(path=PREFIX+'step-config001.v1.json', bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def require(ok, label):
    if not ok: raise ValueError('NATIVE009_FULL75_ENTRY_'+label)


def configured(fn, updates):
    require(type(fn) is FunctionType and fn.__name__ in ('worker_api', 'launch_api')
        and fn.__code__.co_filename.replace('\\', '/').endswith(PREVIOUS['path']), 'EXACT_PREVIOUS_ENTRY_FUNCTION')
    result = FunctionType(fn.__code__, dict(fn.__globals__, **updates), name=fn.__name__,
        argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
        and result.__closure__ is fn.__closure__, 'WHOLE_PREVIOUS_ENTRY_CODE_DEFAULTS_CLOSURE')
    return result


def prepare_slots(fn):
    require(type(fn) is FunctionType and fn.__name__ == 'prepare'
        and fn.__code__.co_filename.replace('\\', '/').endswith(PREVIOUS['path']), 'EXACT_PREVIOUS_NESTED_PREPARATION')
    before = fn.__code__
    counts = [n for n, value in enumerate(before.co_consts) if type(value) is int and value == 73]
    names = [n for n, value in enumerate(before.co_names) if value == 'native009_full73_transport_v1']
    require(len(counts) == len(names) == 1, 'ONE_TYPED_COUNT_AND_ONE_NAMED_TRANSPORT_SLOT')
    constants = list(before.co_consts); constants[counts[0]] = 75
    attributes = list(before.co_names); attributes[names[0]] = 'native009_full75_transport_v1'
    code = before.replace(co_consts=tuple(constants), co_names=tuple(attributes))
    inverse_constants = list(code.co_consts); inverse_constants[counts[0]] = 73
    inverse_names = list(code.co_names); inverse_names[names[0]] = 'native009_full73_transport_v1'
    require(code.replace(co_consts=tuple(inverse_constants), co_names=tuple(inverse_names)) == before,
        'ENTIRE_PREPARATION_CODE_INVERSE')
    result = FunctionType(code, fn.__globals__, name=fn.__name__, argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result, dict(old_count=73, new_count=75, count_slot=counts[0], transport_name_slot=names[0],
        old_transport_namespace='native009_full73_transport_v1', new_transport_namespace='native009_full75_transport_v1',
        entire_code_inverse=True, original_defaults_closure_and_globals_retained=True,
        preparation_checks_read_paths_and_engine_body_removed=False)


def worker_api(root, envelope, loader):
    modules, _ = loader.load(root, [PREVIOUS], {})
    previous = modules.native009_full73_worker_entry_v1
    make = configured(previous.worker_api, dict(SELF=SELF, HINT=HINT, WIRE=WIRE, STEP=STEP, TRANSPORT=TRANSPORT))
    api = make(root, envelope, loader)
    before = api.prepare
    revised, proof = prepare_slots(before)
    api.main.__globals__['prepare'] = revised; api.prepare = revised
    api.preparation_before = before; api.preparation_slots_proof = proof
    api.preparation_implementation_is_new_v4_with_original_worker_body = False
    api.preparation_implementation_is_new_v5_with_original_worker_body = True
    return api


def launch_api(root, loader):
    modules, _ = loader.load(root, [PREVIOUS], {})
    previous = modules.native009_full73_worker_entry_v1
    make = configured(previous.launch_api, dict(SELF=SELF))
    return make(root, loader)


def main():
    root = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(root/'tools/p09'))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    api = worker_api(root, envelope, envelope.namespace_bundle)
    return api.main()


if __name__ == '__main__': raise SystemExit(main())
