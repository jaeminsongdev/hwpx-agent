"""Complete fixed 15 form + 2 CLICK_HERE queue. Inspection never activates COM."""
import json
import subprocess
from tools.p09 import click_here_owned_trace_binding as field
from tools.p09 import qualify_native_form_binding_batch as forms
from tools.p09 import run_native_form_binding_batch as form_dispatch
from tools.p09 import verify_native_form_saved_package_contract as saved

ROOT, require, sha, canonical = forms.ROOT, forms.require, forms.sha, forms.canonical
ADMISSION = 'implementation/p09/evidence/p09-56-reference-native-queue.source-admission.v1.json'
DISPATCH = 'implementation/p09/evidence/p09-56-reference-native-queue.dispatch-r01.v1.json'
CURRENT = 'implementation/p09/evidence/p09-56-reference-native-queue.current-r01.v1.json'
EXPECTED_IDS = tuple(f'P09-35-C{i:02}' for i in range(1,16))+('P09-55-C01','P09-55-C02')


def context():
    p55 = field.predecessor()
    p52 = forms.admitted()
    form_rows = forms.candidate.validate_manifest(forms.read_json(forms.candidate.MANIFEST,524288))
    form_cases = forms.case_plan(form_rows,require_unused=False)
    field_rows, _ = field.p.original_inputs()
    cases=[]
    for row, _, _, directory in form_cases:
        cases.append({'case_id':row['case_id'],'kind':'native_form','package_sha256':row['package_sha256'],
            'plan_sha256':row['plan_sha256'],'run_directory':directory.relative_to(ROOT).as_posix()})
    for row in field_rows:
        cases.append({'case_id':row['case_id'],'kind':'click_here','package_sha256':row['source_package_sha256'],
            'plan_sha256':row['plan_sha256'],'run_directory':row['run_directory']})
    require(tuple(r['case_id'] for r in cases) == EXPECTED_IDS and len({r['run_directory'] for r in cases}) == 17,
        'p56_complete_queue_inventory')
    return {'p52_admission_sha256':sha(forms.candidate.bounded(ROOT/forms.ADMISSION)),
        'p52_source_sha256':p52['source_sha256'],'p55_source_receipt_sha256':field.P55_SHA,
        'p55_source_sha256':p55['source_sha256'],'entire_preserved_source_identity_sha256':sha(canonical(p55['preservation'])),
        'private_field_plan_bundle':field.p.inspect_bundle(),'complete_ordered_queue':cases}


def unused(ctx):
    for row in ctx['complete_ordered_queue']:
        forms.environment.q.shared.within((ROOT/row['run_directory']).parent,ROOT/'implementation/p09/evidence/private')
        require(not (ROOT/row['run_directory']).exists(),'p56_attempt_already_exists')
    require(not (ROOT/forms.DISPATCH).exists() and not (ROOT/DISPATCH).exists() and not (ROOT/CURRENT).exists(),
        'p56_current_evidence_already_exists')
    forms.hwp_zero()


def check_context(actual, expected):
    field.exact_dict(actual,expected,'p56_exact_full_queue_context')
    require(type(actual['complete_ordered_queue']) is list and
        tuple(row['case_id'] for row in actual['complete_ordered_queue']) == EXPECTED_IDS,'p56_complete_queue_identity')


