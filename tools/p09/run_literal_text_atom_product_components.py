"""Strict v2 product: ten new cases plus fifteen affected v1-parser/v2-borrowed cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_literal_text_atom_recovery as prior
import run_search_review_text_components as audit
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-literal-text-atom-product-components079.v1.json'
PRIOR=prior.OUTPUT
TEST='crates/product-cli/tests/form_stored_provider/actual_import/literal_text_atom_product.rs'
PARSER='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=prior.base.SOURCE
MODULE=prior.base.MODULE
NEW={TEST,'crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs',STORED[:-3]+'/product.rs'}
CHANGED={PARSER,STORED,MODULE}
V1_TEST='crates/product-cli/tests/form_stored_provider/actual_import/literal_replacement_product.rs'
CAPTURE='implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx'
PARSE_BRIDGE=('        Self::parse_profile(raw,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)\n    }\n'
    '    fn parse_profile(raw:&[u8],schema:&str)->Result<Self,E> {\n')
SCOPED_WRAPPER='    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {self.scoped_sha_profile(scope,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)}\n'


def inventory(check):return prior.base.inventory(check)


def inverse(q,old):
    text=q.text(PARSER)
    for current,original in (('pub mod atoms;\n',''),(PARSE_BRIDGE,''),('request.schema_version!=schema','request.schema_version!=LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA'),
        (SCOPED_WRAPPER,''),('fn scoped_sha_profile(&self,scope:[u8;32],schema:&str)','fn scoped_sha(&self,scope:[u8;32])'),
        ('&(schema,scope,self.canonical_sha()?)','&(LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?)')):
        c.require(text.count(current)==1,'ONLY_PRIVATE_VERSION_PARAMETER_EXTRACTION_AND_ADDITIVE_V2_MODULE');text=text.replace(current,original)
    audit.inverse(text,old[PARSER],'ORIGINAL_V1_STRICT_PARSER_CANONICAL_SCOPE_AND_PRODUCT_ACCESS_BODIES_EXACT_INVERSE')
    text=q.text(STORED)
    for current,original in (('mod product;\n',''),("source:super::product::LiteralSource<'a>,","source:&'a StoredImportedDocumentForms,"),
        ('source:super::product::LiteralSource::Borrowed(self),','source:self,')):
        c.require(text.count(current)==1,'ONLY_EXISTING_BORROWED_OWNED_SOURCE_WRAPPER_REUSE');text=text.replace(current,original)
    audit.inverse(text,old[STORED],'ORIGINAL_V2_PREPARE_FRESH_SOURCE_AUTH_WRITER_AND_FINAL_HEAD_BODIES_EXACT_INVERSE')
    text=q.text(MODULE);addition='#[path = "actual_import/literal_text_atom_product.rs"]\nmod literal_text_atom_product;\n'
    c.require(text.count(addition)==1,'ONE_V2_PRODUCT_TEST_MODULE');audit.inverse(text.replace(addition,''),old[MODULE],'ORIGINAL_PRODUCT_TEST_MODULES_UNCHANGED')
    # Real ownership handoff uses the already qualified v1 enum and same body, not an output trait.
    old_owner=q.text('crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs')
    new_owner=q.text(STORED[:-3]+'/product.rs')
    def handoff_body(value):
        at=value.index('    pub(crate) fn ');start=value.index('\n',value.index('    where ',at))+1
        return value[start:value.index('\n    }',start)]
    transformed=handoff_body(new_owner).replace('prepare_literal_text_atom_candidate','prepare_literal_search_candidate').replace('PreparedStoredLiteralTextAtomCandidate','PreparedStoredLiteralSearchCandidate')
    c.require(transformed==handoff_body(old_owner),'EXACT_EXISTING_MOVE_OUTPUT_RECEIPT_AND_BOX_SOURCE_HANDOFF_BODY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_ATOM_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_TEXT_ATOM_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
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
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='d824977e51989932c03e16d591f11bd90a40928a713c4cf69fab62b3f58f75c5'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==6,'EXACT_PREVIOUS_SIX_STORED_ATOM_PASSES')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_V2_JSON_OWNER_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_CORE_SCALAR_READER_V1_PROVIDER_OR_TEST_SOURCE_CHANGE')
        inverse(q,old)
        def tests(path,prefix):return {prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}
        new=tests(TEST,'actual_import::literal_text_atom_product::');v1=tests(V1_TEST,'actual_import::literal_replacement_product::')
        borrowed=tests(prior.base.TEST,'actual_import::literal_text_atom_output::');affected=v1|borrowed
        c.require((len(new),len(v1),len(borrowed),len(affected))==(10,9,6,15),'EXACT_TEN_NEW_AND_FIFTEEN_AFFECTED_CURRENT_CASE_IDENTITIES')
        c.require({n for n,s in previous['steps'][0]['tests']}==borrowed and all(s=='ok'for n,s in previous['steps'][0]['tests']),'EXACT_PREVIOUS_SIX_BORROWED_PASS_IDENTITIES')
        env=audit.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--']
        print(json.dumps(dict(state='LITERAL_ATOM_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=10,affected_cases=15,original_parser_and_access_body_inverse_verified=True)),flush=True)
        harness.run_one('ten_strict_owned_v2_literal_product_cases',common+[*sorted(new),'--exact','--test-threads=1'],new,guard,env,row)
        harness.run_one('fifteen_affected_v1_product_and_v2_borrowed_cases',common+[*sorted(affected),'--exact','--test-threads=1'],affected,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_LITERAL_ATOM_PRODUCT_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STRICT_V2_LITERAL_PRODUCT_TEN_NEW_FIFTEEN_AFFECTED_CORE_RETAINED_NOT_FULL_SEARCH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=10,affected_cases=15,total_executed_cases=25,
            original_v1_strict_parser_and_canonical_provider_scope_bodies_inverse_verified=True,original_v2_current_access_writer_and_final_head_bodies_inverse_verified=True,
            source_ownership_transferred_without_clone_or_reimport=True,core_scalar_and_unrelated_stored_tests_reexecuted=False,
            v1_v2_schema_and_semantic_boundaries_separate=True,invalid_request_rejected_before_artifact_reads=True,
            raw_canonical_and_provider_scope_request_digests_bound=True,idempotency_key_claimed=False,
            command_line_or_server_dispatcher_added=False,next_work='Extended_review_body_literal_replacement_with_explicit_hidden_and_MEMO_policy')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_ATOM_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_ATOM_PRODUCT_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
