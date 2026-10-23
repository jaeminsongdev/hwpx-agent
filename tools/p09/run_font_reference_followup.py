"""Only one failed positive or one embedding diagnostic; retain original303 twelve passes."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_reference_valid_ids as previous
prior=previous.prior
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
DRIVER='tools/p09/run_font_reference_followup.py'
OLD='''    with_fonts(&output,|fonts|{
        for link in fonts.links(){let d=fonts.definitions().iter().find(|d|d.font_id==link.font_id).ok_or("output target")?;
            if let Some(m)=mappings.iter().find(|m|m.language==link.language){assert_eq!(d.declared.id,m.to_native_id);}}
        Ok(())
    })?;Ok(())
'''
NEW='''    with_fonts(original,|before|with_fonts(&output,|fonts|{
        assert_eq!(before.links().len(),fonts.links().len());let mut changed=0;
        for (old,link) in before.links().iter().zip(fonts.links()){
            let source=before.definitions().iter().find(|d|d.font_id==old.font_id).ok_or("original target")?;
            let target=fonts.definitions().iter().find(|d|d.font_id==link.font_id).ok_or("output target")?;
            assert_eq!(old.language,link.language);
            let expected=if let Some(m)=mappings.iter().find(|m|m.language==old.language&&m.from_native_id==source.declared.id){changed+=1;m.to_native_id}else{source.declared.id};
            assert_eq!(target.declared.id,expected);
        }
        assert_eq!(changed,c.receipt().changed_references);
        Ok(())
    }))?;Ok(())
'''

def main():
    c.require(sys.argv[1:]in [['--failed-positive'],['--embedding-diagnostic']],'CLOSED_FONT_FOLLOWUP_MODE')
    diagnostic=sys.argv[1]=='--embedding-diagnostic';run=305 if diagnostic else 304
    output=f'implementation/p09/evidence/p09-361-font-reference-followup{run}.v1.json'
    c.require(not(c.ROOT/output).exists(),'FONT_FOLLOWUP_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_FOLLOWUP',steps=[],own_cpu_selection=selection,diagnostic_only=diagnostic,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_or_scoped_product_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='6b46012c9acee2016331789eddb68e1f76fef7c2fe450228f5e37a9041298c11'and failed['cleanup'],'EXACT303_PARTIAL_RESULT')
        passed={n for n,s in failed['steps'][0]['tests']if s=='ok'};c.require(len(passed)==12,'RETAIN303_TWELVE_PASSES')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n not in {prior.TEST,prior.CORE}:c.require(q.snapshots[n]==old[n],'ALL_EXISTING_READERS_PROTECTION_PATCH_WRITER_AND_OTHER_INPUTS_UNCHANGED')
        text=q.text(prior.CORE)
        c.require(text.count('.map_err(|error| E::Patch(error.code()))')==3,'THREE_FIXED_CODE_ERROR_MAPPINGS')
        restored=text.replace('.map_err(|error| E::Patch(error.code()))','.map_err(|_| E::Patch)').replace(
            '#[error("FONT_REFERENCE_REPLACEMENT_PATCH_REJECTED:{0}")] Patch(&\'static str),','#[error("FONT_REFERENCE_REPLACEMENT_PATCH_REJECTED")] Patch,')
        audit.inverse(restored,old[prior.CORE],'ONLY_FIXED_ERROR_CODE_RETAINED_NO_ALGORITHM_BRANCH_OR_SUCCESS_PATH_CHANGE')
        text=q.text(prior.TEST);c.require(text.count(NEW)==1,'ONE_COMPLETE_SOURCE_EXPECTED_MAP_ASSERTION_FIX')
        audit.inverse(text.replace(NEW,OLD),old[prior.TEST],'ALL_OTHER13_TEST_BODIES_UNCHANGED')
        q.pin(DRIVER)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        name='embedded_declarations_and_binary_reference_remain_exact_without_activation'if diagnostic else'all_seven_language_axes_read_back_and_other_package_members_exact'
        c.require(name in {n for n,s in failed['steps'][0]['tests']if s=='FAILED'},'ONE_PREVIOUSLY_FAILED_CASE_ONLY')
        scratch=c.ROOT/f'target/p09-font-reference-scratch-{run}'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_FOLLOWUP_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_FOLLOWUP_PREFLIGHT',inputs=len(q.snapshots),selected_cases=1,retained_passes=12,diagnostic_only=diagnostic)),flush=True)
        harness.run_one('embedding_reference_diagnostic'if diagnostic else'failed_positive_source_mapping_recovery',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--',name,'--exact','--test-threads=1'],{name},guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],{name});c.require(not any(scratch.iterdir()),'FONT_FOLLOWUP_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REFERENCE_ONE_FAILED_CASE_RECOVERY_NOT_FULL_SEARCH_PRODUCT_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            newly_passed_cases=1,retained_passed_cases=12,remaining_original_failed_cases=1,official249_and_passed12_replayed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_FOLLOWUP_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_FOLLOWUP_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,output,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
