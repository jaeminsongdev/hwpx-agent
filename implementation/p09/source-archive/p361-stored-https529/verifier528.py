"""528: repair test-only match arm types; preserve527 compile failure; only new nine cases."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_stored_https_targets.py'
OUTPUT='implementation/p09/evidence/p09-361-stored-https-target528.v1.json'
BASE='implementation/p09/evidence/p09-361-source-https-target526.v1.json'
PARENT='crates/product-cli/src/form_stored_provider/actual_import.rs'
NEW='crates/product-cli/src/form_stored_provider/actual_import/https_target_output.rs'
TEST='crates/product-cli/tests/stored_https_target_product.rs'
ARCHIVE='implementation/p09/source-archive/p361-stored-https527/actual-import.rs'
CAPTURE=deps.CAPTURE

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'STORED_HTTPS527_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=artifact=None
    row=dict(state='FAILED_STORED_HTTPS_TARGET',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,previous526_tests_or_official249_replayed=False,
        external003_cleanup_or_claim_changed=False,operating_repository_issuer_scanner_atomic_policy_lease_compiler_CAS_or_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='466fdbf0c9ed7bbb0fc2099917ebb387d2f41025046bee6ac58195ed85229b40'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==836,'STORED_HTTPS527_EXACT526_ACCEPTANCE_RETAINED')
        failed='implementation/p09/evidence/p09-361-stored-https-target527.v1.json';saved='implementation/p09/source-archive/p361-stored-https528/'
        names=inventory.inventory(guard)|{SELF,BASE,PARENT,NEW,TEST,ARCHIVE,CAPTURE,failed,saved+'test527.rs',saved+'verifier527.py'}|includes.test_inputs((TEST,),guard)
        for path in sorted(names):q.pin(path)
        prior=layout.unpack(q.json(failed));c.require(q.snapshots[failed]['sha256']=='747e264601f2a5216eeb092630a8835c2596eea33b8bb608c671c376af2b6cc0'
            and prior['cleanup']is True and prior['final_fresh_hashes']==0 and prior['steps'][0]['exit_code']==101
            and prior['steps'][0]['tests']==[],'STORED_HTTPS528_ORIGINAL_COMPILE_FAILURE_NO_TESTS_EXECUTED')
        for pin in prior['source_pins']:
            actual=q.snapshots[saved+'test527.rs']if pin['path']==TEST else q.snapshots[saved+'verifier527.py']if pin['path']==SELF else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'STORED_HTTPS528_ORIGINAL_PRODUCT_AND_INPUTS_RETAINED')
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/')or '/src/'not in pin['path']:continue
            actual=q.snapshots[ARCHIVE]if pin['path']==PARENT else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'STORED_HTTPS527_ALL_ORIGINAL_PRODUCT_AND_GUARD_CODE_PRESERVED')
        r.audit.inverse(q.text(PARENT).replace('pub mod https_target_output;\n',''),q.snapshots[ARCHIVE],'STORED_HTTPS527_PARENT_ONLY_NEW_MODULE')
        c.require(q.snapshots[CAPTURE]['sha256']=='feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480','STORED_HTTPS527_IMMUTABLE_SOURCE')
        cases=helpers.tests(q,TEST);c.require(len(cases)==9,'STORED_HTTPS527_EXACT_NINE_NEW_CASES')
        guard.check(force=True);scratch=c.ROOT/'target/p09-stored-https-scratch528'
        c.require(not scratch.exists(),'STORED_HTTPS527_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='STORED_HTTPS_PREFLIGHT',inputs=len(q.snapshots),new_cases=len(cases),CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('stored_https_target_product',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'STORED_HTTPS527_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'STORED_HTTPS527_ALL_COMPILER_INPUTS_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'STORED_HTTPS527_ONE_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'STORED_HTTPS527_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_HTTPS_TARGET_NINE_NOT_SQL_ISSUER_CAS_NATIVE_OR_GATE',qualified_cases=len(cases),actual_encrypted_artifact_policy_and_source_reads=True,
            source_or_head_published_by_candidate=False,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'STORED_HTTPS527_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
