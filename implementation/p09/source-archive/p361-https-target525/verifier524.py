"""524: policy-bound source HTTPS target batch through original patch/writer, no Native/SQL/URL access."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as previous
import search_sql_receipt as layout
SELF='tools/p09/verify_source_https_targets.py'
OUTPUT='implementation/p09/evidence/p09-361-source-https-target524.v1.json'
BASE='implementation/p09/evidence/p09-361-source-field-semantics523.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-https-target524/'
CHANGED={'crates/domain-ir/src/link_reference.rs':'domain.rs','crates/hwpx-package/src/hyperlink_hwpx.rs':'hyperlink.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/source_index.rs':'index.rs',
    'crates/hwpx-package/src/document_import/search/replacement.rs':'replacement.rs',
    'crates/hwpx-package/src/document_import/search/replacement/font_profile.rs':'font-profile.rs',
    'crates/product-cli/src/reference_validation_product/source_field_semantics.rs':'product.rs'}
CORE='crates/hwpx-package/tests/source_https_target_changes.rs'
PRODUCT='crates/product-cli/tests/source_https_target_product.rs'
POLICY='crates/domain-ir/tests/external_target_policy.rs'
LOWER='crates/hwpx-package/src/document_import/fields/semantics/source_index/https_targets.rs'
CAPTURE=previous.CAPTURE

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS524_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;row=dict(state='FAILED_SOURCE_HTTPS_TARGETS',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_Hancom_COM_SQL_Native_or_network_started=False,
        official249_SQL520_or_previous_tests_replayed=False,external003_cleanup_or_claim_changed=False,
        production_policy_issuer_scanner_registry_route_or_native_update_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='9b8bda3b1aa5f8dbaef2078163fd3fe879770ec68740a08e7273aae5da3de15a'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==849 and base['qualified_cases']==15,'HTTPS524_EXACT523_ORIGINAL_ACCEPTANCE')
        names=inventory.inventory(guard)|{SELF,BASE,CORE,PRODUCT,POLICY,LOWER,CAPTURE}|{ARCHIVE+name for name in CHANGED.values()}
        names|=includes.test_inputs((CORE,PRODUCT,POLICY),guard)
        for path in sorted(names):q.pin(path)
        c.require(q.snapshots[CAPTURE]['sha256']=='feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480','HTTPS524_IMMUTABLE_CAPTURE')
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/')or '/src/'not in pin['path']:continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS524_PRIOR_CHANGED_AND_UNRELATED_LIBRARY_CODE_PRESERVED')
        text=q.text('crates/domain-ir/src/link_reference.rs');start=text.index('impl ExternalLinkPolicy {');end=text.index('\n}\n',start)+4
        r.audit.inverse(text[:start]+text[end:],q.snapshots[ARCHIVE+'domain.rs'],'HTTPS524_ORIGINAL_POLICY_AND_STATE_RULES_UNCHANGED')
        text=q.text('crates/hwpx-package/src/hyperlink_hwpx.rs');start=text.index('/// Exact original six-parameter profile, yielding only the two existing content leaves.');end=text.index('fn validate_parameters(',start)
        r.audit.inverse(text[:start]+text[end:],q.snapshots[ARCHIVE+'hyperlink.rs'],'HTTPS524_ORIGINAL_NATIVE_PROFILE_READERS_AND_WRITER_UNCHANGED')
        r.audit.inverse(q.text('crates/hwpx-package/src/document_import/fields/semantics/source_index.rs').replace('pub mod https_targets;\n',''),
            q.snapshots[ARCHIVE+'index.rs'],'HTTPS524_ORIGINAL_MEANING_INDEX_UNCHANGED')
        r.audit.inverse(q.text('crates/hwpx-package/src/document_import/search/replacement.rs').replace('pub(in crate::document_import) mod font_profile;','mod font_profile;'),
            q.snapshots[ARCHIVE+'replacement.rs'],'HTTPS524_ORIGINAL_SEARCH_OPERATIONS_UNCHANGED')
        r.audit.inverse(q.text('crates/hwpx-package/src/document_import/search/replacement/font_profile.rs').replace('pub(in crate::document_import) fn select','pub(super) fn select'),
            q.snapshots[ARCHIVE+'font-profile.rs'],'HTTPS524_ORIGINAL_FONT_ID_PROFILE_SELECTION_UNCHANGED')
        text=q.text('crates/product-cli/src/reference_validation_product/source_field_semantics.rs');start=text.index('    /// Produces an owned candidate only,');end=text.index('    /// Reads exact source-derived supported meanings once',start)
        r.audit.inverse(text[:start]+text[end:],q.snapshots[ARCHIVE+'product.rs'],'HTTPS524_ORIGINAL_READ_ONLY_API_UNCHANGED')
        domain=helpers.tests(q,POLICY);core=helpers.tests(q,CORE);product=helpers.tests(q,PRODUCT)
        c.require((len(domain),len(core),len(product))==(3,8,4),'HTTPS524_NEW15_EXACT_CASES')
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.301693333880961,'HTTPS524_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-https-target-scratch524';c.require(not scratch.exists(),'HTTPS524_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='SOURCE_HTTPS_PREFLIGHT',inputs=len(q.snapshots),new_cases=15,CPU_cap_percent=6.25)),flush=True)
        row['actual_compile_inputs']=[]
        for package,target,cases in [('domain-ir','external_target_policy',domain),('hwpx-package','source_https_target_changes',core),('hwpx-agent-cli','source_https_target_product',product)]:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,args,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS524_NO_COMPILER_WARNINGS')
            found=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=previous.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS524_ALL_ACTUAL_DEPENDENCIES_PREPINNED')
                found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
            c.require(len(found)==1,'HTTPS524_ONE_CURRENT_NEW_HOST_DEP_INFO');row['actual_compile_inputs'].extend(found)
        c.require(not any(scratch.iterdir()),'HTTPS524_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_HTTPS_TARGET_BATCH_POLICY_AND_PRODUCT15_NOT_NATIVE_OR_GATE',qualified_cases=15,new_cases=15,
            actual_original_source_target_edits_and_readback=True,source_overwritten=False,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS524_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
