"""External one-shot prepared-file capture. Code qualification before any Native.

User invocation authorizes only current session qualification and this fixed8
capture. It never retries consumed SDK trials, refreshes fields, edits input,
publishes a revision or claims semantic acceptance/P09 completion.
"""
import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS

import prepared_bookmark_native630 as runtime
import crossref_lossless_receipt610 as codec
import metadata_forensic_retention615 as retention

r = runtime.r
SELF = runtime.ENTRY
CODE = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code002.v1.json'
STATE = 'PASS630_PREPARED_NATIVE_CAPTURE_CODE_AND_ACTUAL_READY_DENIAL_NOT_NATIVE_OR_GATE'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark630-native001.v1.json'
CLAIM = 'implementation/p09/evidence/p09-361-prepared-bookmark630-claim001.v1.json'
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark630-native001-forensic'


def parser():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute-prepared-eight-once', action='store_true', required=True)
    return p


def publish(path, value):
    return r.shared.publisher.publish(r.c.ROOT, path, codec.pack(value, lambda: None), NS(require=r.c.require, exact=r.a.exact))


def load_code(reader):
    proof = codec.unpack(reader.json(CODE))
    runtime.require(proof['state'] == STATE and proof['cleanup'] is True
                    and proof['fresh_inputs'] == proof['final_fresh_hashes'] > 0
                    and proof['contracts'] == dict(run=14, errors=0, failures=0, skipped=0)
                    and proof['actual_native_started'] is False
                    and proof['ready_denial']['cleanup'] is True
                    and proof['ready_denial']['requests'] == 1
                    and proof['ready_denial']['result']['completed_callback_cases'] == 0,
                    'PREPARED630_CURRENT_CODE_AND_ACTUAL_DENIAL_PROOF')
    pins = {p['path']: p for p in proof['source_pins']}
    paths = set(proof['execution_dependency_paths'])
    runtime.require(runtime.SOURCES | {SELF, runtime.SELF} <= paths <= set(pins)
                    and runtime.prepared.loaded_dependencies(r.c.ROOT) <= paths, 'PREPARED630_WHOLE_EXECUTION_CLOSURE')
    for path in sorted(paths):
        runtime.require(reader.pin(path) == pins[path], 'PREPARED630_CHANGED_INPUT_REQUALIFY')
    return pins, paths


def close_readers(readers):
    for reader in readers.values():
        reader.finish()
    value = dict(closed=True, readers={k: dict(fresh_inputs=len(v.snapshots), final_fresh_hashes=v.final_fresh_hashes) for k, v in readers.items()})
    runtime.require(runtime.sections.closed_boundary(value), 'PREPARED630_WHOLE_READER_CLOSURE')
    return value


