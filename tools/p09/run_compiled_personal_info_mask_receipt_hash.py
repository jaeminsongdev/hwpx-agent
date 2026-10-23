"""371: independent public receipt SHA assertion uses both hash imports; only affected1, retained31 not replayed."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-personal-info-mask-receipt-hash371.v1.json';DRIVER='tools/p09/run_compiled_personal_info_mask_receipt_hash.py'
BASE='implementation/p09/evidence/p09-361-compiled-personal-info-mask-metadata-recovery370.v1.json'
TEST='crates/product-cli/tests/support/personal_info_mask_compiled.rs';CASE='compiled::compiled_mask_targets_actual_text_anchors_and_locks_twelve_arguments'
ASSERT='    assert_eq!(c.receipt().mutation_receipt_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(original.receipt())?)));\n'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'MASK_RECEIPT_HASH_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_MASK_RECEIPT_HASH',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        source_document_mutation=False,output_ingest_commit_or_publication=False,whole_package_personal_data_removed=False,native_mask_semantics_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-compiled-mask-receipt-hash-scratch-371'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'RECEIPT_HASH_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e70b1f39ea06773091b58d624f9273af2d65a8b19c1d3a46131ae8a94d250330'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==866
            and len(before['steps'])==4 and sum(len(s['tests'])for s in before['steps'])==32 and all(s['exit_code']==0 and all(v=='ok'for _,v in s['tests'])for s in before['steps']),'EXACT370_NEW19_AFFECTED13_PASS_WITH_TWO_UNUSED_HASH_IMPORT_WARNINGS')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(set(old)|r.closure.inventory(guard.check)|{DRIVER}):
            q.pin(path)
            if path in old and path!=TEST:c.require(q.snapshots[path]==old[path],'ALL_PRODUCTION_SOURCE_MODE_TYPES_GUARDS_AND_OTHER_TESTS_UNCHANGED')
            elif path not in old:c.require(path==DRIVER,'ONLY_INDEPENDENT_HASH_VERIFIER_ADDED')
        text=q.text(TEST);c.require(text.count(ASSERT)==1,'ONE_INDEPENDENT_RECEIPT_SHA_ASSERTION');audit.inverse(text.replace(ASSERT,''),old[TEST],'ALL_PREVIOUS_TEST_BODIES_UNCHANGED_EXCEPT_ONE_ADDITIONAL_INDEPENDENT_ASSERTION')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='MASK_RECEIPT_HASH_PREFLIGHT',inputs=len(q.snapshots),affected_cases=1,retained_cases=31)),flush=True)
        harness.run_one('mask_independent_receipt_sha_affected1',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],{CASE});c.require(row['steps'][-1]['diagnostics']==[],'INDEPENDENT_RECEIPT_SHA_CASE_AND_ALL_IMPORTS_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'MASK_RECEIPT_HASH_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_MASK_INDEPENDENT_RECEIPT_SHA1_RETAINED31_COMMON23_NOT_EXECUTION_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            affected_cases=1,retained_cases=31,distinct_cases=32,new_common_cases=19,affected_original_cases=13,mutation_families=23)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'MASK_RECEIPT_HASH_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'MASK_RECEIPT_HASH_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'case_count':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
