"""320: public original-byte attribute test helper; retain319 source9, first product36 run."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_inventory_components as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-edit-inventory-recovery320.v1.json';DRIVER='tools/p09/run_font_inventory_recovery.py'
CURRENT='''                let original_part=archive::read_part(raw,e.source_part_path())?;
                assert_eq!(std::str::from_utf8(&original_part[e.source_start()..e.source_end()])?.parse::<usize>()?,original_items);assert_eq!(output_items-original_items,receipt.cloned_character_properties);assert_eq!(e.fragments(),0);
'''
ORIGINAL='                assert_eq!(a.semantic_value().parse::<usize>()?,original_items);assert_eq!(output_items-original_items,receipt.cloned_character_properties);assert_eq!(e.fragments(),0);\n'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_INVENTORY_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_EDIT_INVENTORY_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        common_operation_compiler_or_dispatcher_qualified=False,output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='b99c99bf713335849158e0f0d0484e47e4a1bf69a92f3b1da326e7ca6b5aa238'and failed['cleanup']and len(failed['steps'])==2,'EXACT319_MIXED_CORE_SUCCESS_AND_PRODUCT_COMPILE_FAILURE')
        retained=failed['steps'][0];expected={'scoped::'+n for n in previous.CORE_CASES}
        c.require(retained['exit_code']==0 and retained['diagnostics']==[]and len(retained['tests'])==9 and {n for n,s in retained['tests']if s=='ok'}==expected
            and failed['steps'][1]['tests']==[]and failed['steps'][1]['bounded_output_observation']['rust_error_codes']==['E0624'],'EXACT_SOURCE9_SUCCESS_AND_TEST_HELPER_VISIBILITY_ERROR')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=previous.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCT_KERNEL_INVENTORY_AND_PREVIOUS_TEST_BODIES_UNCHANGED')
        q.pin(DRIVER);text=q.text(previous.TEST);c.require(text.count(CURRENT)==1,'ONE_PUBLIC_ORIGINAL_ATTRIBUTE_BYTE_READER_FIX')
        audit.inverse(text.replace(CURRENT,ORIGINAL),old[previous.TEST],'ALL12_NEW_TEST_ASSERTIONS_EXCEPT_PRIVATE_HELPER_READ_UNCHANGED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        legacy=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(previous.base.TEST)));new={'edit_inventory_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(legacy)==24 and len(new)==12,'SAME24_PREVIOUS_AND12_NEW_PRODUCT_CASES_NOT_EXECUTED_IN319')
        scratch=c.ROOT/'target/p09-font-inventory-scratch-320';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_INVENTORY_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='FONT_INVENTORY_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained_source_passes=9,new_cases=12,affected_product_cases=24)),flush=True)
        harness.run_one('font_inventory_public_helper_product36',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','--test-threads=1'],legacy|new,guard,env,row,observe_capture=previous.base.snapshot)
        tools.good_step(row['steps'][-1],legacy|new);c.require(not any(scratch.iterdir()),'FONT_INVENTORY_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_EXACT_HEADER_BODY_INVENTORY_NEW12_AFFECTED_PRODUCT24_RETAINED_SOURCE9_NOT_COMMON_COMPILER_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=12,affected_product_cases=24,retained_source_cases=9,unchanged_source_cases_not_replayed=11,production_changed_from319=False,
            next_work='bind_header_resource_dependencies_and_actual_body_owners_in_common_operation_compiler')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_INVENTORY_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_INVENTORY_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