def main(argv=None):
    parser().parse_args(argv)
    c, a, shared = r.c, r.a, r.shared
    runtime.require(Path(sys.executable) == runtime.prepared.inspection.fixed.PYTHON, 'PREPARED630_FIXED_PYTHON')
    runtime.prepared.require_absent(c.ROOT, OUTPUT)
    runtime.prepared.require_absent(c.ROOT, CLAIM)
    runtime.absent()
    selection = r.tools.select_own_single_cpu()
    shared.host.configure_host_policy(c)
    guard = runtime.sections.guard_type(shared.baseline.guard_type(shared.final.guard_type(a.Guard)))()
    begin = time.monotonic()
    readers = {}
    row = dict(state='FAILED630_PREPARED_NATIVE_CAPTURE', own_cpu_selection=selection, native_claim_created=False,
               fixed_eight_executed=False, SDK_insertion_invoked=False, REF036_refresh_invoked=False,
               native_startup_qualified=False, reference_semantics_qualified=False, P09_gate='OPEN', P10_started=False,
               accepted_count_delta=0, automatic_retry=False)
    def notice(stage, value):
        print(json.dumps(dict(value, capture_purpose='prepared_files_not_SDK_insertion')), flush=True)
        if value.get('state') in ('NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP', 'NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP'):
            key = stage+'_early_notice'
            if key not in row:
                row[key] = publish('implementation/p09/evidence/p09-361-prepared-bookmark630-'+stage+'-notice001.v1.json', value)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        readers['source'] = q
        manifest, paths = load_code(q)
        row['prepared_files'] = runtime.prepared.validate_prepared(q, codec.unpack)
        row['python_host'] = runtime.prepared.runtime.require_qualification(q)
        installed = runtime.base.installed
        image = a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent, guard.check)
        shell = a.AcceptanceReader(Path(runtime.base.candidate.original.SHELL).parent, guard.check)
        python = a.AcceptanceReader(installed.fixed.PYTHON.parent, guard.check)
        readers = dict(source=q, native=image, shell=shell, runtime=python)
        runtime.prepared.runtime.verify_current_reader(python)
        shell_expected = shell.pin(Path(runtime.base.candidate.original.SHELL).name)
        runtime.require(shell_expected == codec.unpack(q.json(CODE))['shell_pin'], 'PREPARED630_EXACT_VERIFIED_SHELL')
        row['prerequisites'] = installed.prerequisites.inspect(guard.windows, guard.check,
            lambda: image.fresh_pin(Path(installed.native.EXECUTABLE).name))
        row['preparation_boundary'] = close_readers(readers)
        runtime.require(row['prerequisites']['all_observed_prerequisites_passed'], 'PREPARED630_CURRENT_PREREQUISITES_DENIED_NO_CLAIM')
        guard.advance('qualification', lambda: runtime.sections.closed_boundary(row['preparation_boundary']))
        row['claim'] = publish(CLAIM, dict(state='ONE_PREPARED_EIGHT_CAPTURE_CLAIMED_NO_RETRY',
            purpose='current_session_then_prepared_file8_save_independent_reopen_PDF',
            code_receipt=CODE, code_sha256=q.snapshots[CODE]['sha256'], P09_complete=False))
        row['native_claim_created'] = True
        scratch = c.ROOT/'target/p09-prepared-bookmark630-native001-scratch'
        runtime.prepared.require_absent(c.ROOT, scratch.relative_to(c.ROOT).as_posix())
        scratch.mkdir()
        env = r.audit.environment()
        env.update(TEMP=str(scratch), TMP=str(scratch), PYTHONDONTWRITEBYTECODE='1')
        runtime.execute(guard, manifest, paths, shell_expected, env, notice, row)
        guard.advance('final_audit', lambda: row.get('batch_closed_for_final_audit') is True)
        current = {}
        for label, old in readers.items():
            fresh = a.AcceptanceReader(old.root, guard.check)
            for name, pin in old.snapshots.items():
                runtime.require(fresh.pin(name) == pin, 'PREPARED630_FINAL_FRESH_INPUTS')
            current[label] = fresh
        readers = current
        row['final_audit_boundary'] = close_readers(readers)
        guard.complete(lambda: runtime.sections.closed_boundary(row['final_audit_boundary']) and row['batch_closed_for_final_audit'])
        row.update(state='CAPTURED630_PREPARED_EIGHT_NATIVE_FILES_AND_PDF_SEMANTICS_UNQUALIFIED', fixed_eight_executed=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        row.update(error_type=type(error).__name__, error_code=runtime.prepared.safe_code(error), rerun_forbidden=True)
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(v.get('cleanup') is True for k, v in row.items() if k in ('qualification_worker', 'capture_worker')),
            elapsed_seconds=round(time.monotonic()-begin, 3), section_timing=guard.section_summary(), resource_samples=guard.samples,
            source_pins=[] if 'source' not in readers else list(readers['source'].snapshots.values()),
            fresh_inputs=0 if 'source' not in readers else len(readers['source'].snapshots),
            final_fresh_hashes=0 if 'source' not in readers else readers['source'].final_fresh_hashes)
        normalized, retained = retention.retain(c.ROOT, SPOOL, row)
        pin = publish(OUTPUT, normalized)
        print(json.dumps(dict(state=row['state'], error_code=row.get('error_code'), cleanup=row['cleanup'],
            fixed_eight_executed=row['fixed_eight_executed'], native_claim_created=row['native_claim_created'],
            reference_semantics_qualified=False, P09_complete=False, receipt=pin, retained_metadata=retained)), flush=True)
    return 0 if row['state'].startswith('CAPTURED630_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
