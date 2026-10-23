"""Retain63 passes; repair the XML-wide letter-count oracle and run its one case only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_case_conversion_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-case-conversion-recovery170.v1.json'
CASE='case::case_review_policy_excludes_before_caps_and_retains_cache_and_metadata'
OLD='''        let out=c.with_verified_bytes(section)??;assert_eq!(out.matches('k').count(),n);assert!(out.contains("CACHE FROZEN"));assert!(out.contains("PRIVATE-AUTHOR"));
'''
NEW='''        let mut expected=review::body().replace("BODY K K","BODY k k");
        if h{expected=expected.replace("HIDDEN K K","HIDDEN k k");}if m{expected=expected.replace("MEMO K K","MEMO k k");}
        exact(&raw,&c,&review::body(),&expected)?;
        let out=c.with_verified_bytes(section)??;assert!(out.contains("CACHE FROZEN"));assert!(out.contains("PRIVATE-AUTHOR"));
'''


def repair(q,pins):
    audit.inverse(base.one(q.text(base.TEST),NEW,OLD),pins[base.TEST],
        'ENTIRE_CASE_SUITE_RESTORED_EXCEPT_ONE_XML_LETTER_COUNT_REPLACED_WITH_EXACT_POLICY_DEPENDENT_SECTION_AND_PART_COMPARISON')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CASE_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;stdlib=None;started=time.monotonic();row=dict(state='FAILED_CASE_CONVERSION_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,case_stored_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='c1d2709f369357e27a20ae65d99fcbc540852aa6c8a6675b5a00d0a065a0493c'
            and failed['state']=='FAILED_CASE_CONVERSION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'EXACT_ORIGINAL169_FAILURE_PRESERVED')
        step=failed['steps'][0];retained={n for n,s in step['tests']if s=='ok'}
        c.require(step['exit_code']==101 and len(retained)==63 and {n for n,s in step['tests']if s!='ok'}=={CASE}
            and step['panic_locations']==['crates/hwpx-package/tests/document_import_case_conversion.rs:105:50']
            and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'EXACT63_PASSES_ONE_XML_WIDE_COUNT_ASSERTION_FAILURE_AND_TERMINAL_JOB')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_GUARDS_LIMITS_OTHER_TESTS_AND_FIXTURES_UNCHANGED_AFTER169')
        repair(q,pins);base.inverse(q,{p['path']:p for p in baseline['source_pins']});c.require(base.expected(q)==retained|{CASE},'EXACT64_IDENTITIES_WITH63_RETAINED')
        stdlib=a.AcceptanceReader(base.STD_ROOT,guard.check);stdpins={p['path']:p for p in failed['stdlib_reference_pins']}
        for name in sorted(base.STD_FILES):stdlib.pin(name);c.require(stdlib.snapshots[name]==stdpins[name],'SAME_THREE_LOCAL_STD_UNICODE17_REFERENCE_FILES')
        print(json.dumps(dict(state='CASE_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),current_cases=1,retained_cases=63,one_cpu_mask=4)),flush=True)
        harness.run_one('one_corrected_review_policy_exact_xml_oracle',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','case_conversion_focused','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],{CASE});c.require(base.inventory(guard.check)==names,'FINAL_CASE_RECOVERY_INVENTORY_DRIFT');q.finish();stdlib.finish();guard.check(force=True)
        row.update(state='PASS_CASE1_REPAIRED63_RETAINED_NOT_CASE_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            stdlib_reference_inputs=len(stdlib.snapshots),stdlib_final_fresh_hashes=stdlib.final_fresh_hashes,
            current_source_cases=1,retained_source_cases=63,new_source_cases=22,affected_source_cases=42,total_distinct_cases=64,
            production_unchanged_after169=True,passed63_cases_reexecuted=False,old172_products_and_unrelated57_source_reexecuted=False,
            original_unicode_and_guard_patch_bodies_inverse_verified=True,whole_string_default_mapping_not_older_casefold_or_regex_properties=True,
            adjacent_changes_coalesced_only_within_original_text_atom=True,
            next_work='Current_stored_and_strict_product_binding_of_explicit_default_case_conversion_then_remaining_P09_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CASE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),stdlib_reference_root=str(base.STD_ROOT),stdlib_reference_pins=[]if stdlib is None else list(stdlib.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CASE_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','stdlib_reference_inputs','stdlib_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
