"""Two unchanged failed cases; closed static error codes only, no XML/log disclosure or PASS promotion."""
import json,re,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_paragraph_sort_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-paragraph-sort-diagnosis231.v1.json'
DRIVER='tools/p09/inspect_source_paragraph_sort_failures.py'
CASES={'sort_inside_one_table_cell_preserves_structure_and_original_inherited_lock_guard','sort_run_boundaries_tab_linebreak_and_empty_paragraph_are_kept'}
ALLOWED={'id_index_unknown_id_like_attribute','id_index_dangling_reference','id_index_duplicate_declaration','id_index_invalid_value',
    'id_index_invalid_profile','patch_selector_stale','patch_conflict','patch_limit_exceeded','text_flow_unsupported_shape','text_flow_wrong_root',
    'text_flow_invalid_number','text_flow_invalid_boolean','text_flow_invalid_text','text_flow_invalid_tab','text_flow_invalid_field'}


def snapshot(capture,expected):
    result=base.prior.base.prior.base.base.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    result['closed_source_sort_codes']=[n for n in re.findall(r'"([a-z0-9_]{1,96})"',raw)if n in ALLOWED][:16]
    result['closed_body_variants']=[n for n in re.findall(r'Body\(([A-Za-z]+)',raw)if n in {'Binding','Section','Paragraph','Table','Note','Graph','Limit'}][:16]
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SORT_DIAGNOSIS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PARAGRAPH_SORT_DIAGNOSIS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,diagnostic_only=True,formal_case_acceptance=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='72a57c2be2e2e8f0704454ccad91f7e6f417039f33b3465de5d8f6e7ea3ce7be'
            and failed['cleanup']and{n for n,s in failed['steps'][0]['tests']if s!='ok'}==CASES,'EXACT230_TWO_FAILURES_AND_SEVENTEEN_PASSES_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.inventory(guard.check)|{DRIVER}):
            q.pin(name)
            if name!=DRIVER:c.require(q.snapshots[name]==old[name],'DIAGNOSIS_SOURCE_TESTS_FIXTURES_AND_GUARDS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        for case in sorted(CASES):
            try:
                base.harness.run_one(case,[base.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','source_paragraph_sort',
                    '--message-format=short','--',case,'--exact','--test-threads=1'],{case},guard,audit.environment(),row,observe_capture=snapshot)
            except ValueError as error:c.require(str(error)=='SOURCE_NOTE_API_COMMAND_FAILED','EXPECTED_FAILED_DIAGNOSTIC_COMMAND_ONLY')
            step=row['steps'][-1];c.require(step['exit_code']==101 and step['tests']==[(case,'FAILED')]
                and step['bounded_output_observation']['closed_source_sort_codes'],'ONE_FAILED_CASE_AND_CLOSED_STATIC_REASON_OBSERVED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_TWO_UNCHANGED_SOURCE_SORT_FAILURE_DIAGNOSES_NOT_COMPONENT_OR_PRODUCT_PASS',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,retained17_not_reexecuted=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SORT_DIAGNOSIS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},
            'closed_diagnoses':[{k:s.get(k)for k in('stage','exit_code','bounded_output_observation')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
