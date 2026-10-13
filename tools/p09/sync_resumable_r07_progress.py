"""P189 terminal/P190 plan document sync; not a runtime/source qualification."""
import argparse
import base64
import hashlib
import json

import resumable_current_r07 as v

c = v.c
SELF = 'tools/p09/sync_resumable_r07_progress.py'
REPORT = 'implementation/p09/P09-190_CURRENT_R07_RESUMABLE_VALIDATION_REPORT.md'
DOCS = ('CURRENT_STATE.md', 'implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
ARCHIVE = 'implementation/p09/source-archive/p09-190-pre-resumable-progress/document-preimages.v1.json'
DEST = 'implementation/p09/evidence/p09-190-resumable-progress-sync-run01.v1.json'
PREP = dict(path=v.observed.PREP, bytes=342258,
            sha256='d7ae0688d8dc0446e70efde0542edb34fb28c6ba66987f092b02d87dae0aa753')
ACTUAL = dict(path=v.observed.ACTUAL, bytes=2758106,
              sha256='699f9eb4a4c84b1bb08295942767ad71a8f6bf58a0bd79ca95bd2eb70d80742c')
LIGHT = dict(path=v.DEST, bytes=6556,
             sha256='0104038a52bff6a5b2438e7f06dea09992327924c80fee369a61cd7efb2520fd')


def require(ok, code):
    v.require(ok, 'DOC_' + code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('archive', 'verify'), required=True)
    args = ap.parse_args()
    require(c.Path.cwd().resolve() == c.ROOT, 'CWD')
    destination = v.observed.s.scoped_path(ARCHIVE if args.mode == 'archive' else DEST, fresh=True)
    resources = v.observed.run.pressure.observation.ObservedResources()
    q = None
    out = dict(state='FAILED_NOT_ACCEPTED', goal_status='active', full249_current_qualified=False,
               signed16_current_qualified=False, product_complete=False, P09_gate='OPEN',
               A12_gate='OPEN', A13_gate='OPEN', PC_freeze_resolved=False,
               current_full_source_or_EXE_audit_executed=False, test_runtime_or_Cargo_SQL_Hangul_child_executed=False,
               old_partial48_promoted_to_completed_cases=False)
    try:
        resources.admit()
        q = v.observed.run.pressure.PressureReader(resources)
        q.pin(SELF)
        if args.mode == 'archive':
            files = []
            for name in DOCS:
                raw = q.text(name).encode()
                pin = q.reader.snapshots[name]
                require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'WHOLE_RAW_DOC')
                files.append(dict(**pin, base64=base64.b64encode(raw).decode()))
            q.finish()
            out.update(state='WHOLE_PRIOR_R59_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE', files=files)
        else:
            for pin in (PREP, ACTUAL, LIGHT, v.observed.run.PARENT):
                require(q.pin(pin['path']) == pin, 'IMMUTABLE_RECEIPTS')
            prep = q.json(PREP['path'])
            actual = q.json(ACTUAL['path'])
            light = q.json(LIGHT['path'])
            parent = q.json(v.observed.run.PARENT['path'])
            expected, exe = v.observed.run.parent_scope(parent)
            require(prep['state'] == 'PASS_CURRENT_R07_FULL249_PREPARATION_ONLY_NOT_RUNTIME_OR_GATE'
                    and prep['contract_tests_passed'] == 109 and prep['resource_stop_reason'] is None
                    and prep['resource_watcher_cleanup_confirmed'] is True, 'ACTUAL_PREP_ONLY')
            require(actual['state'] == 'STOPPED_NOT_ACCEPTED' and actual['stop_reason'] == 'STOP_SUSTAINED_SYSTEM_CPU'
                    and actual['operation_phase'] == 'running' and actual['exit_code'] is None
                    and actual['policy'] == c.POLICY and actual['maximum_seconds'] == 1200
                    and actual['cleanup_confirmed'] is True and actual['owned_tree_empty'] is True
                    and actual['job_final']['active_processes'] == 0
                    and actual['capture_diagnostics']['public_passed_test_count'] == 48
                    and actual['capture_diagnostics']['public_completed_test_count'] == 48
                    and actual['capture_diagnostics']['public_active_test_name'].endswith(
                        'all36_frozen_originals_signed_full_candidates_or_no_formula_denial_and_live_revocation')
                    and actual['full249_current_qualified'] is False and actual['signed16_current_qualified'] is False,
                    'TERMINAL_RUNNING_STOP_NOT_SUCCESS')
            require(light['state'] == 'PASS_R07_RESUMABLE_CONTRACT22_AND_PLAN_ONLY_NOT_RUNTIME_OR_GATE'
                    and light['contract_tests_passed'] == 22 and light['resource_stop_reason'] is None
                    and light['resource_watcher_cleanup_confirmed'] is True
                    and light['runtime_launcher_implemented'] is False
                    and light['plan'] == v.plan(parent['source_test_names'], expected, exe)
                    and light['plan']['remaining_regular_cases'] == 243
                    and light['plan']['remaining_corpus_cases'] == 6
                    and light['plan']['accepted_individual_cases'] == 0, 'EXACT_PLAN_NOT_RUNTIME')
            frozen = {p['path']: p for p in light['bound_input_pins']}
            for name in (v.SELF, v.TEST):
                require(q.pin(name) == frozen[name], 'LIGHT_HELPERS_UNCHANGED')
            out.update(v.contracts())
            old = q.json(ARCHIVE)
            prefixes = []
            require(old['state'] == 'WHOLE_PRIOR_R59_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE', 'ARCHIVE_STATE')
            for name in DOCS:
                _, raw = v.observed.run.b.parser.preimage(old, name)
                current = q.text(name).encode()
                require(current.endswith(raw) and len(current) > len(raw), 'WHOLE_PRIOR_DOC_SUFFIX')
                prefixes.append(current[:-len(raw)])
            require(prefixes[0] == prefixes[1] and all(word in prefixes[0] for word in
                    (b'P189_ACTUAL_STOPPED', b'P190_PLAN_ONLY', b'243', b'6', b'48', b'r61',
                     b'compiled249=true/full249=false/signed16=false')), 'SAME_ACCURATE_PREFIX')
            report = q.text(REPORT)
            require(all(word in report for word in ('243', '6', '22', 'NOT_RUN', '48', 'P09')), 'REPORT_SCOPE')
            q.finish()
            out.update(state='PASS_R07_RESUMABLE_PLAN_AND_TERMINAL_STOP_DOC_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                       whole_prior_documents_preserved=True, actual_terminal_receipt_pin=ACTUAL,
                       preparation_receipt_pin=PREP, resumable_contract_plan_pin=LIGHT,
                       inherited_current_compiled249_standing_only=True,
                       completed_new_runtime_cases=0, original_P189_stop_preserved=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out['error_code'] = v.observed.run.original.closed_error(error)
    finally:
        v.observed.s.finish_watcher(resources, out)
        out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None:
            out.update(IO=q.summary(), bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'contract_tests_passed', 'error_code',
                                                 'resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_', 'WHOLE_')) else 2


if __name__ == '__main__':
    raise SystemExit(main())
