"""362: explicit original selection masking25 + shared protection/control/preservation3, no Native/PII inputs."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-mask362.v1.json';DRIVER='tools/p09/run_personal_info_mask.py'
BASE='implementation/p09/evidence/p09-361-named-declarations-product-isolated359.v1.json'
DOCS='implementation/p09/evidence/p09-361-named-declarations-product-sync-recovery361.v1.json'
PARENT='crates/hwpx-package/src/document_import/search/replacement/atoms.rs';CORE=PARENT[:-3]+'/personal_info.rs';TEST='crates/hwpx-package/tests/personal_info_mask.rs'
NEW={DRIVER,CORE,TEST};OLD_TEST='crates/hwpx-package/tests/document_import_unicode_normalization.rs'
AFFECTED={'unicode_ancestor_tracking_is_checked_before_noop_elimination','unicode_tabs_and_paired_linebreaks_are_immutable_normalization_barriers',
    'unicode_selected_component_preserves_outside_decomposed_text_and_entity_spelling'}

def inverse(q,old):
    text=q.text(PARENT);line='pub mod personal_info;\n';c.require(text.count(line)==1,'ONE_PERSONAL_INFO_MASK_MODULE_EXPORT')
    audit.inverse(text.replace(line,''),old[PARENT],'ALL_ORIGINAL_TEXT_ATOM_EDITING_WRITER_READBACK_PROTECTION_AND_EXISTING_CONVERSION_CODE_UNCHANGED')

def main(scratch_relative='target/p09-personal-info-mask-scratch-362'):
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_MASK_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_MASK',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        synthetic_markers_not_actual_personal_data=True,source_document_mutation=False,output_ingest_commit_or_publication=False,
        whole_package_personal_data_removed=False,native_mask_semantics_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PERSONAL_INFO_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='278695e20b8d3406dc28b9a6f483cfad44ffc73ebadde06a1e53c34119f09cfe'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==842,'EXACT359_FULL_SOURCE_BASELINE_TERMINAL')
        c.require(q.snapshots[DOCS]['sha256']=='639b2e837e1f51d46124788c68fe7388ecefbf26dfe42cff990633a3bcda79f5'and docs['cleanup'],'EXACT361_CURRENT_DOC_BASELINE')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|{OLD_TEST}):
            q.pin(path)
            if path in old and path!=PARENT:c.require(q.snapshots[path]==old[path],'ALL_OTHER_SOURCE_READERS_PROTECTION_PLANNER_WRITERS_PRODUCT_TESTS_AND_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW|{OLD_TEST},'ONLY_SELECTION_MASK_CORE_TEST_DRIVER_AND_EXPLICIT_ORIGINAL_REGRESSION_INPUT_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                p=Path(path).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==25,'EXACT25_MASK_SELECTION_CONTROL_NFC_PRIVACY_AND_RESOURCE_CASES')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='PERSONAL_INFO_MASK_PREFLIGHT',inputs=len(q.snapshots),new_cases=25,affected_cases=3)),flush=True)
        for binary,label,selected in [('personal_info_mask','personal_info_selection_mask25',cases),('document_import_unicode_normalization','shared_original_protection_control_and_preservation3',AFFECTED)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'PERSONAL_INFO_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SELECTION_PERSONAL_INFO_MASK25_SHARED_BOUNDARY3_NOT_NATIVE_PACKAGE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=25,affected_cases=3,current_service_execution_or_publication_authority=False,
            next_work='current_stored_service_and_strict_personal_info_mask_product_then_full_scope_and_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_MASK_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'PERSONAL_INFO_MASK_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
