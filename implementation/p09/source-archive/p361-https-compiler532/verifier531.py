"""531: original common compiler/owner logic for HTTPS, new5+affected5; retain unchanged early-denial4."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_https_target_compiler.py'
OUTPUT='implementation/p09/evidence/p09-361-https-target-compiler531.v1.json'
BASE='implementation/p09/evidence/p09-361-stored-https-target530.v1.json'
STORED='crates/product-cli/src/form_stored_provider/actual_import/https_target_output.rs'
COMPILED=STORED[:-3]+'/compiled.rs'
SEARCH='crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs'
OWNERS=SEARCH[:-3]+'/owners.rs'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
TEST='crates/product-cli/tests/support/stored_https_compiler.rs'
ARCHIVE='implementation/p09/source-archive/p361-https-compiler531/'
CHANGED={STORED:'stored.rs',SEARCH:'search.rs',OWNERS:'owners.rs',HOST:'test.rs'}
CONTRACT='protocol/private/p09-hyperlink-hwpx-v1.json'
AFFECTED={'captured_source_actual_encrypted_policy_and_output_readback_do_not_publish',
    'stored_batch_preserves_unselected_field_and_rejects_one_unapproved_member_atomically',
    'candidate_delivery_rechecks_both_acls_repository_revocation_scope_and_latest_version',
    'policy_revocation_during_preparation_or_final_delivery_never_exposes_bytes',
    'changed_stored_head_denies_delivery_and_does_not_replace_newer_revision'}

def inverse(q):
    text=q.text(STORED).replace('pub mod compiled;\n','').replace(',anchors:Vec<domain_ir::SourceAnchorHandle>','')
    text=text.replace('        let anchors=compiled::selected_anchors(&fields,output.receipt())?;\n','').replace('receipt,anchors})','receipt})')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'stored.rs'],'HTTPS531_ORIGINAL_STORED_POLICY_ACL_AEAD_SOURCE_LOWER_AND_DELIVERY_UNCHANGED')
    text=q.text(SEARCH).replace('pub(crate) use owners::resolve_original_source_owners;\n','').replace('pub(crate) fn bounded_hash','pub(super) fn bounded_hash')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'search.rs'],'HTTPS531_ENTIRE_ORIGINAL_SEARCH_COMPILER_AND_HASH_BODY_UNCHANGED')
    text=q.text(OWNERS);start=text.index('// Shared original resolver,');end=text.index('pub(super) fn resolve(',start)
    r.audit.inverse(text[:start]+text[end:],q.snapshots[ARCHIVE+'owners.rs'],'HTTPS531_ENTIRE_ORIGINAL_OWNER_RESOLVER_UNCHANGED')
    r.audit.inverse(q.text(HOST).replace('#[path="support/stored_https_compiler.rs"]mod compiled;\n',''),q.snapshots[ARCHIVE+'test.rs'],
        'HTTPS531_ALL_NINE_ORIGINAL_STORED_TEST_BODIES_AND_FIXTURES_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS531_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_TARGET_COMPILER',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,official249_SQL520_or_previous_Native_replayed=False,
        external003_cleanup_or_claim_changed=False,operating_policy_issuer_registry_manifest_job_CAS_route_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='a31381e4b75bd6588eacc3a8c09d35c0be9cd76b9aa3245a22d92bb825ce8642'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==831 and base['distinct_qualified_cases']==9,
            'HTTPS531_EXACT_ORIGINAL530_ACCEPTANCE_RETAINED')
        names=inventory.inventory(guard)|{SELF,BASE,STORED,COMPILED,SEARCH,OWNERS,HOST,TEST,CONTRACT,deps.CAPTURE}|{ARCHIVE+v for v in CHANGED.values()}
        names|=includes.test_inputs((HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/'):continue
            if '/src/'not in pin['path']and pin['path']!=HOST:continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS531_ALL_ORIGINAL530_LIBRARY_INPUTS_PRESERVED')
        inverse(q)
        c.require(q.json(CONTRACT)['capability_features']['REF-034']=='ref.hyperlink_edit','HTTPS531_EXISTING_REF034_FEATURE_ID')
        old=helpers.tests(q,HOST);new=helpers.tests(q,TEST,'compiled::');retained=old-AFFECTED
        c.require((len(old),len(new),len(retained))==(9,5,4)and AFFECTED<=old,'HTTPS531_NEW_FIVE_AFFECTED_FIVE_RETAINED_EARLY_DENIAL_FOUR')
        row.update(retained_unchanged_early_denial_cases=4,retained_case_names=sorted(retained),new_cases=5,affected_cases=5,unchanged_early_denial_four_replayed=False,
            affected_preparation_five_replayed_because_selected_anchor_retention_changed=True)
        cases=new|AFFECTED;guard.check(force=True);scratch=c.ROOT/'target/p09-https-compiler-scratch531'
        c.require(not scratch.exists(),'HTTPS531_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_COMPILER_PREFLIGHT',inputs=len(q.snapshots),current_cases=len(cases),retained_early_denial=4,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('https_target_common_compiler',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS531_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS531_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS531_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS531_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_TARGET_COMMON_COMPILER_CURRENT_TEN_RETAINED_FOUR_NOT_ROUTE_NATIVE_OR_GATE',current_qualified_cases=len(cases),distinct_qualified_cases=len(old|new),
            actual_common_owner_resolver_and_operation_compiler=True,source_or_head_published_by_candidate=False,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS531_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
