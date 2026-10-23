"""355: separate finite hash preimage and response bounds; failed1/new1/affected2, catalog3 not previously run."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_style_declarations as base
shared,c,a,tools,compact,harness,audit=base.shared,base.c,base.a,base.tools,base.compact,base.harness,base.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-declarations-recovery355.v1.json';DRIVER='tools/p09/run_named_style_declarations_recovery.py'
FAILED='entire_metadata_exact_byte_limit_and_one_byte_less_are_enforced';NEW_CASE='long_valid_query_binding_has_separate_bound_from_exact_public_response_bytes'
AFFECTED={'query_axis_and_original_source_bind_receipts_without_leaking_names_or_body','mapping_query_and_regex_budgets_fail_without_partial_resolution'}
BOUND='''// The request hash also consumes private names/catalog metadata not emitted in the response.
// Keep this finite fixed ceiling separate from the server's smaller public response byte budget.
const MAX_BINDING_BYTES:usize=4*1024*1024;
'''
def inverse(q,old):
    text=q.text(base.CORE);c.require(text.count(BOUND)==1,'ONE_FINITE_BINDING_PREIMAGE_CEILING');text=text.replace(BOUND,'')
    text=text.replace('self.receipt(),query,&from,&target),MAX_BINDING_BYTES)?','self.receipt(),query,&from,&target),limits.result_bytes)?')
    audit.inverse(text,old[base.CORE],'ALL_NAME_RESOLUTION_TYPED_RESOURCE_BINDINGS_HASH_PAYLOAD_OUTPUT_LIMITS_AND_AUTHORITY_FLAGS_UNCHANGED')
    text=q.text(base.TEST);start=text.index('// Independent private hash input and public response budget boundary begins.\n');end=text.index('// Independent private hash input and public response budget boundary ends.\n',start)+len('// Independent private hash input and public response budget boundary ends.\n')
    audit.inverse(text[:start]+text[end:],old[base.TEST],'ALL_ORIGINAL18_TEST_BODIES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_DECLARATION_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_DECLARATION_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        body_occurrences_or_target_semantics_qualified=False,source_document_mutation=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a36c0016568d8f350e1d465fbbf679a0b89d529c45ac35e36fe11a70c144bb37'and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==830
            and len(failed['steps'])==1 and {n for n,s in failed['steps'][0]['tests']if s=='FAILED'}=={FAILED}and sum(s=='ok'for n,s in failed['steps'][0]['tests'])==17,'EXACT354_SEVENTEEN_PASS_ONE_RESPONSE_BUDGET_FAILURE_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            q.pin(path)
            if path in old and path not in {base.CORE,base.TEST}:c.require(q.snapshots[path]==old[path],'ALL_OTHER_SOURCE_READERS_TESTS_OBSERVER_AND_RESOURCE_GUARDS_UNCHANGED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                p=Path(path).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        current=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));c.require(len(current)==19 and {FAILED,NEW_CASE}|AFFECTED<=current,'EXACT_CURRENT19_REPAIRED1_NEW1_AFFECTED2_RETAINED15')
        scratch=c.ROOT/'target/p09-named-style-declarations-recovery-scratch-355';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATION_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_DECLARATION_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),declaration_cases=4,retained=15,catalog_cases_not_previously_run=3)),flush=True)
        for binary,label,cases in [('named_style_declarations','named_declarations_failed1_new1_affected2',{FAILED,NEW_CASE}|AFFECTED),('document_import_catalog','original_catalog3_not_previously_run',base.AFFECTED)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',binary,'--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=base.snapshot)
            tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'NAMED_DECLARATION_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_DECLARATION_RECOVERED1_NEW1_AFFECTED2_RETAINED15_CATALOG3_NOT_BODY_BINDING_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_declaration_cases=4,retained_declaration_cases=15,distinct_current_declaration_cases=19,original_catalog_cases=3,current_access_execution_or_publication_authority=False,
            next_work='qualified_original_character_style_before_after_capture_then_exact_body_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_DECLARATION_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_DECLARATION_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
