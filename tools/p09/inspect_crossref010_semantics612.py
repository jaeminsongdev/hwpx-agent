"""Fresh40 + existing24 probes/XML shapes, not a probe rerun or semantic qualification."""
import importlib.util,json,re,sys,time,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_capture010_shape612 as shape
import crossref_lossless_receipt610 as codec
import crossref_inline_receipt567 as layout
import crossref_external010_runtime as runtime
SELF='tools/p09/inspect_crossref010_semantics612.py'
TEST='tools/p09/tests/test_crossref_capture010_shape612.py'
RECOVERY='implementation/p09/evidence/p09-361-capture010-lossless-recovery611.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-capture010-parameter-shapes612-validated.v1.json'
def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--observe-only'],'P612_OBSERVE_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P612_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED010_PARAMETER_SHAPE_OBSERVATIONS',own_cpu_selection=selection,
        actual_Native_COM_or_Hancom_started=False,existing_probe_bodies_replayed=False,raw_parameter_values_or_commands_printed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,parameter_key_semantics_qualified=False,native_target_resolution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);recovery=layout.unpack(q.json(RECOVERY))
        c.require(q.snapshots[RECOVERY]['sha256']=='88eb3f144e32e0bd1fc7378c8c84eaf8e1968d12c933c5a8193ae196a628cab4'
            and recovery['state'].startswith('PASS_DERIVED010_')and recovery['cleanup']is True
            and recovery['fresh_inputs']==recovery['final_fresh_hashes']>0,'P612_RETAINED611_AUDIT')
        pin=recovery['derived_carrier'];c.require(q.pin(pin['path'])==pin,'P612_CURRENT_DERIVED_CARRIER')
        value=codec.unpack(q.json(pin['path']),guard.check)
        c.require(value['captured_cases']==8 and value['cleanup']is True and value['crossref_semantics_qualified']is False,'P612_RAW010_REMAINS_UNQUALIFIED')
        for pin in recovery['source_pins']:
            if pin['path']in('tools/p09/crossref_lossless_receipt610.py','tools/p09/compact_receipt_json.py'):
                c.require(q.pin(pin['path'])==pin,'P612_FROZEN_CODEC')
        packet_path=runtime.original.PACKET;packet=q.json(packet_path)
        fixed=runtime.fixed_input_pins()[packet_path];pin=q.snapshots[packet_path]
        c.require((pin['bytes'],pin['sha256'])==fixed and len(packet['cases'])==8,'P612_ORIGINAL_PREPARED8')
        for name in(SELF,TEST,'tools/p09/crossref_capture010_shape612.py'):q.pin(name)
        spec=importlib.util.spec_from_file_location('shape612_models',c.ROOT/TEST);models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        result=unittest.TestResult()
        with patch('subprocess.Popen',side_effect=AssertionError('P612_PROCESS_TRAP'))as trap:
            unittest.defaultTestLoader.loadTestsFromModule(models).run(result)
            row['process_constructor_trap_calls']=trap.call_count
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped));row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=9,errors=0,failures=0,skipped=0)and trap.call_count==0,'P612_NINE_BOUNDARY_MODELS')
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py'and '/tests/'not in path.as_posix():q.pin(path.relative_to(c.ROOT).as_posix())
        commands=[case['sdk_command']for case in packet['cases']];rows=[]
        for case in value['artifacts']['cases']:
            index=case['case_index'];pins=case['artifacts']
            for pin in pins.values():c.require(q.pin(pin['path'])==pin,'P612_FRESH_ORIGINAL40')
            trace=q.json(pins['target-trace.json']['path']);stages={}
            for stage in('opened','saved','reopened'):
                data=shape.read_package(q,pins[stage+'.hwpx'])
                observed=shape.inspect(data,commands[index-1],commands,guard.check);probe=trace['probe_observations'][stage]
                c.require(observed['crossref_fields']==probe['crossref_fields'],'P612_XML_AND_RECORDED_PROBE_COUNTS_AGREE')
                c.require(probe['observed_output_sha256']==pins[stage+'.hwpx']['sha256']and probe['observed_output_bytes']==pins[stage+'.hwpx']['bytes'],
                    'P612_RECORDED_PROBE_BOUND_TO_EXACT_CURRENT_ARTIFACT')
                stages[stage]=dict(shape=observed,recorded_probe_counts={k:probe[k]for k in('crossref_fields','crossrefs_without_parameters','opaque_parameter_children','plain_string_leaves')},
                    recorded_target_candidate_counts=probe['target_candidate_counts'])
            c.require(trace['operations']['sdk_insert']['execute_returned']is True,'P612_RECORDED_EXECUTE_RETURN')
            saved=stages['saved']['shape'];reopened=stages['reopened']['shape']
            rows.append(dict(case_index=index,stages=stages,saved_reopened_parameter_observations_equal=saved==reopened,
                recorded_sdk_returned_true=True,semantic_binding_qualified=False))
        row['cases']=rows;row['observed_cases']=len(rows)
        q.finish();guard.check(force=True);row['state']='PASS_FRESH010_EIGHT_CASES24_EXISTING_PROBES_XML_SHAPES_NOT_PARAMETER_SEMANTICS_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError,zipfile.BadZipFile)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P612_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        pin=s.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','observed_cases','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'cases':[dict(case_index=v['case_index'],saved_reopened_equal=v['saved_reopened_parameter_observations_equal'],
            opened=v['stages']['opened']['shape']['crossref_fields'],saved=v['stages']['saved']['shape']['crossref_fields'],reopened=v['stages']['reopened']['shape']['crossref_fields'],
            saved_selected_command_matches=sum(f['exact_selected_matching_children']for f in v['stages']['saved']['shape']['fields']))for v in row.get('cases',[])],
            'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
