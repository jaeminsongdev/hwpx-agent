"""Recheck only19 explicit-v2 cases after replacing quadratic atom-array insertion with a merge."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_recovery as prior
base=prior.base
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-linear120.v1.json'
OLD='''        for (at,value) in additions.into_iter().rev(){after.atoms.insert(at,TextAtom::Text(value));}
        // Boundary insertion can make two adjacent original/new text atoms; the original reader
        // merges those tokens. Construct the same canonical atom sequence before readback.
        if insertions.is_some(){let mut merged:Vec<TextAtom>=Vec::new();for atom in after.atoms {match atom {
            TextAtom::Text(value)=>if let Some(TextAtom::Text(previous))=merged.last_mut(){append(previous,&value,index.limits.0.result_bytes)?;}else{merged.push(TextAtom::Text(value));},
            atom=>merged.push(atom),
        }}after.atoms=merged;}
'''
NEW='''        // Boundary insertion can make two adjacent original/new text atoms; the original reader
        // merges those tokens. Construct the same canonical atom sequence before readback.
        if insertions.is_some(){regex::insertions::materialize(&mut after,additions,index.limits.0.result_bytes)?;}
'''


def inverse(q,old):
    text=q.text(base.ATOMS);c.require(text.count(NEW)==1 and 'after.atoms.insert('not in text,'ONLY_EXPLICIT_V2_MERGE_REPLACES_REPEATED_VECTOR_INSERTIONS')
    audit.inverse(text.replace(NEW,OLD),old[base.ATOMS],'WHOLE_PROTECTED_COMPILER_EXACT_INVERSE_OUTSIDE_V2_MATERIALIZATION')
    projection=q.text(base.INSERTIONS);marker='\n/// Merge sorted original atom edges'
    c.require(projection.count(marker)==1 and 'for boundary in 0..=length'in projection and 'additions.into_iter().peekable()'in projection,
        'ONE_ADDITIVE_LINEAR_ORIGINAL_ATOM_AND_INSERTION_MERGE')
    audit.inverse(projection.split(marker,1)[0],old[base.INSERTIONS],'WHOLE_ORIGINAL_NFC_PROJECTION_AND_BOUNDARY_HASH_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_LINEAR_IMMUTABLE_RUN_EXISTS');selection=base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_LINEAR',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_zero_width_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='b6ef94d5d05be689f4f73ebd4490df9cecfc24e14a55ac5971215e9042ec144d'
            and previous['state'].startswith('PASS_')and previous['total_distinct_cases']==116 and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==591,'EXACT_PRIOR_COMPONENT_RECOVERY_AND_FULL_INPUT_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for name in names-{base.ATOMS,base.INSERTIONS}:c.require(q.snapshots[name]==old[name],'NO_QUERY_PROJECTION_PATCH_PROTECTION_WRITER_AUTH_PRODUCT_OR_TEST_INPUT_CHANGE')
        inverse(q,old);base.boundaries(q)
        cases={'regex_insertions::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))}
        c.require(len(cases)==19,'EXACT_NINETEEN_AFFECTED_V2_CASES_NO_ORIGINAL_NINETY_SEVEN_REPLAY')
        print(json.dumps(dict(state='REGEX_INSERTION_LINEAR_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),affected_v2_cases=19,retained_original_cases=97,one_cpu_mask=4)),flush=True)
        harness.run_one('nineteen_v2_cases_after_linear_control_slot_materialization',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_insertion_focused','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25
            and limits['priority_class']==16384,'ORIGINAL_SINGLE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(base.inventory(guard.check)==names,'FINAL_LINEAR_INSERTION_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_LINEAR_NINETEEN_AFFECTED_NINETY_SEVEN_RETAINED_NOT_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_current_cases=19,retained_original_cases=97,total_distinct_cases=116,previous_original_cases_reexecuted=False,
            original_compiler_inverse_outside_explicit_v2_merge=True,projection_patch_field_protection_writer_and_tests_unchanged=True,
            complexity='Original_atom_and_sorted_insertion_single_pass_not_repeated_vector_shifts',
            next_work='Explicit_v2_zero_width_current_stored_and_strict_product_binding_then_remaining_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_LINEAR_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LINEAR_INSERTION_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
