"""Exact original sibling-byte permutation, existing patch/writer guards, no source sort/Native promotion."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_pinned_p02_registry_components as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-sibling-permutation-components227.v1.json'
DRIVER='tools/p09/run_sibling_permutation_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-pinned-p02-registry-sync226.v1.json'
ROOT='crates/hwpx-package/src/patch.rs'
MODEL='crates/hwpx-package/src/patch/sibling_permutation.rs'
PARENT='crates/hwpx-package/tests/patch_engine.rs'
TEST='crates/hwpx-package/tests/support/patch_sibling_permutation.rs'
NEW={MODEL,TEST,DRIVER}
CHANGED={ROOT,PARENT}
CHILD='\n#[path = "support/patch_sibling_permutation.rs"]\nmod sibling_permutation_v1;\n'


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_pinned_p02_registry_sync.py','protocol/migrations/p09-pinned-p02-registry-evidence-v1.md'}


def inverse(q,old):
    text=q.text(ROOT)
    for marker in ('mod sibling_permutation;\n',
        '            Self::PermuteSiblingElements { .. } => formatter.write_str("PermuteSiblingElements(<redacted>)"),\n',
        '        let projected_edits=sibling_permutation::preflight(self.intents,self.patch_limits)?;\n',
        '        let mut permutation_bytes=self.patch_limits.config().max_fragment_bytes;\n'):
        c.require(text.count(marker)==1,'ONE_ADDITIVE_PERMUTATION_MODULE_DEBUG_AND_PREFLIGHT');text=text.replace(marker,'')
    for pattern in (r'    /// Reorders only original element byte slices.*?    },\n',
        r'                PatchIntent::PermuteSiblingElements \{ targets, source_order \} => \{.*?\n                }\n'):
        text,count=re.subn(pattern,'',text,flags=re.S);c.require(count==1,'ONE_TYPED_VARIANT_AND_BYTE_EDIT_DISPATCH_ONLY')
    marker='.try_reserve_exact(projected_edits)';c.require(text.count(marker)==1,'ONE_BOUNDED_EDIT_RESERVATION')
    text=text.replace(marker,'.try_reserve_exact(self.intents.len())')
    audit.inverse(text,old[ROOT],'ALL_ORIGINAL_PATCH_SELECTORS_ID_REFERENCES_CONFLICT_VALIDATION_AND_OUTPUT_BRANCHES_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_APPENDED_PATCH_TEST_CHILD')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL_SIX_ORIGINAL_PATCH_CASES_AND_HELPERS_BYTE_IDENTICAL')
    text=q.text(MODEL)
    for marker in ('node.parent().ok_or(E::RootMutation)','parent!=actual','span.start()<end',
        'std::mem::replace(slot,true)','*remaining=remaining.checked_sub(bytes)',
        'max_intents','limit:"permutation_bytes"'):
        c.require(marker in text,'SAME_PARENT_ORDER_BIJECTION_AGGREGATE_WORK_AND_COPY_LIMITS')
    c.require(all(marker not in text for marker in ('std::fs::','std::process::','ValidatedXmlFragment::','unsafe','SignatureVerified','commit_success(')),
        'NO_XML_RECONSTRUCTION_EXTERNAL_IO_NATIVE_TRUST_OR_COMMIT')


def expected(q):
    new=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    old=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PARENT))
    c.require(len(new)==len(set(new))==12 and len(old)==len(set(old))==6,'EXACT12_NEW_PERMUTATION_AND6_AFFECTED_PATCH_TESTS')
    return {'sibling_permutation_v1::'+n for n in new}|set(old)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERMUTATION_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SIBLING_PERMUTATION_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,source_sort_or_locale_semantics_verified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='a4bff4e76e3beba1bc050d3a5d71c8f9e8297bc38f226fa083d6062faf3460bb'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==780,'EXACT225_PINNED_CRYPTO18_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='12125ef9aba5daf24218348b1ab90b8d49baea996ebfed6978d94811422013b4'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==29,'EXACT226_SELECTED_DOC_CLOSURE')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_PROTECTION_COMPILER_PRODUCTS_TRUST_AND_TEST_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SIBLING_PERMUTATION_PREFLIGHT',inputs=len(q.snapshots),new_cases=12,affected_cases=6,official249_reexecuted=False)),flush=True)
        harness.run_one('twelve_source_byte_permutations_and_six_affected_original_patch_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','patch_engine','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_SIBLING_BYTE_PERMUTATION12_AFFECTED_PATCH6_NOT_SOURCE_SORT_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=18,
            original_ID_reference_conflict_preservation_and_writer_guards_retained=True,
            prior_crypto18_protection44_compiler36_and_official249_reexecuted=False,
            next_work='source_bound_SEARCH021_comparator_scope_protection_order_semantics_then_product_request_and_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PERMUTATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PERMUTATION_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
