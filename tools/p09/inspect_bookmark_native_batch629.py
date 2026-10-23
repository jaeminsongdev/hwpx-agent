"""One fixed read-only external preparation. No execute flag, COM or child launch.

This command does NOT run the eight documents and is NOT their session permit.
Its immutable receipt cannot be consumed as a live Native handoff later.
"""
import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS

import named_style_verification_runtime as r
import bookmark_native_preparation629 as preparation
import crossref_lossless_receipt610 as receipt

SELF = 'tools/p09/inspect_bookmark_native_batch629.py'
CODE = 'implementation/p09/evidence/p09-361-bookmark-native-preparation629-code002.v1.json'
OUTPUT = 'implementation/p09/evidence/p09-361-bookmark-native-preparation629-external001.v1.json'
CODE_STATE = 'PASS629_PREPARED_EIGHT_AND_READONLY_CONTRACTS_NOT_NATIVE_ENTRY_READY'


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument('--inspect-only', action='store_true', required=True)
    return value


def load_code(reader):
    proof = receipt.unpack(reader.json(CODE))
    preparation.require(proof['state'] == CODE_STATE and proof['cleanup'] is True
                        and proof['fresh_inputs'] == proof['final_fresh_hashes'] > 0
                        and proof['contracts'] == dict(run=18, errors=0, failures=0, skipped=0)
                        and proof['actual_native_started'] is False, 'READONLY_CODE_PROOF')
    pins = {p['path']: p for p in proof['source_pins']}
    paths = set(proof['entry_dependency_paths'])
    preparation.require({SELF, preparation.SELF} <= paths <= set(pins)
                        and preparation.loaded_dependencies(r.c.ROOT) <= paths, 'COMPLETE_READONLY_CODE_CLOSURE')
    for path in sorted(paths):
        preparation.require(reader.pin(path) == pins[path], 'CURRENT_READONLY_CODE_CHANGED_REQUALIFY')
    return proof


def main(argv=None):
    parser().parse_args(argv)
    c, a, shared = r.c, r.a, r.shared
    preparation.require(Path(sys.executable) == preparation.inspection.fixed.PYTHON, 'FIXED_RUNTIME_PATH')
    preparation.require_absent(c.ROOT, OUTPUT)
    selection = r.tools.select_own_single_cpu()
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = native = python = None
    started = time.monotonic()
    row = dict(state='FAILED629_READONLY_PREPARATION_NOT_NATIVE', own_cpu_selection=selection,
               actual_native_started=False, permission_dialog_requested=False, fixed_eight_executed=False,
               native_execution_authorized=False, native_startup_qualified=False, native_entry_ready=False,
               automatic_execution_or_retry=False, P09_gate='OPEN', P10_started=False, accepted_count_delta=0)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        load_code(q)
        row['prepared_files'] = preparation.validate_prepared(q, receipt.unpack)
        row['python_qualification'] = preparation.runtime.require_qualification(q)
        executable = Path(preparation.inspection.native.EXECUTABLE)
        native = a.AcceptanceReader(executable.parent, guard.check)
        python = a.AcceptanceReader(preparation.inspection.fixed.PYTHON.parent, guard.check)
        row['observation'] = preparation.inspect_current(guard.windows, guard.check,
            lambda: native.fresh_pin(executable.name), lambda: preparation.runtime.verify_current_reader(python))
        native.finish()
        python.finish()
        q.finish()
        guard.check(force=True)
        row['state'] = ('OBSERVED629_CURRENT_EXTERNAL_PREREQUISITES_AND_EIGHT_FILES_NOT_NATIVE_ENTRY_READY'
                        if row['observation']['external_jobless_prerequisites_observed']
                        else 'DENIED629_CURRENT_PREREQUISITES_NO_NATIVE_STARTED')
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        row.update(error_type=type(error).__name__, error_code=preparation.safe_code(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup, elapsed_seconds=round(time.monotonic() - started, 3),
                   fresh_inputs=0 if q is None else len(q.snapshots),
                   final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                   source_pins=[] if q is None else list(q.snapshots.values()),
                   native_image_final_fresh_hashes=0 if native is None else native.final_fresh_hashes,
                   runtime_final_fresh_hashes=0 if python is None else python.final_fresh_hashes,
                   resource_samples=guard.samples)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, receipt.pack(row, lambda: None), NS(require=c.require, exact=a.exact))
        print(json.dumps(dict(state=row['state'], error_code=row.get('error_code'), cleanup=row['cleanup'],
                              elapsed_seconds=row['elapsed_seconds'], receipt=pin,
                              fixed_eight_executed=False, native_entry_ready=False)), flush=True)
    return 0 if row['state'].startswith('OBSERVED629_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
