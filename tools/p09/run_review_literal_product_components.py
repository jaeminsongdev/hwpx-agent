"""Ten strict v3 product cases + nineteen affected v1/v2 + six original borrowed cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_review_literal_focused as prior
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-review-literal-product-components088.v1.json'
PRIOR=prior.OUTPUT
PARSER='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PRODUCT=PARSER[:-3]+'/review.rs'
STORED=prior.base.SOURCE
OWNER=STORED[:-3]+'/product.rs'
TARGET='crates/product-cli/tests/review_literal_product.rs'
WRAPPER='crates/product-cli/tests/review_literal_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/review_literal_product.rs'
V1='crates/product-cli/tests/form_stored_provider/actual_import/literal_replacement_product.rs'
V2='crates/product-cli/tests/form_stored_provider/actual_import/literal_text_atom_product.rs'
NEW={PRODUCT,OWNER,TARGET,WRAPPER,TEST};CHANGED={PARSER,STORED}
PARSE_BRIDGE='        Self::parse_value(Self::parse_object(raw)?,schema)\n    }\n    fn parse_object(raw:&[u8])->Result<serde_json::Value,E> {\n'
VALUE_BRIDGE='        Ok(value)\n    }\n    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,E> {\n'


def inventory(check):return prior.inventory(check)|{TARGET,WRAPPER}


def inverse(q,old):
    text=q.text(PARSER)
    for addition in ('pub mod review;\n',PARSE_BRIDGE,VALUE_BRIDGE):
        c.require(text.count(addition)==1,'ONLY_STRICT_PARSER_OBJECT_VALUE_EXTRACTION_AND_NEW_MODULE');text=text.replace(addition,'')
    prior.base.prior.audit.inverse(text,old[PARSER],'ORIGINAL_V1_V2_PARSE_VALUE_POLICY_CANONICAL_SCOPE_AND_AUTH_BODIES_EXACT_INVERSE')
    text=q.text(STORED);c.require(text.count('mod product;\n')==1,'ONE_ADDITIVE_V3_OWNERSHIP_ADAPTER')
    prior.base.prior.audit.inverse(text.replace('mod product;\n',''),old[STORED],'ORIGINAL_V3_PREPARE_FRESH_WRITER_AND_FINAL_HEAD_BODIES_UNCHANGED')
    def handoff_body(value):
        at=value.index('    pub(crate) fn ');start=value.index('\n',value.index('    where ',at))+1
        return value[start:value.index('\n    }',start)]
    current=handoff_body(q.text(OWNER)).replace('prepare_review_literal_candidate','prepare_literal_text_atom_candidate')
    current=current.replace('query,scope,policy,replacement','query,scope,replacement').replace('PreparedStoredReviewLiteralCandidate','PreparedStoredLiteralTextAtomCandidate')
    previous=handoff_body(q.text('crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/product.rs'))
    c.require(current==previous,'EXACT_QUALIFIED_OUTPUT_RECEIPT_MOVE_AND_BOX_SOURCE_NO_CLONE_OR_REIMPORT')


def test_names(q,path,module):
    return {'actual_import::'+module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_LITERAL_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_LITERAL_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        old_result=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='2d5c00db901cdfba93a072f5a42132ce195075f1fc354dce2fd7ca45a5ef18ed'
            and old_result['state'].startswith('PASS_')and old_result['cleanup']and old_result['current_stored_cases']==6,'EXACT_PREVIOUS_V3_STORED_SIX_PASSES')
        old={p['path']:p for p in old_result['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_V3_PRODUCT_OWNER_TEST_AND_FOCUSED_TARGET_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_CORE_PROVIDER_FIXTURE_OR_EXISTING_TEST_CHANGE')
        inverse(q,old)
        groups=(test_names(q,TEST,'review_literal_product'),test_names(q,V1,'literal_replacement_product'),
            test_names(q,V2,'literal_text_atom_product'),test_names(q,prior.base.TEST,'review_literal_output'))
        c.require(tuple(map(len,groups))==(10,9,10,6),'EXACT_TEN_NEW_NINETEEN_PRODUCT_AND_SIX_BORROWED_AFFECTED_TESTS')
        expected=set().union(*groups)
        c.require(len(expected)==35 and {n for n,s in old_result['steps'][0]['tests']}==groups[3],'PREVIOUS_SIX_EXACT_IDENTITIES_NOW_OWNER_ADAPTER_AFFECTED')
        wrapper=q.text(WRAPPER)
        c.require(wrapper=='use super::*;\n'+''.join(f'#[path="../form_stored_provider/actual_import/{module}.rs"]\nmod {module};\n'
            for module in ('review_literal_product','review_literal_output','literal_replacement_product','literal_text_atom_product')),
            'FOCUSED_TARGET_EXACT_FOUR_ORIGINAL_TEST_MODULES_NO_LEGACY_SUITE')
        c.require(q.text(TARGET)=='//! Focused v3 product and affected v1/v2/shared-owner cases, never the full stored suite.\n'
            'use domain_ir::DocumentId;\nuse std::error::Error;\ntype TestResult=Result<(),Box<dyn Error>>;\n'
            'include!("support/stored_source_fixture.rs");\n#[path="review_literal_product/actual_import.rs"]\nmod actual_import;\n',
            'SAME_SHARED_FIXTURE_IN_ORIGINAL_LEXICAL_SCOPE')
        env=prior.base.prior.audit.environment()
        print(json.dumps(dict(state='REVIEW_LITERAL_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=10,affected_cases=25,
            retained_core_cases=32,strict_v1_v2_parser_and_v3_access_inverse=True)),flush=True)
        harness.run_one('ten_new_v3_nineteen_affected_v1_v2_six_borrowed_cases',[harness.CARGO,'test','--offline','--locked','-j','1',
            '-p','hwpx-agent-cli','--test','review_literal_product','--','--test-threads=1'],expected,guard,env,row,observe_capture=prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_LITERAL_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_V3_REVIEW_LITERAL_PRODUCT_TEN_NEW_TWENTY_FIVE_AFFECTED_NOT_FULL_SEARCH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=10,affected_cases=25,total_executed_cases=35,
            retained_core_cases=32,original_v1_v2_parser_and_canonical_provider_scope_bodies_inverse_verified=True,
            original_v3_current_access_writer_and_final_head_bodies_unchanged=True,source_ownership_transferred_without_clone_or_reimport=True,
            explicit_both_policy_booleans_and_version_bound_digests=True,invalid_request_rejected_before_artifact_reads=True,
            v1_v2_schema_and_semantic_boundaries_preserved=True,idempotency_key_claimed=False,
            core_scalar_and_unrelated_stored_tests_reexecuted=False,command_line_or_server_dispatcher_added=False,
            next_work='Full_search_scope_and_effective_style_visibility_semantics_or_reference_source_completion')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_LITERAL_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_V3_PRODUCT_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
