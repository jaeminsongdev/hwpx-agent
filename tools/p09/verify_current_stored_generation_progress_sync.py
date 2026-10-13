"""P152 progress-only closing; prior full document bytes remain exact suffixes."""
import argparse
import base64
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF = 'tools/p09/verify_current_stored_generation_progress_sync.py'
ARCHIVE = 'implementation/p09/source-archive/p09-152-pre-progress-r33/document-pins.v1.json'
FAILED_ARCHIVE = 'implementation/p09/source-archive/p09-152-pre-progress-placement-fix-r33/source-preimages.v1.json'
PINS = [
    dict(path='implementation/p09/evidence/p09-152-current-stored-generation.light-run01.v1.json', bytes=2435,
        sha256='88ade416395d80207182518c50d3c5b121cbb8d87af6711c1f4f5fb3bd609483'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-generation.prepare-run01.v1.json', bytes=354870,
        sha256='0bf823b37a2f0444e0d650bab205f8c71201e5d50b09a002a31f1379b0499b38'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-generation.terminal-audit-run01.v1.json', bytes=299334,
        sha256='45b6fef6145b797a6d9bcc17f561a3e70e1066e9f54774d15ee6d3e05d16eec9')]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    s.require(s.c.Path.cwd().resolve() == s.c.ROOT, 'SYNC_REPOSITORY_CWD')
    destination = s.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-generation.progress-sync-run{args.run:02}.v1.json', fresh=True)
    resources = s.SQLRuntimeResources(); q = None; started = time.monotonic()
    out = dict(schema_version='hwpx-agent.p09-current-stored-generation-progress-sync/v1', state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False, actual_Cargo_Rustc_SQL_Docker_native_or_child_executed=False,
        current_compiled249_qualified=False, full249_current_qualified=False, product_complete=False,
        P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN', goal_status='active', remaining_non_permission_work_units=76,
        raw_logs_included=False, PC_freeze_resolved=False)
    try:
        resources.admit(); q = s.LiveSQLReader(resources); q.pin(SELF)
        with patch('subprocess.Popen', side_effect=AssertionError('P152_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('P152_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start', side_effect=AssertionError('P152_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS: s.require(q.pin(pin['path']) == pin, 'SYNC_EVIDENCE_IMMUTABLE')
            failed_archive = q.json(FAILED_ARCHIVE); failed_pin = failed_archive['failed_receipt_pin']
            s.require(q.pin(failed_pin['path']) == failed_pin, 'SYNC_FAILED_RECEIPT_IMMUTABLE')
            failed = q.json(failed_pin['path'])
            s.require(failed['state'] == 'FAILED_NOT_ACCEPTED' and failed['source_closing_exact'] is False
                and failed['error_code'] == 'P152_PREP_SYNC_WHOLE_PRIOR_BODY_EXACT'
                and failed['actual_Cargo_Rustc_SQL_Docker_native_or_child_executed'] is False, 'SYNC_FAILED_SCOPE_PRESERVED')
            s.require(len(failed_archive['files']) == 1, 'SYNC_FAILED_SOURCE_COUNT')
            item = failed_archive['files'][0]; raw = base64.b64decode(item['base64'], validate=True)
            old_pin = {k: item[k] for k in ('path', 'bytes', 'sha256')}
            s.require(item['path'] == SELF and len(raw) == item['bytes']
                and hashlib.sha256(raw).hexdigest() == item['sha256']
                and old_pin in failed['bound_input_pins'], 'SYNC_FAILED_WHOLE_SOURCE_PRESERVED')
            prepared = q.json(PINS[1]['path']); audited = q.json(PINS[2]['path'])
            s.require(prepared['state'] == s.PASS and audited['state'] ==
                'PASS_CURRENT_RUST785_SOURCE249_CLOSING_ONLY_NOT_COMPILED_RUNTIME_SQL_OR_GATE'
                and audited['source_closing_exact'] is True and audited['current_Rust_input_count'] == 785
                and audited['source_test_count'] == 249 and audited['source_module_instance_count'] == 59
                and audited['protected_executables_exact'] == 54 and audited['preserved_parent_EXE_input_count'] == 59
                and audited['contract_tests_passed'] == 14 and audited['compile_executor_connected'] is False
                and audited['full249_current_qualified'] is False, 'SYNC_SOURCE_ONLY_SCOPE')
            prefix = None; docs = []
            archive = q.json(ARCHIVE); prior = s.inputs.inventory(archive['files'], 2)
            s.require(set(prior) == {'CURRENT_STATE.md', 'implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'}, 'SYNC_DOCUMENT_SCOPE')
            for name, pin in prior.items():
                current = q.text(name).encode('utf-8'); actual = q.reader.snapshots[name]
                s.require(len(current) == actual['bytes'] and hashlib.sha256(current).hexdigest() == actual['sha256'], 'SYNC_CURRENT_DOCUMENT_BYTES')
                s.require(len(current) > pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest() == pin['sha256'], 'SYNC_WHOLE_PRIOR_BODY_EXACT')
                this_prefix = current[:-pin['bytes']]
                s.require(prefix is None or prefix == this_prefix, 'SYNC_IDENTICAL_PREFIX'); prefix = this_prefix; docs.append(actual)
            s.require(prefix.startswith('> 2026-10-07 P152 current-source249 preparation-r33:'.encode()), 'SYNC_CURRENT_GENERATION')
            header = prefix.decode('utf-8')
            for literal in ('목표 active', '잔여76', 'product=false', 'P10 새 구현 없음', 'executor_connected=false',
                    'false/NOT_RUN', 'compile600초/full2491200초', '기존 policy', 'SQL fixed image 부재'):
                s.require(literal in header, 'SYNC_DECLARED_BOUNDARY')
            for pin in PINS: s.require(pin['sha256'] in header, 'SYNC_EVIDENCE_LINK')
            q.finish(); out.update(state='PASS_PROGRESS_SYNC_ONLY_NOT_COMPILED_RUNTIME_SQL_NATIVE_OR_GATE',
                source_closing_exact=True, previous_whole_documents_preserved_as_byte_exact_suffix=True,
                failed_sync_and_whole_tested_helper_preserved=True, failed_sync_receipt_pin=failed_pin,
                prior_document_pins=list(prior.values()), current_document_pins=docs, current_evidence_pins=PINS,
                prefix_bytes=len(prefix), prefix_sha256=hashlib.sha256(prefix).hexdigest())
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else 'P152_SYNC_REDACTED_FAILURE'
        out['error_code'] = code if re.fullmatch('[A-Za-z0-9_]{1,160}', code) else 'P152_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources, out); out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'): out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None: out['IO'] = q.summary(); out['bound_input_pins'] = list(q.reader.snapshots.values())
        out['wall_seconds'] = round(time.monotonic()-started, 4)
        with destination.open('x', encoding='utf-8') as stream: json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'previous_whole_documents_preserved_as_byte_exact_suffix',
            'error_code', 'wall_seconds', 'resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__ == '__main__': raise SystemExit(main())
