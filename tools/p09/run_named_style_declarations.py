"""354: exact PARA/CHAR declaration/resource resolver18 + existing catalog3, no body semantics/Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-declarations354.v1.json';DRIVER='tools/p09/run_named_style_declarations.py'
BASE='implementation/p09/evidence/p09-361-compiled-named-style-options351.v1.json';RECONCILED='implementation/p09/evidence/p09-361-compiled-named-style-options-reconciled352.v1.json'
PARENT='crates/hwpx-package/src/document_import/fields/semantics/catalog.rs';CORE=PARENT[:-3]+'/named_styles.rs';TEST='crates/hwpx-package/tests/named_style_declarations.rs';OLD_TEST='crates/hwpx-package/tests/document_import_catalog.rs'
RUNTIME='tools/p09/named_style_verification_runtime.py';NEW={DRIVER,CORE,TEST}
OFFICIAL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/'
REFERENCES={OFFICIAL+'Class/Head/StyleType.cpp',OFFICIAL+'Class/Para/t.cpp',OFFICIAL+'Class/Para/ctrl.cpp',OLD_TEST}
AFFECTED={'each_body_style_paragraph_and_character_reference_must_resolve','each_named_style_relationship_resolves_without_guessing_inheritance','duplicate_named_ids_and_declared_counts_are_rejected'}

def inverse(q,old):
    text=q.text(PARENT);c.require(text.count('pub mod named_styles;\n')==1,'ONE_NAMED_DECLARATION_MODULE_EXPORT');audit.inverse(text.replace('pub mod named_styles;\n',''),old[PARENT],'ALL_ORIGINAL_CATALOG_READERS_RESOURCE_DOMAIN_RELATIONSHIPS_AND_ADMISSION_UNCHANGED')

def snapshot(capture,expected):
    result=r.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    result['closed_named_style_name_errors']=sorted(set(re.findall(r'\bNAMED_STYLE_NAME_[A-Z_]{1,64}\b',raw)));return result

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_DECLARATIONS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_DECLARATIONS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        body_occurrences_or_target_semantics_qualified=False,source_document_mutation=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);original=compact.unpack(q.json(BASE));recovered=q.json(RECONCILED)
        c.require(q.snapshots[BASE]['sha256']=='11bbf8033db14c59af5f439e6d1aef70705865ca1c0d6d9fb99641879481051f'and original['cleanup']and original['fresh_inputs']==original['final_fresh_hashes']==821,'EXACT351_ORIGINAL_FULL_SOURCE_CLOSURE_AND_FAILURE_RETAINED')
        c.require(q.snapshots[RECONCILED]['sha256']=='c15c8ffc2918b884f0c08a27884255d6cd871ad6dd07cd1757c166cbbd2d026f'and recovered['cleanup']and recovered['original_case_count']==27,'EXACT352_ORIGINAL27_RECONCILIATION_WITH_FIXED_RUNTIME')
        old={p['path']:p for p in original['source_pins']};fixed={p['path']:p for p in recovered['source_pins']};c.require(RUNTIME in old and RUNTIME in fixed,'EXACT_RUNTIME_FIX_IS_EXPLICIT')
        old[RUNTIME]=fixed[RUNTIME]
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|REFERENCES):
            q.pin(path)
            if path in old and path!=PARENT:c.require(q.snapshots[path]==old[path],'ALL_OTHER_PRODUCT_NATIVE_GUARDS_READERS_TESTS_AND_FIXED_RUNTIME_UNCHANGED')
            elif path not in old:c.require(path in NEW|REFERENCES,'ONLY_DECLARATION_RESOLVER_TEST_DRIVER_AND_EXPLICIT_REFERENCE_INPUTS_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                p=Path(path).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==18 and len(AFFECTED)==3,'EXACT_NEW18_DECLARATION_AND_AFFECTED3_CATALOG_CASES')
        scratch=c.ROOT/'target/p09-named-style-declarations-scratch-354';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_DECLARATIONS_PREFLIGHT',inputs=len(q.snapshots),new_cases=18,affected_cases=3)),flush=True)
        for binary,label,selected in [('named_style_declarations','named_declarations18',cases),('document_import_catalog','affected_original_catalog3',AFFECTED)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'NAMED_DECLARATIONS_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARA_CHAR_DECLARATION_RESOURCES18_AFFECTED_CATALOG3_NOT_BODY_BINDING_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=18,affected_cases=3,current_access_execution_or_publication_authority=False,
            next_work='qualified_original_character_style_before_after_capture_then_exact_body_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_DECLARATIONS_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_DECLARATIONS_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
