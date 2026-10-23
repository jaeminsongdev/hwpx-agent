"""Explicit DERIVED lossless010 carrier + retrospective audit, never a Native rerun.

The consumed010 output stays ABSENT (its publication really failed). The raw
spool, failure notices, original sources and claim stay unchanged. This NEW
carrier is not the original runtime receipt or an acceptance/Native permit.
"""
import hashlib,json,re,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_generation010_publication as old
import crossref_lossless_receipt610 as codec
import crossref_inline_receipt567 as layout
import compact_receipt_json as compact
import crossref_external010_runtime as runtime

SELF='tools/p09/recover_crossref010_result611.py'
CODE='implementation/p09/evidence/p09-361-lossless-codec610-models-audit002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-capture010-lossless-recovery611.v1.json'
CARRIER='implementation/p09/evidence/p09-361-capture010-derived-lossless-result611.v1.json'
RAW_SHA='8b3b52e328fe106e0d4485626e2e46a8441bc5d0b435b7b7222517d332e6b547'

def main():
    c,a,s=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--recover-retained-only'],'P611_RETAINED_ONLY')
    for name in(OUTPUT,CARRIER):c.require(not(c.ROOT/name).exists()and not(c.ROOT/name).is_symlink(),'P611_NEW_IMMUTABLE_OUTPUT')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_DERIVED010_LOSSLESS_RECOVERY',own_cpu_selection=selection,
        actual_Native_COM_or_Hancom_started=False,consumed010_replayed=False,original010_republished=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,crossref_semantics_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=layout.unpack(q.json(CODE))
        c.require(q.snapshots[CODE]['sha256']=='0d467385ef4543ee95492da1f00b10a715b3c9259c19f5f24bf73c17c4eeced0'
            and proof['state']=='PASS_CODEC610_EXACT010_LOSSLESS_ROUND_TRIP_NOT_NATIVE_OR_GATE'and proof['cleanup']is True
            and proof['fresh_inputs']==proof['final_fresh_hashes']>0 and proof['contracts']==dict(run=16,errors=0,failures=0,skipped=0),'P611_CURRENT_16_CODEC_MODELS_NOT_REPLAYED')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'P611_ALL_QUALIFIED_CODEC_INPUTS_UNCHANGED')
        value=old.retained_row(c.ROOT);raw=compact.raw(value)
        c.require(len(raw)==831005 and hashlib.sha256(raw).hexdigest()==RAW_SHA,'P611_EXACT_RAW010')
        for pin in value['source_pins']:c.require(q.pin(pin['path'])==pin,'P611_CONSUMED010_EXECUTION_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        c.require(value['state']=='CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED'
            and value['cleanup']is True and value['fixed_eight_executed']is True and value['captured_cases']==8
            and value['fresh_inputs']==value['final_fresh_hashes']==len(value['source_pins'])
            and value['batch_closed_for_final_audit']is True and value['section_timing']['completed']is True
            and len(value['section_timing']['closed_sections'])==12,'P611_RECORDED_ALL8_AND_FINAL_AUDIT_CLOSED')
        old.validate(value)
        for name in('qualification_boundary','fixed_boundary','preparation_boundary','final_audit_boundary'):
            c.require(runtime.sections.closed_boundary(value[name]),'P611_ORIGINAL_WHOLE_BOUNDARIES_CLOSED')
        c.require(len(value['case_source_boundaries'])==8 and all(runtime.sections.closed_boundary(item)for item in value['case_source_boundaries']),
            'P611_ORIGINAL_EIGHT_CASE_SOURCE_BOUNDARIES_CLOSED')
        for name in('qualification_worker','fixed_worker'):
            worker=value[name];c.require(worker['exit_code']==0 and worker['cleanup']is True and worker['io_threads_joined']is True
                and worker['owned_job']['cleanup_confirmed']is True and worker['owned_job']['owned_tree_empty']is True
                and worker['owned_job']['forced_termination_invoked']is False,'P611_ORIGINAL_EXACT_WORKER_CLEANUP')
        summary=value['fixed_worker']['handler_summary'];protocol=summary['protocol']['protocol'];scope=summary['protocol']['scope']
        c.require(summary['worker_lease_closed']is True and summary['source_case']is None and summary['source_error']is None
            and protocol['all_eight_callback_cases_returned']is True and protocol['stopped']is False and protocol['sequence']==152
            and protocol['primary_error']is None and protocol['cleanup_error']is None
            and protocol['completed_callback_cases']==[dict(case_index=i,case_status='returned')for i in range(1,9)]
            and scope['closed']is True and scope['next_case_index']==9 and scope['next_step_index']==0
            and scope['pending_owner_admission']is False and scope['stopped']is False and len(scope['retired_sessions'])==16,
            'P611_RECORDED_EXACT_SCOPE_AND_152_CALLBACKS')
        # This facade contains ONLY recorded data, not live handles or saved permits.
        recorded=NS(protocol=NS(protocol=NS(case_index=scope['next_case_index'],stopped=protocol['stopped'])),scope=NS(sessions=scope['retired_sessions']))
        with patch.object(runtime.original.session.startup,'PreassignedNativeStartup',side_effect=AssertionError('P611_NATIVE_TRAP'))as native,patch(
            'subprocess.Popen',side_effect=AssertionError('P611_PROCESS_TRAP'))as process:
            artifacts=runtime.capture_artifacts(guard,recorded)
            row.update(native_constructor_trap_calls=native.call_count,process_constructor_trap_calls=process.call_count)
        c.require(native.call_count==process.call_count==0 and artifacts==value['artifacts'],'P611_SAME40_FRESH_ARTIFACTS_AND_CANONICAL16_IDENTITIES_NOT_NEW_LIVE_QUALIFICATION')
        for case in artifacts['cases']:
            for pin in case['artifacts'].values():c.require(q.pin(pin['path'])==pin,'P611_ALL40_ARTIFACT_PINS_STILL_CURRENT')
        packet=codec.pack(value,guard.check)
        carrier=s.publisher.publish(c.ROOT,CARRIER,packet,NS(require=c.require,exact=a.exact))
        c.require(q.pin(CARRIER)==carrier and compact.raw(codec.unpack(q.json(CARRIER),guard.check))==raw,'P611_ACTUAL_DISK_CARRIER_LOSSLESS')
        c.require(not(c.ROOT/old.OUTPUT).exists(),'P611_ORIGINAL_FAILED_OUTPUT_NOT_CREATED')
        samples=value['resource_samples']
        row.update(derived_carrier=carrier,original_raw_sha256=RAW_SHA,original_raw_bytes=len(raw),original010_state=value['state'],
            original010_cleanup=value['cleanup'],original010_elapsed_seconds=value['elapsed_seconds'],original010_captured_cases=8,
            retrospective_artifact_fresh_inputs=artifacts['fresh_inputs'],retrospective_artifact_final_fresh_hashes=artifacts['final_fresh_hashes'],
            original_runtime_result_not_replaced=True,old_failed_publication_output_still_absent=True,
            actual010_system_CPU_max=value['system_CPU_max'],actual010_available_RAM_min_percent=value['available_RAM_min_percent'],
            actual010_samples_over90=sum(sample['system_cpu_percent']>=90 for sample in samples),
            actual010_samples_over98=sum(sample['system_cpu_percent']>=98 for sample in samples),
            actual010_parent_cpu_max=max((sample.get('parent_cpu_machine_percent')or 0 for sample in samples),default=0),
            codec_models_retained_without_replay=q.snapshots[CODE],actual_semantic_binding_qualified=False)
        q.finish();guard.check(force=True);row['state']='PASS_DERIVED010_LOSSLESS_CARRIER_AND_FRESH40_RETROSPECTIVE_AUDIT_NOT_NATIVE_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P611_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        pin=s.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','derived_carrier','original010_captured_cases','retrospective_artifact_fresh_inputs',
            'retrospective_artifact_final_fresh_hashes','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent',
            'actual010_system_CPU_max','actual010_samples_over90','actual010_parent_cpu_max')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
