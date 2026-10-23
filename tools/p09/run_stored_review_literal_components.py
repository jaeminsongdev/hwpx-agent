"""Six current stored review-body literal cases; keep completed32 core cases intact."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_literal_components as prior
import run_stored_literal_text_atom_components as boundary
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-stored-review-literal-components082.v1.json'
PRIOR=prior.OUTPUT
PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms.rs'
SOURCE=PARENT[:-3]+'/review.rs'
MODULE='crates/product-cli/tests/form_stored_provider/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/review_literal_output.rs'
NEW={SOURCE,TEST};CHANGED={PARENT,MODULE}


def inventory(check):return prior.inventory(check)


def inverse(q,old):
    for name,addition in ((PARENT,'pub mod review;\n'),(MODULE,'#[path = "actual_import/review_literal_output.rs"]\nmod review_literal_output;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONE_ADDITIVE_STORED_REVIEW_LITERAL_MODULE')
        prior.audit.inverse(text.replace(addition,''),old[name],'ORIGINAL_V2_STORED_ACCESS_AND_TEST_MODULE_BODIES_EXACT_INVERSE')
    original=q.text(PARENT);new=q.text(SOURCE);prepared=boundary.body(new,'prepare_review_literal_candidate')
    for current,previous in (('lower_review_literal_candidate','lower_literal_text_atom_candidate'),('query,scope,policy,replacement','query,scope,replacement'),
        ('output.receipt().output.source_package_sha256','output.receipt().source_package_sha256'),('StoredReviewLiteralReceipt','StoredLiteralTextAtomReceipt'),
        ('hwpx-agent.stored-literal-search-candidate/v3','hwpx-agent.stored-literal-search-candidate/v2'),
        ('PreparedStoredReviewLiteralCandidate','PreparedStoredLiteralTextAtomCandidate'),('source:super::super::product::LiteralSource::Borrowed','source:super::product::LiteralSource::Borrowed')):
        c.require(prepared.count(current)==1,'ONE_TYPED_REVIEW_RECEIPT_POLICY_OR_OWNER_SUBSTITUTION');prepared=prepared.replace(current,previous)
    c.require(prepared==boundary.body(original,'prepare_literal_text_atom_candidate'),'SAME_CURRENT_WRITE_SOURCE_PROOF_SOURCE_SHA_AND_FINAL_PREPARE_HEAD_BODY')
    fresh=boundary.body(new,'fresh');extra='\n            ||self.receipt.output.native_author_visibility_resolution_or_execution_qualified||!self.receipt.output.memo_payload_not_cached_result_verified'
    c.require(fresh.count(extra)==1 and fresh.count('self.receipt.output.output.')==5,'EXACT_NESTED_REVIEW_RECEIPT_AND_CLOSED_V3_FLAGS')
    c.require(fresh.replace(extra,'').replace('self.receipt.output.output.','self.receipt.output.')==boundary.body(original,'fresh'),
        'SAME_FRESH_SOURCE_ACL_AEAD_BINDING_BODY_PLUS_CLOSED_REVIEW_FLAGS')
    for name in ('verify','with_verified_bytes','require_current_product_route'):
        c.require(boundary.body(new,name)==boundary.body(original,name),'SAME_WRITER_INTEGRITY_FINAL_CONSUMER_HEAD_AND_DENIED_ROUTE_BODY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_REVIEW_LITERAL_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVIEW_LITERAL_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
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
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='4ce628eb5aa3ebc2cfd8b5a604502a1548ce81264fdbeb7811088cd03936e8c2'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==32,'EXACT_PREVIOUS_TWELVE_NEW_TWENTY_AFFECTED_CORE_PASSES')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_STORED_REVIEW_LITERAL_SOURCE_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_REVIEW_PROJECTION_FIELD_CACHE_SCALAR_OR_EXISTING_PRODUCT_CHANGE')
        inverse(q,old)
        tests={'actual_import::review_literal_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
        c.require(len(tests)==6,'EXACT_SIX_NEW_STORED_REVIEW_LITERAL_CASES');env=prior.audit.environment()
        print(json.dumps(dict(state='STORED_REVIEW_LITERAL_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=6,retained_core_cases=32,original_access_and_final_head_bodies_verified=True)),flush=True)
        harness.run_one('six_current_stored_review_literal_candidate_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(tests),'--exact','--test-threads=1'],tests,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_STORED_REVIEW_LITERAL_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_REVIEW_LITERAL_SIX_NEW_THIRTY_TWO_CORE_RETAINED_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_stored_cases=6,total_executed_cases=6,retained_core_cases=32,
            original_access_source_writer_and_final_head_method_bodies_verified=True,field_cache_and_native_metadata_grants_not_added=True,
            current_acl_quarantine_aead_and_three_head_boundaries_exercised=True,
            query_lowering_or_review_projection_repeated_during_delivery=False,existing_product_and_stored_tests_reexecuted=False,
            product_json_cli_cas_or_execution_route_added=False,next_work='Strict_v3_review_literal_product_JSON_with_explicit_body_policy_and_owned_source')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVIEW_LITERAL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORED_REVIEW_LITERAL_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