def preflight_all(ctx):
    check_context(ctx,context())
    unused(ctx)
    rows=forms.candidate.validate_manifest(forms.read_json(forms.candidate.MANIFEST,524288))
    proof=forms.actual_prefixes(forms.case_plan(rows))
    for row in field.p.original_inputs()[0]:
        result=subprocess.run(field.p.preflight_command(row),cwd=ROOT,env=forms.environment.child_environment(),
            capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        require(result.returncode == 0 and not result.stderr,'p56_field_preflight_failed')
        value=json.loads(result.stdout,object_pairs_hook=forms.candidate.prior.io.duplicate_guard)
        expected={'state':'preflight_pass_no_com_no_run_directory','case_id':row['case_id'],
            'source_sha256':row['source_package_sha256'],'plan_sha256':row['plan_sha256'],
            'harness_sha256':ctx['p55_source_sha256'][field.p.HARNESS],
            'lifecycle_library_sha256':ctx['p55_source_sha256'][field.p.LIBRARY],
            'x86_sta':True,'no_com_server_activation':True,'native_run_directory_created':False,
            'registry_or_system_setting_changed':False,'p09_complete':False}
        field.exact_dict(value,expected,'p56_field_preflight_response')
        proof.append({'case_id':row['case_id'],'exit_code':0,'exact_prefix_pass':True,
            'new_run_directory_created':False,'native_session_started':False})
    require(tuple(r['case_id'] for r in proof) == EXPECTED_IDS,'p56_all_preflight_inventory')
    check_context(ctx,context())
    unused(ctx)
    return proof


def validate_dispatch(value, ctx, source_pins):
    expected={'schema_version':'hwpx-agent.reference-native-complete-queue-dispatch/v1',
        'state':'all_seventeen_actual_attempts_terminal_non_green','queue_context_sha256':sha(canonical(ctx)),
        'source_sha256':source_pins,'p52_dispatch_sha256':sha(forms.candidate.bounded(ROOT/forms.DISPATCH)),
        'permission_click_attestation':'not_attested','computer_use_click_or_type_invoked':False,
        'native_package_render_differential_or_product_qualified':False,'p09_complete':False}
    require(type(value) is dict and value.keys() == expected.keys()|{'field_cases','field_native_evidence_sha256'},
        'p56_dispatch_schema')
    for key, item in expected.items():
        require(type(value[key]) is type(item) and canonical(value[key]) == canonical(item),'p56_dispatch_identity')
    require(type(value['field_cases']) is list and [r.get('case_id') for r in value['field_cases']] == list(EXPECTED_IDS[-2:]),
        'p56_dispatch_full_field_inventory')
    require(type(value['field_native_evidence_sha256']) is dict and 2 <= len(value['field_native_evidence_sha256']) <= 10,
        'p56_dispatch_field_evidence_inventory')


def rebind_current(value, ctx, source_pins):
    validate_dispatch(value,ctx,source_pins)
    original_forms=saved.bind_actual_current() # Entire unchanged P52 actual binder, not a recreated subset.
    evidence={};cases=[]
    for row, recorded in zip(field.p.original_inputs()[0],value['field_cases'],strict=True):
        require(type(recorded) is dict and type(recorded.get('harness_exit')) is int,'p56_actual_field_child_result')
        bound,pins=field.read_case(row,recorded['harness_exit'],source_pins=ctx['p55_source_sha256'])
        require(bound == recorded,'p56_actual_field_trace_unbound')
        evidence.update(pins);cases.append(bound)
    require(evidence == value['field_native_evidence_sha256'] and ctx == context(),'p56_actual_field_evidence_changed')
    return original_forms,cases


def observe_current(source_pins):
    ctx=context()
    if not (ROOT/DISPATCH).exists():
        return {'state':'NOT_RUN','reason':'complete_seventeen_dispatch_absent_partial_evidence_not_promoted',
            'case_count':0,'native_session_started':False,'raw_document_values_present':False,'p09_complete':False}
    raw=forms.candidate.bounded(ROOT/DISPATCH)
    value=json.loads(raw,object_pairs_hook=forms.candidate.prior.io.duplicate_guard)
    before=rebind_current(value,ctx,source_pins)
    actual_form_packages=saved.current_observation() # Real P53 SDK consumer, after actual native batch only.
    require(before == rebind_current(value,ctx,source_pins) and raw == forms.candidate.bounded(ROOT/DISPATCH),
        'p56_current_changed_during_consumption')
    return {'state':'all_seventeen_current_results_bound_not_render_or_product','case_count':17,
        'actual_dispatch_sha256':sha(raw),'actual_fifteen_form_saved_packages':actual_form_packages,
        'actual_two_field_results':before[1],'native_session_started':False,'raw_document_values_present':False,
        'native_render_differential_or_product_qualified':False,'p09_complete':False}


def execute_full_queue(admitted, source_pins):
    # This function is NEVER called by source tests/inspection. Human authorization is required.
    ctx=context();require(admitted['queue_context'] == ctx,'p56_admitted_queue_changed')
    unused(ctx);preflight_all(ctx)
    print(json.dumps({'event':'complete_queue_start','case_count':17,'permission_clicks':'user_owned'}),flush=True)
    form_dispatch.run() # Actually invokes unchanged full15 dispatcher; no case-selector/shrunken copy.
    saved.bind_actual_current()
    require(ctx == context(),'p56_sources_changed_after_form_lane')
    cases=[];evidence={}
    for row in field.p.original_inputs()[0]:
        forms.hwp_zero();require(ctx == context(),'p56_sources_changed_before_field_case')
        command=field.p.preflight_command(row)
        require(command[-1] == '-PreflightOnly','p56_field_exact_execution_command')
        command[-1]='-ExecuteNative'
        print(json.dumps({'event':'case_start','case_id':row['case_id'],'of':17}),flush=True)
        process=subprocess.Popen(command,cwd=ROOT,env=forms.environment.child_environment(),stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        # No permission timeout/automatic retry/kill; drain output without logging document values.
        output_bytes=0
        for chunk in iter(lambda:process.stdout.read(4096),b''):output_bytes+=len(chunk)
        code=process.wait()
        require(output_bytes <= 262144,'p56_native_child_output_bound')
        record,pins=field.read_case(row,code,source_pins=ctx['p55_source_sha256'])
        cases.append(record);evidence.update(pins)
        require(record['cleanup_safe_to_continue'],'p56_unresolved_field_process_stop_preserve_evidence')
        forms.hwp_zero();require(ctx == context(),'p56_sources_changed_after_field_case')
    value={'schema_version':'hwpx-agent.reference-native-complete-queue-dispatch/v1',
        'state':'all_seventeen_actual_attempts_terminal_non_green','queue_context_sha256':sha(canonical(ctx)),
        'source_sha256':source_pins,'p52_dispatch_sha256':sha(forms.candidate.bounded(ROOT/forms.DISPATCH)),
        'field_cases':cases,'field_native_evidence_sha256':evidence,'permission_click_attestation':'not_attested',
        'computer_use_click_or_type_invoked':False,'native_package_render_differential_or_product_qualified':False,'p09_complete':False}
    rebind_current(value,ctx,source_pins)
    path=ROOT/DISPATCH
    forms.environment.q.shared.within(path.parent,ROOT/'implementation/p09/evidence')
    with path.open('xb') as stream:stream.write(canonical(value))
    print(json.dumps({'state':'complete_seventeen_diagnostic_attempts_terminal','p09_complete':False}),flush=True)
