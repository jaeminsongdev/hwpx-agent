"""Private product entry binding, retaining original Native launch/Job checks.

The old zlib diagnostic loader and worker remain unmodified. This adapter
selects a distinct entry pin in the private parent and the unchanged native
launcher. Constructing this adapter does not execute or authorize a product.
"""
import sys
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/batch_product_launch.py'
TEST = 'tools/p09/tests/test_batch_product_worker.py'
WORKER = 'tools/p09/batch_product_worker.py'
TASK = 'case165-current-r010-tests'


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_PRODUCT_LAUNCH_' + code)


def launch_api(root, loader, common, *, probe):
    require(type(probe) is bool and common.TASK == TASK, 'EXPLICIT_CURRENT_PROFILE')
    names, _ = loader.load(root, [common.LAUNCH], {})
    original = names.native009_worker_launch_v1
    require(original.ENTRY == common.ENTRY['path'] and original.TASK == 'case165-current-r009-tests',
        'UNCHANGED_ORIGINAL_NATIVE_LAUNCHER')
    selected = common.family(original, dict(ENTRY=WORKER, TASK=TASK))
    if not probe:
        return selected
    original_connect = selected.connect
    def connect(root, pin, component, protocol, connection, factory, capture_type, subprocess,
                owned, checkpoint, **options):
        def no_go(command, **kwargs):
            require(type(command) is list and len(command) == 7
                and command[:3] == [sys.executable, '-B', str(root / WORKER)]
                and command[3] == '--ready-handle' and command[5:] == ['--task', TASK],
                'EXACT_NEW_ENTRY_PROBE_COMMAND')
            return factory([*command[:3], '--probe-no-go', *command[3:]], **kwargs)
        return original_connect(root, pin, component, protocol, connection, no_go, capture_type,
            subprocess, owned, checkpoint, **options)
    return NS(**{**vars(selected), 'connect':connect, 'product_entry_probe_only':True})


def loader_for_parent(loader, *, probe):
    require(type(probe) is bool, 'EXPLICIT_NEW_PARENT_MODE')
    def load(root, pins, reuse):
        libraries, proof = loader.load(root, pins, reuse)
        if hasattr(libraries, 'batch_worker_launch'):
            common = libraries.batch_worker_launch
            def selected(actual_root, actual_loader):
                require(actual_root == root, 'SAME_PARENT_ROOT')
                return launch_api(root, actual_loader, common, probe=probe)
            libraries = NS(**{**vars(libraries),
                'batch_worker_launch':NS(**{**vars(common), 'launch_api':selected})})
        return libraries, proof
    return NS(**{**vars(loader), 'load':load})


def parent_apis(entry, parent, *, probe):
    """Change only the private explicit worker-pin/loader dependencies."""
    require(type(probe) is bool and entry.WORKER == 'tools/p09/batch_worker_launch.py',
        'UNCHANGED_ORIGINAL_PARENT_ENTRY')
    original = entry.connect
    require(type(original) is FunctionType, 'ORIGINAL_PARENT_CONNECT_BODY')
    connected = FunctionType(original.__code__, dict(original.__globals__, WORKER=WORKER),
        argdefs=original.__defaults__, closure=original.__closure__)
    connected.__kwdefaults__ = original.__kwdefaults__
    original_package = parent.connect_package
    def package(*args, **kwargs):
        result = original_package(*args, **kwargs)
        return NS(**{**vars(result), 'loader':loader_for_parent(result.loader, probe=probe)})
    return (NS(**{**vars(entry), 'connect':connected}),
        NS(**{**vars(parent), 'connect_package':package}))
