"""Separate run010 zlib product entry; original diagnostic entry is unchanged.

The unchanged original main/ReadyReader/execute waits for the real GO and
retains original Job/source/worker checks. --probe-no-go permanently denies
process creation and allows only actual stdin EOF, never synthetic GO.
This is a worker entry, not a Native dispatcher or execution authorization.
"""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS

SELF = 'tools/p09/batch_product_worker.py'
TASK = 'case165-current-r010-tests'
LOADER = dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py', bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
COMMON = dict(path='tools/p09/batch_worker_launch.py', bytes=13040,
    sha256='a643b9c1fc1cf570e688e4e8d34ef2ff38e4277aecdc96ecdd6505be45b0c02f')
PROFILE = dict(path='tools/p09/batch_zlib_runtime.py', bytes=6690,
    sha256='93ac8ed05a3fb0032746eb66294b753da60ca2184b6427c4d9bd9da9c6605435')


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_PRODUCT_WORKER_' + code)


def bootstrap(root):
    path = root / LOADER['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(), 'DIRECT_LOADER')
    for ancestor in (path.parent, *path.parent.parents):
        require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(), 'DIRECT_ANCESTORS')
        if ancestor == root:
            break
    with path.open('rb') as stream:
        raw = stream.read(LOADER['bytes'] + 1)
    require(len(raw) == LOADER['bytes'] and hashlib.sha256(raw).hexdigest() == LOADER['sha256'],
        'EXACT_ORIGINAL_LOADER')
    env = dict(__name__='p09_exact_product_worker_loader', __file__=str(path))
    exec(compile(raw, LOADER['path'], 'exec'), env)
    return NS(**env)


def deny_probe_process(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
        raise ValueError('BATCH_PRODUCT_WORKER_PROBE_PROCESS_DENIED')


def worker_api(root, loader):
    """Only preparation and explicit entry/task metadata differ from main9."""
    common_lib, _ = loader.load(root, [COMMON, PROFILE], {})
    common, package = common_lib.batch_worker_launch, common_lib.batch_zlib_runtime
    require(common.SELF == COMMON['path'] and common.TASK == TASK and package.SELF == PROFILE['path'],
        'EXACT_CLOSED_COMMON_AND_PACKAGE')
    original_lib, _ = loader.load(root, [common.ENTRY], {})
    original = original_lib.native009_worker_entry_v1
    require(original.TASK == 'case165-current-r009-tests', 'UNCHANGED_ORIGINAL_ENTRY')
    api = common.family(original, dict(__file__=str(root / SELF), SELF=SELF, TASK=TASK, STEP=common.STEP))
    prepared = []
    def prepare(actual):
        require(actual == root and not prepared, 'ONE_CURRENT_ROOT_PREPARATION_NO_RETRY')
        # Latch before calling the original preparation so failure cannot retry.
        prepared.append(None)
        result = common.prepare(actual, package=package)
        prepared[0] = result
        return result
    def measured_json(row, **options):
        if row.get('terminal') == 'WORKER_NOT_AUTHORIZED':
            require(len(prepared) == 1 and prepared[0] is not None, 'ACTUAL_PREPARATION_BEFORE_EOF_REPORT')
            row = package.terminal_evidence(prepared[0][0], row)
            row = dict(row, separate_product_entry=SELF, original_common_diagnostic_entry_unchanged=True,
                actual_product_or_Native_or_acceptance_qualified=False)
        return json.dumps(row, **options)
    api.main.__globals__.update(prepare=prepare, json=NS(**{**vars(json), 'dumps':measured_json}))
    api.prepare = prepare
    return NS(**{**vars(api), 'preparations':prepared, 'common':common,
        'execution_authorization_granted':False, 'new_Native_dispatcher':False})


def run(api, argv, *, probe):
    require(type(argv) is list and type(probe) is bool, 'EXPLICIT_ARGUMENTS_AND_PROBE_MODE')
    api.arguments(argv)  # Original closed handle/task checks before preparation.
    before_argv, before_stdin = sys.argv, sys.stdin
    try:
        sys.argv = [before_argv[0], *argv]
        if probe:
            sys.stdin = api.common.NoGoInput(before_stdin)
        return api.main()
    finally:
        sys.argv, sys.stdin = before_argv, before_stdin


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'tools/p09'))
    sys.dont_write_bytecode = True
    argv = sys.argv[1:]
    probe = bool(argv and argv[0] == '--probe-no-go')
    if probe:
        sys.addaudithook(deny_probe_process)
        argv = argv[1:]
    return run(worker_api(root, bootstrap(root)), argv, probe=probe)


if __name__ == '__main__':
    raise SystemExit(main())
