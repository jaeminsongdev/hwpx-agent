"""P190 exact-case resume contracts for current r07; no runtime launcher here.

완료를 재사용하려면 정상 종료된 개별 case와 동일 입력의 별도 closing이
모두 필요하다. 중단된 ALL249의 카운트/순서로 테스트 이름을 추정하지 않는다.
Whole preservation auditing belongs at batch boundaries, not every case.
This module only plans/validates; mock contract PASS is never runtime PASS.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch

import run_observed_r07_full as observed

c = observed.c
SELF = 'tools/p09/resumable_current_r07.py'
TEST = 'tools/p09/tests/test_resumable_current_r07.py'
DEST = 'implementation/p09/evidence/p09-190-r07-resumable-contracts-and-plan-run01.v1.json'
SCHEMA = 'hwpx-agent.p09-r07-single-case/v1'
CLOSING_SCHEMA = 'hwpx-agent.p09-r07-resumable-batch-closing/v1'
CASE_PASS = 'PASS_EXACT_R07_SINGLE_CASE_NOT_FULL_OR_GATE'
CLOSING_PASS = 'PASS_EXACT_R07_RESUMABLE_BATCH_CLOSING_NOT_FULL_OR_GATE'
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_:]*')
RECEIPT = re.compile(r'p190-case-([0-9]{3})-attempt-([0-9]{3})\.json')
CORPUS_PREFIX = 'actual_import::formula_policy_issuer::corpus::'
SUMMARY = re.compile(
    r'(?m)^test result: ok\. ([0-9]+) passed; ([0-9]+) failed; ([0-9]+) ignored; '
    r'([0-9]+) measured; ([0-9]+) filtered out;[^\r\n]*\r?$')


def require(ok, code):
    c.require(ok, 'RESUME_' + code)


def pins(rows):
    require(isinstance(rows, list) and bool(rows), 'INPUT_SCOPE')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'PIN_FIELDS')
        path = row['path']
        require(isinstance(path, str) and path and '\\' not in path and ':' not in path
                and not path.startswith('/') and all(x not in ('', '.', '..') for x in path.split('/')),
                'PIN_PATH')
        require(type(row['bytes']) is int and row['bytes'] >= 0
                and isinstance(row['sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['sha256']),
                'PIN_VALUE')
        require(path not in result, 'DUPLICATE_PIN')
        result[path] = row
    return result


def identity(names, expected, exe):
    require(isinstance(names, list) and len(names) == 249 and len(set(names)) == 249
            and all(isinstance(n, str) and NAME.fullmatch(n) for n in names), 'EXACT249_NAMES')
    bound = pins(list(expected.values()))
    require(bound == expected and bound.get(exe['path']) == exe
            and exe == observed.run.listing.EXE, 'CURRENT_EXE')
    payload = dict(inventory_pin=observed.run.PARENT, compiled_test_executable_pin=exe,
                   all_test_names=names, bound_input_pins=[bound[n] for n in sorted(bound)])
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(compiled_inventory_pin=observed.run.PARENT, compiled_test_executable_pin=exe,
                exact_input_manifest_sha256=digest, expected_test_count=249)


def arguments(name):
    require(isinstance(name, str) and NAME.fullmatch(name), 'PUBLIC_CASE_NAME')
    return [name, '--exact', '--test-threads=1', '--format=pretty', '--color=never']


def terminal(output, errors, name):
    """No substring selection, captured panic text, or partial marker acceptance."""
    require(isinstance(output, str) and isinstance(errors, str)
            and len(output.encode('utf-8')) <= 32768 and len(errors.encode('utf-8')) <= 32768,
            'ORIGINAL_STREAM_CAP')
    require(errors == '', 'SUCCESS_STDERR_NOT_EMPTY')
    require(re.findall(r'(?m)^running ([0-9]+) tests?\r?$', output) == ['1'], 'EXACT_ONE_RUNNING')
    matches = SUMMARY.findall(output)
    require(matches == [('1', '0', '0', '0', '248')], 'EXACT_ONE_TERMINAL')
    lines = re.findall(r'(?m)^test ([A-Za-z_][A-Za-z0-9_:]*) \.\.\. (ok|FAILED|ignored)\r?$', output)
    require(lines == [(name, 'ok')], 'EXACT_ONE_NAMED_OK')
    return dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=248)


def closed_scope(doc):
    require(doc['policy'] == c.POLICY, 'ORIGINAL_RESOURCE_POLICY')
    require(type(doc['maximum_seconds']) is int and doc['maximum_seconds'] == 1200,
            'ORIGINAL_DEADLINE')
    require(doc['cleanup_confirmed'] is True and doc['owned_tree_empty'] is True
            and doc['job_final']['active_processes'] == 0 and doc['job_final']['owned_processes'] == [],
            'OWNED_CLEANUP')
    require(doc['resource_stop_reason'] is None and doc['stop_reason'] is None,
            'STOP_NOT_PASS')
    require(doc['writer_authorized'] is True and doc['worker_created'] is True
            and doc['job_assigned'] is True and doc['actual_job_membership_checked'] is True
            and doc['owned_limits_verified'] is True, 'ACTUAL_OWNERSHIP')
    require(doc['exit_code'] == 0 and type(doc['exit_code']) is int, 'EXIT_ZERO')
    require(all(doc[k] is False for k in ('full249_current_qualified', 'signed16_current_qualified',
            'product_complete', 'PC_freeze_resolved', 'actual_Cargo_SQL_Hangul_run'))
            and doc['P09_gate'] == doc['A12_gate'] == doc['A13_gate'] == 'OPEN', 'NO_SCOPE_PROMOTION')


def validate_case(doc, name, binding):
    require(doc['schema_version'] == SCHEMA and doc['state'] == CASE_PASS, 'CASE_SCOPE')
    require(doc['binding'] == binding and doc['selected_test_names'] == [name]
            and doc['test_arguments'] == arguments(name), 'EXACT_CASE_IDENTITY')
    closed_scope(doc)
    summary = dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=248)
    require(doc['terminal_summary'] == summary and doc['passed_test_names'] == [name], 'TERMINAL_PROOF')
    require(doc['capture']['error_code'] is None and doc['capture']['per_stream_limit_bytes'] == 32768
            and doc['capture']['complete_streams'] is True and doc['capture']['raw_logs_saved'] is False,
            'COMPLETE_CAPTURE')


def accept_case(doc, name, binding, closing, expected, actual_receipt_pin):
    validate_case(doc, name, binding)
    pins([actual_receipt_pin])
    require(closing['schema_version'] == CLOSING_SCHEMA and closing['state'] == CLOSING_PASS
            and closing['binding'] == binding and closing['resource_stop_reason'] is None
            and closing['resource_watcher_cleanup_confirmed'] is True
            and closing['source_closing_exact'] is True, 'SEPARATE_CLOSING_REQUIRED')
    require(pins(closing['source_freeze_before']) == expected
            and pins(closing['source_freeze_after']) == expected, 'WHOLE_BATCH_BOUNDARIES')
    require(closing['case_receipt_pins'][actual_receipt_pin['path']] == actual_receipt_pin, 'CASE_PIN_CLOSED')
    require(closing['actual_test_runtime_executed'] is False
            and closing['full249_current_qualified'] is False
            and closing['signed16_current_qualified'] is False
            and closing['product_complete'] is False and closing['P09_gate'] == 'OPEN', 'CLOSING_NOT_RUNTIME')
    return True


def plan(names, expected, exe, rows=(), closings=None):
    binding = identity(names, expected, exe)
    closings = {} if closings is None else closings
    accepted, attempts, candidates = set(), {}, set()
    seen_attempts = set()
    for filename, doc, actual_pin in rows:
        match = RECEIPT.fullmatch(filename)
        require(match is not None, 'RECEIPT_NAME')
        index, attempt = map(int, match.groups())
        require(1 <= index <= 249 and 1 <= attempt <= 999, 'RECEIPT_RANGE')
        require((index, attempt) not in seen_attempts, 'DUPLICATE_ATTEMPT')
        seen_attempts.add((index, attempt))
        pins([actual_pin])
        require(actual_pin['path'] == 'implementation/p09/evidence/resumable-r07/'+filename, 'RECEIPT_PATH')
        require(doc.get('schema_version') == SCHEMA and doc.get('binding') == binding
                and doc.get('selected_test_names') == [names[index-1]], 'ATTEMPT_SCOPE')
        attempts[index] = max(attempts.get(index, 0), attempt)
        if doc['state'] == CASE_PASS:
            validate_case(doc, names[index-1], binding)
            key = doc.get('closing_id')
            if key not in closings:
                # A stopped batch can receive an independent fresh closing later.
                # Until then preserve successful candidates, but do not skip them.
                candidates.add(index)
                continue
            accept_case(doc, names[index-1], binding, closings[key], expected, actual_pin)
            require(index not in accepted, 'DUPLICATE_ACCEPTED_CASE')
            accepted.add(index)
        else:
            require(doc['state'] in ('STOPPED_NOT_ACCEPTED', 'DEFERRED_NOT_STARTED', 'FAILED_NOT_ACCEPTED'),
                    'UNKNOWN_STATE')
    pending = [i for i in range(1, 250) if i not in accepted]
    heavy = [i for i in pending if names[i-1].startswith(CORPUS_PREFIX)]
    runnable = [i for i in pending if i not in heavy and i not in candidates]
    next_index = runnable[0] if runnable else None
    return dict(state='PLAN_ONLY_NOT_RUNTIME_OR_GATE', binding=binding,
                accepted_test_names=[names[i-1] for i in sorted(accepted)],
                accepted_individual_cases=len(accepted), remaining_individual_cases=len(pending),
                successful_candidates_requiring_separate_closing=len(candidates-accepted),
                remaining_regular_cases=len(pending)-len(heavy), remaining_corpus_cases=len(heavy),
                corpus_case_names=[names[i-1] for i in heavy], corpus_cases_deferred_not_skipped=True,
                next_index=next_index, next_test_name=names[next_index-1] if next_index else None,
                next_attempt=attempts.get(next_index, 0)+1 if next_index else None,
                maximum_cases_per_invocation=1, automatic_retry=False, parallel_execution=False,
                full249_current_qualified=False, signed16_current_qualified=False,
                all249_individual_runtime_qualified=False, single_process_full249_qualified=False,
                product_complete=False, P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN')


def contracts():
    sys.path.insert(0, str(c.ROOT/'tools/p09/tests'))
    suite = unittest.defaultTestLoader.loadTestsFromName('test_resumable_current_r07')
    with patch('subprocess.Popen', side_effect=AssertionError('P190_NO_CHILD')), \
            patch('subprocess.run', side_effect=AssertionError('P190_NO_CHILD')), \
            patch('threading.Thread.start', side_effect=AssertionError('P190_NO_NEW_THREAD')):
        checked = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    failed = sorted(t.id().split('.')[-1] for t, _ in checked.failures+checked.errors)
    require(checked.wasSuccessful() and checked.testsRun == 22 and not checked.skipped,
            'CONTRACT22_' + ('FAILED' if failed else 'COUNT'))
    return dict(contract_tests_run=22, contract_tests_passed=22)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=('light',), required=True)
    ap.parse_args()
    require(c.Path.cwd().resolve() == c.ROOT, 'CWD')
    destination = observed.s.scoped_path(DEST, fresh=True)
    resources = observed.run.pressure.observation.ObservedResources()
    q = None
    out = dict(state='FAILED_NOT_ACCEPTED', goal_status='active', full249_current_qualified=False,
               signed16_current_qualified=False, product_complete=False, P09_gate='OPEN',
               A12_gate='OPEN', A13_gate='OPEN', PC_freeze_resolved=False,
               actual_Cargo_SQL_Hangul_test_body_or_child_executed=False,
               runtime_launcher_implemented=False, full_current_source_or_EXE_audit_executed=False)
    try:
        resources.admit()
        q = observed.run.pressure.PressureReader(resources)
        require(q.pin(observed.run.PARENT['path']) == observed.run.PARENT, 'CURRENT_INVENTORY_PIN')
        parent = q.json(observed.run.PARENT['path'])
        expected, exe = observed.run.parent_scope(parent)
        out.update(contracts())
        for name in (SELF, TEST, observed.SELF, observed.TEST, observed.run.SELF, observed.run.TEST):
            q.pin(name)
        # Historical partial progress is diagnostic only. Do not invent 48 names.
        stopped = q.json(observed.ACTUAL)
        require(stopped['state'] == 'STOPPED_NOT_ACCEPTED'
                and stopped['stop_reason'] == 'STOP_SUSTAINED_SYSTEM_CPU'
                and stopped['cleanup_confirmed'] is True and stopped['owned_tree_empty'] is True
                and stopped['job_final']['active_processes'] == 0, 'LATEST_TERMINAL_STOP')
        out.update(plan=plan(parent['source_test_names'], expected, exe),
                   previous_actual_pin=q.reader.snapshots[observed.ACTUAL],
                   previous_partial_named_ok_count=stopped['capture_diagnostics']['public_passed_test_count'],
                   previous_partial_counts_used_as_reusable_completion=False)
        q.finish()
        out['state'] = 'PASS_R07_RESUMABLE_CONTRACT22_AND_PLAN_ONLY_NOT_RUNTIME_OR_GATE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out['error_code'] = observed.run.original.closed_error(error)
    finally:
        observed.s.finish_watcher(resources, out)
        out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None:
            out.update(IO=q.summary(), bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'contract_tests_passed', 'error_code',
                                                 'resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__ == '__main__':
    raise SystemExit(main())
