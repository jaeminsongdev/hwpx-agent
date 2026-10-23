"""521: scoped IO/receipt models only. SQL520 body is preserved, not replayed or promoted."""
import ast,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import search_sql_receipt as codec
OUTPUT='implementation/p09/evidence/p09-361-search-sql-receipt521.v1.json'
BODY='target/p09-common-search-sql24-observation-520.json'
FAILURE='implementation/p09/evidence/p09-361-search-sql520-publication-failure.v1.json'
TESTS=('tools/p09/tests/test_paced_postgres_hash.py','tools/p09/tests/test_search_sql_receipt.py')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'SQL_RECEIPT521_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_SQL_RECEIPT_MODELS',steps=[],resource_samples=[],
        own_cpu_selection=selection,actual_SQL_or_Cargo_or_Hancom_started=False,SQL520_body_replayed=False,
        SQL520_parent_source_closure_reconstructed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names={BODY,FAILURE,*TESTS,'tools/p09/verify_search_sql_receipt.py','tools/p09/verify_search_request_sql.py',
            'tools/p09/paced_postgres_hash.py','tools/p09/search_sql_receipt.py','tools/p09/native_postgres_search_request_recovery.py',
            'implementation/p09/source-archive/p361-search-sql521/verifier520.py'}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                p=Path(value).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':names.add(p.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        body=q.json(BODY);failure=q.json(FAILURE)
        c.require(q.snapshots[BODY]['sha256']=='815fcfe5f797a2980ec0879099e420ba1d1a70acf09b787dafe003b713e986df'
            and body['all_owned_postmasters_normal_stop']is True and body['common_search_SQL_cases']==1,'SQL_RECEIPT521_ORIGINAL_BODY_EXACT_NOT_PARENT_CLOSURE')
        c.require(failure['full_current_source_SQL_qualification']is False and failure['parent_receipt_created']is False
            and q.snapshots[failure['original_parent_verifier']]['sha256']==failure['original_parent_verifier_sha256'],'SQL_RECEIPT521_FAILURE_NOT_PROMOTED')
        model_rows=[]
        for i,path in enumerate(TESTS):
            ast.parse(q.text(path));spec=importlib.util.spec_from_file_location('sql_receipt_models_'+str(i),str(c.ROOT/path))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=unittest.TestResult()
            unittest.defaultTestLoader.loadTestsFromTestCase(module.Models).run(result)
            model_rows.append(dict(tests=result.testsRun,errors=len(result.errors),failures=len(result.failures)))
            c.require(result.testsRun==[7,6][i]and not result.errors and not result.failures,'SQL_RECEIPT521_MODELS_PASS_WITHOUT_SQL')
            if i==1:
                fixture=module.fixture();packet=codec.pack(fixture)
                row['large_receipt_model']=dict(source_pins=1062,resource_samples=1210,
                    published_bytes=len((json.dumps(packet,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()),
                    original_cap_bytes=262144,all_values_and_types_roundtrip=True,external_carrier=False)
        q.finish();guard.check(force=True)
        row.update(state='PASS_IO_AND_LOSSLESS_RECEIPT_MODELS13_NOT_SQL_SOURCE_CLOSURE_OR_GATE',models=model_rows,
            original_SQL_body_observed=body['state'],original_SQL_body_normal_stop=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'SQL_RECEIPT521_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,codec.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','large_receipt_model')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
