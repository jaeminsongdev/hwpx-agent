"""Strict literal product request: nine new product and six affected borrowed cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_search_output_components as prior
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-literal-replacement-product-components070.v1.json'
PRIOR=prior.OUTPUT
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/literal_replacement_product.rs'
LOWER='crates/hwpx-package/src/document_import/search/replacement.rs'
STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
MODULE='crates/product-cli/tests/form_stored_provider/actual_import.rs'
ROOT='crates/product-cli/src/form_product_request.rs'
NEW={PRODUCT,'crates/product-cli/src/form_product_request/stored_literal_replacement.rs',STORED[:-3]+'/product.rs'}
CHANGED={LOWER,STORED,MODULE,ROOT}
POLICY=('/// # Errors\n/// Pure preflight shared by product parsing and lowering; never a source or access grant.\n'
    'pub fn validate_literal_replacement(replacement:&str)->Result<(),SourceLiteralReplacementError> {\n'
    '    if replacement.len()>PatchLimits::default().config().max_value_bytes{return Err(E::Limit);}\n'
    '    PatchText::new(replacement).map_err(|_|E::Value)?;\n'
    '    crate::text_flow::validate_text(replacement).map_err(|_|E::Value)\n}\n')
INLINE=('        if replacement.len()>PatchLimits::default().config().max_value_bytes{return Err(E::Limit);}\n'
    '        PatchText::new(replacement).map_err(|_|E::Value)?;\n'
    '        crate::text_flow::validate_text(replacement).map_err(|_|E::Value)?;\n')


def inventory(check):return prior.inventory(check)


def inverse(q,old):
    text=q.text(LOWER);call='        validate_literal_replacement(replacement)?;\n'
    c.require(text.count(POLICY)==1 and text.count(call)==1,'ONLY_EXACT_ORIGINAL_VALUE_POLICY_EXTRACTION')
    prior.base.inverse(text.replace(POLICY,'').replace(call,INLINE),old[LOWER],'ORIGINAL_CORE_LITERAL_COMPILER_AND_VALUE_POLICY_EXACT_INVERSE')
    text=q.text(STORED)
    for current,original in (('mod product;\n',''),('source:product::LiteralSource<\'a>,','source:&\'a StoredImportedDocumentForms,'),
        ('source:product::LiteralSource::Borrowed(self),','source:self,')):
        c.require(text.count(current)==1,'ONLY_BORROWED_OWNED_SOURCE_WRAPPER_EXTENSION');text=text.replace(current,original)
    prior.base.inverse(text,old[STORED],'ORIGINAL_LITERAL_PREPARATION_ACCESS_AND_DELIVERY_METHODS_EXACT_INVERSE')
    for path,addition in ((ROOT,'pub mod stored_literal_replacement;\n'),(MODULE,'#[path = "actual_import/literal_replacement_product.rs"]\nmod literal_replacement_product;\n')):
        text=q.text(path);c.require(text.count(addition)==1,'ONE_ADDITIVE_LITERAL_PRODUCT_MODULE');prior.base.inverse(text.replace(addition,''),old[path],'ORIGINAL_OTHER_PRODUCT_AND_TEST_MODULES_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_REPLACEMENT_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='86542bf1921e5a80ef75202b3cfa1009b0eb99a6036475c6d72386d1ce9735fd'
            and previous['state'].startswith('PASS_')and previous['cleanup'],'EXACT_PRIOR_ACTUAL_LITERAL_OUTPUT_PASS')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.scalar.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_LITERAL_PRODUCT_SOURCE_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_CORE_SEARCH_SCALAR_TEST_OR_HEADER_CHANGE')
        inverse(q,old)
        product={'actual_import::literal_replacement_product::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        borrowed={'actual_import::literal_search_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(prior.PRODUCT))}
        c.require(len(product)==9 and len(borrowed)==6 and {n for n,s in previous['steps'][1]['tests']}==borrowed
            and all(s=='ok'for n,s in previous['steps'][1]['tests']),'EXACT_NINE_NEW_SIX_AFFECTED_AND_PREVIOUS_SIX_IDENTITIES')
        env=prior.base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--']
        print(json.dumps(dict(state='LITERAL_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=9,affected_cases=6,original_core_value_policy_and_access_bodies_preserved=True)),flush=True)
        harness.run_one('nine_strict_owned_literal_product_request_cases',common+[*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        harness.run_one('six_affected_borrowed_literal_candidate_cases',common+[*sorted(borrowed),'--exact','--test-threads=1'],borrowed,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_LITERAL_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_LITERAL_REPLACEMENT_PRODUCT_NINE_NEW_SIX_AFFECTED_CORE_TEN_RETAINED_NOT_FULL_SEARCH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=9,affected_borrowed_cases=6,total_executed_cases=15,
            original_core_policy_and_stored_access_methods_inverse_verified=True,source_ownership_transferred_without_clone_or_reimport=True,
            prior_core_cases_reexecuted=False,raw_canonical_and_provider_scope_digests_bound=True,invalid_request_rejected_before_artifact_reads=True,
            idempotency_key_claimed=False,command_line_or_server_route_added=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_PRODUCT_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
