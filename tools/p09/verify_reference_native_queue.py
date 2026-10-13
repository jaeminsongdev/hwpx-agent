"""Exclusive fixed complete17 SOURCE admission/current inspection; no default native execution."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import reference_native_queue as q

ROOT, require, canonical, sha = q.ROOT,q.require,q.canonical,q.sha
SOURCES=('tools/p09/click_here_owned_trace_binding.py','tools/p09/reference_native_queue.py',
    'tools/p09/tests/test_reference_native_queue.py','tools/p09/verify_reference_native_queue.py',
    'implementation/p09/P09-56_REFERENCE_NATIVE_QUEUE_POLICY.md')


def pins():return {name:sha(q.forms.candidate.bounded(ROOT/name)) for name in SOURCES}


def actual_tests():
    command=[sys.executable,'-m','unittest','tools.p09.tests.test_reference_native_queue','-v']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60)
    require(result.returncode == 0,'p56_actual_tests_failed')
    lines=(result.stdout+result.stderr).decode('utf-8',errors='replace').splitlines()
    names=[]
    for line in lines:
        match=re.fullmatch(r'(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_reference_native_queue\.[^)]+\) \.\.\. ok',line)
        if match:names.append(match[1])
    require(len(names) == len(set(names)) == 11 and 'OK' in lines and
        any(re.fullmatch('Ran 11 tests in [0-9.]+s',line) for line in lines),'p56_actual_tests_inventory')
    return {'passed':11,'exit_code':0,'test_names':sorted(names),'command_sha256':sha(canonical(command)),
        'synthetic_trace_fixtures_are_native_evidence':False,'native_execute_invoked':False}


def record():
    before=pins();ctx=q.context();q.unused(ctx)
    tests=actual_tests()
    preflight=q.preflight_all(ctx)
    current=q.observe_current(before)
    require(current['state'] == 'NOT_RUN' and current['case_count'] == 0,'p56_source_current_must_not_run')
    q.check_context(ctx,q.context());require(before == pins(),'p56_new_sources_changed');q.unused(ctx)
    return {'schema_version':'hwpx-agent.reference-native-complete-source-admission/v1',
        'state':'complete_seventeen_source_preflight_not_native_qualification','source_sha256':before,
        'queue_context':ctx,'actual_unit_tests':tests,'actual_all_seventeen_no_com_prefixes':preflight,
        'actual_current_status':current,'claims':{'complete_ready_queue_source_protected':True,
            'complete_p09_reference_coverage':False,'native_session_started':False,'native_dispatch_invoked':False,
            'native_binding_ownership_cleanup_rollback_or_package_render_product_qualified':False,
            'permission_clicks_automated':False,'raw_document_values_present':False,'whole_ordinary_suites_qualified':False,
            'p09_complete':False}}


def admitted():
    value=q.forms.read_json(ROOT/q.ADMISSION)
    expected={'schema_version':'hwpx-agent.reference-native-complete-source-admission/v1',
        'state':'complete_seventeen_source_preflight_not_native_qualification','source_sha256':pins(),
        'queue_context':q.context(),'claims':{'complete_ready_queue_source_protected':True,
            'complete_p09_reference_coverage':False,'native_session_started':False,'native_dispatch_invoked':False,
            'native_binding_ownership_cleanup_rollback_or_package_render_product_qualified':False,
            'permission_clicks_automated':False,'raw_document_values_present':False,'whole_ordinary_suites_qualified':False,
            'p09_complete':False}}
    require(type(value) is dict and value.keys() == expected.keys()|{
        'actual_unit_tests','actual_all_seventeen_no_com_prefixes','actual_current_status'},'p56_admission_schema')
    for key,item in expected.items():
        require(type(value[key]) is type(item) and canonical(value[key]) == canonical(item),'p56_admission_identity')
    proof=[{'case_id':name,'exit_code':0,'exact_prefix_pass':True,'new_run_directory_created':False,
        'native_session_started':False} for name in q.EXPECTED_IDS]
    require(canonical(value['actual_all_seventeen_no_com_prefixes']) == canonical(proof)
        and value['actual_unit_tests']['passed'] == 11 and value['actual_unit_tests']['exit_code'] == 0
        and value['actual_unit_tests']['synthetic_trace_fixtures_are_native_evidence'] is False
        and value['actual_unit_tests']['native_execute_invoked'] is False
        and value['actual_current_status']['state'] == 'NOT_RUN' and value['actual_current_status']['case_count'] == 0,
        'p56_admission_actual_scope')
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ('publish','verify','current','execute-native'):mode.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    try:
        if args.execute_native:
            value=admitted();q.execute_full_queue(value,pins());return 0
        if args.current:
            value=admitted();before=pins();result=q.observe_current(before)
            require(before == pins() and value == admitted(),'p56_current_source_changed')
            if result['state'] != 'NOT_RUN':
                output=ROOT/q.CURRENT;q.forms.environment.q.shared.within(output.parent,ROOT/'implementation/p09/evidence')
                with output.open('xb') as stream:stream.write(canonical(result))
            print(json.dumps({'state':result['state'],'case_count':result['case_count'],'native_session_started':False,
                'p09_complete':False},sort_keys=True));return 0
        target=ROOT/q.ADMISSION
        q.forms.environment.q.shared.within(target.parent,ROOT/'implementation/p09/evidence')
        require(args.verify or not target.exists(),'p56_exclusive_source_admission_exists')
        if target.exists():q.forms.candidate.bounded(target)
        value=record()
        if args.verify:require(canonical(value) == q.forms.candidate.bounded(target),'p56_whole_fresh_admission_changed')
        else:
            with target.open('xb') as stream:stream.write(canonical(value))
        print(json.dumps({'state':'complete_ready_queue_source_pass_not_native_qualification','unit_tests':11,
            'actual_no_com_prefixes':17,'source_admission_sha256':sha(q.forms.candidate.bounded(target)),
            'native_executed':False,'p09_complete':False},sort_keys=True));return 0
    except Exception as error:
        message=str(error);code=message if re.fullmatch('p56_[a-z_]+',message) else type(error).__name__
        print(json.dumps({'state':'fail','error_code':code,'partial_evidence_preserved':True,'native_executed':False,
            'p09_complete':False}),flush=True);return 2


if __name__=='__main__':raise SystemExit(main())
