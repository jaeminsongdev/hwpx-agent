"""Six current stored-service v2 atom cases; preserve the completed 22 core cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_text_atom_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-literal-text-atom-components076.v1.json'
PRIOR=base.OUTPUT
TEST='crates/product-cli/tests/form_stored_provider/actual_import/literal_text_atom_output.rs'
PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
MODULE='crates/product-cli/tests/form_stored_provider/actual_import.rs'
SOURCE='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms.rs'
NEW={TEST,SOURCE};CHANGED={PARENT,MODULE}


def inventory(check):return base.inventory(check)


def body(text,name):
    match=re.search(r'(?m)^    (?:pub )?fn '+name+r'[<(]',text);c.require(match is not None,'ACTUAL_LITERAL_BOUNDARY_METHOD_EXISTS')
    start=text.index('\n',text.index('    where ',match.start()))+1;end=text.index('\n    }',start)
    return text[start:end]


def inverse(q,old):
    for name,addition in ((PARENT,'pub mod atoms;\n'),(MODULE,'#[path = "actual_import/literal_text_atom_output.rs"]\nmod literal_text_atom_output;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONLY_ADDITIVE_STORED_ATOM_MODULE')
        base.prior.base.prior.prior.base.inverse(text.replace(addition,''),old[name],'ORIGINAL_STORED_LITERAL_AND_TEST_MODULE_BODIES_EXACT_INVERSE')
    original=q.text(PARENT);new=q.text(SOURCE)
    prepared=body(new,'prepare_literal_text_atom_candidate')
    for current,previous in (('lower_literal_text_atom_candidate','lower_literal_search_candidate'),('StoredLiteralTextAtomReceipt','StoredLiteralSearchOutputReceipt'),
        ('hwpx-agent.stored-literal-search-candidate/v2','hwpx-agent.stored-literal-search-candidate/v1'),
        ('PreparedStoredLiteralTextAtomCandidate {source:self,','PreparedStoredLiteralSearchCandidate {source:product::LiteralSource::Borrowed(self),')):
        c.require(prepared.count(current)==1,'ONE_TYPED_V2_OUTPUT_PREPARATION_SUBSTITUTION');prepared=prepared.replace(current,previous)
    c.require(prepared==body(original,'prepare_literal_search_candidate'),'SAME_CURRENT_WRITE_SOURCE_PROOF_DIGEST_AND_FINAL_PREPARATION_HEAD_BODY')
    fresh=body(new,'fresh');extra='\n            ||self.receipt.output.control_atom_replacement_qualified||!self.receipt.output.original_control_bytes_preserved'
    c.require(fresh.count(extra)==1 and fresh.replace(extra,'')==body(original,'fresh'),'SAME_FRESH_SOURCE_ACL_AEAD_BINDING_BODY_PLUS_CLOSED_V2_FLAGS')
    for name in ('verify','with_verified_bytes','require_current_product_route'):
        c.require(body(new,name)==body(original,name),'SAME_ORIGINAL_WRITER_INTEGRITY_AND_FINAL_CONSUMER_HEAD_OR_DENIED_ROUTE_BODY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_LITERAL_ATOM_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_LITERAL_TEXT_ATOM_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
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
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='feb3a50059ad8c85d2c29a1964e378d1e02d48d9749e9362ff5695e2bd24d29b'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==22,'EXACT_TWENTY_TWO_CORE_LITERAL_ATOM_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.prior.base.prior.prior.scalar.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_STORED_ATOM_SOURCE_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_SCALAR_READER_EXISTING_PRODUCT_OR_TEST_BODY_CHANGE')
        inverse(q,old)
        tests={'actual_import::literal_text_atom_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
        c.require(len(tests)==6,'EXACT_SIX_NEW_STORED_LITERAL_ATOM_CASES')
        env=base.prior.base.prior.prior.base.environment()
        print(json.dumps(dict(state='STORED_LITERAL_ATOM_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=6,core_passes_retained=22,original_current_source_and_final_head_bodies_shared=True)),flush=True)
        harness.run_one('six_current_stored_literal_atom_candidate_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(tests),'--exact','--test-threads=1'],tests,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_STORED_LITERAL_ATOM_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_LITERAL_TEXT_ATOM_SIX_NEW_TWENTY_TWO_CORE_RETAINED_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_stored_cases=6,total_executed_cases=6,retained_core_cases=22,
            original_access_source_writer_and_final_head_method_bodies_verified=True,existing_v1_literal_api_and_product_json_unchanged=True,
            current_acl_quarantine_aead_and_three_final_head_boundaries_exercised=True,
            query_or_lowering_repeated_during_retained_output_delivery=False,idempotency_key_claimed=False,
            product_json_or_command_line_or_server_route_added=False,
            next_work='Explicit_strict_v2_literal_product_JSON_and_owned_source_handoff')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_LITERAL_ATOM_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORED_LITERAL_ATOM_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
