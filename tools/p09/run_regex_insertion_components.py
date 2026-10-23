"""Explicit source regex v2 insertions; affected core/patch suites plus original v1 products only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_product_components as prior
from run_literal_text_atom_product_components import CAPTURE
from run_stored_review_literal_focused import snapshot
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-components118.v1.json'
ATOMS='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
REGEX=ATOMS[:-3]+'/regex.rs';INSERTIONS=REGEX[:-3]+'/insertions.rs';READBACK=ATOMS[:-3]+'/readback.rs'
PATCH='crates/hwpx-package/src/patch/text_atom_ranges.rs'
TARGET='crates/hwpx-package/tests/regex_insertion_focused.rs';TEST='crates/hwpx-package/tests/document_import_regex_insertions.rs'
NEW={INSERTIONS,TARGET,TEST};CHANGED={ATOMS,REGEX,READBACK,PATCH}
GROUPS=(('regex_insertions','document_import_regex_insertions',18),('regex_v1','document_import_regex_replacement',17),
    ('atom_literal','document_import_search_atom_replacement',12),('review_literal','document_import_search_review_replacement',12),
    ('selector_literal','document_import_review_selector_replacement',8),('atom_ranges','patch_text_atom_ranges',10),('leaf_ranges','patch_leaf_scalar_ranges',9))


def inventory(check):return prior.inventory(check)|NEW


def expected(q):
    result=set()
    for module,file,count in GROUPS:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+file+'.rs'))
        c.require(len(names)==len(set(names))==count,'EXACT_NEW_INSERTION_AND_AFFECTED_ORIGINAL_TEST_IDENTITIES')
        result.update(module+'::'+n for n in names)
    c.require(len(result)==86,'EIGHTEEN_NEW_SIXTY_EIGHT_AFFECTED_CORE_PATCH_CASES');return result


def boundaries(q):
    regex=q.text(REGEX);atoms=q.text(ATOMS);patch=q.text(PATCH);projection=q.text(INSERTIONS)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','index.find_with_captures(query,selector,policy,Some(&mut collector))'):
        c.require(regex.count(marker)==1,'ONE_WHOLE_FIELD_REVIEW_INDEX_CAPTURE_PASS_FOR_BOTH_EXPLICIT_PROFILES')
    c.require('writer,None).map(|(candidate,_)|candidate)'in regex and 'zero_width_control_or_field_cache_edit_qualified:false'in regex,
        'ORIGINAL_V1_PASSES_NO_INSERTION_POLICY_AND_COMBINED_AUTHORITY_FLAG_STAYS_FALSE')
    c.require('let origins=selected_origins(index,m)?;'in atoms and 'guards.get(part.path())'in atoms and 'point<fields[i-1].1'in atoms
        and 'readback::build(source,fresh,&intents,&plans,writer,review)?'in atoms,'ORIGINAL_CONTIGUITY_FIELDS_PROTECTION_AND_ONE_PRESERVING_WRITER_RETAINED')
    c.require('for i in (0..block.units.len()).rev()'in projection and 'for (cut,right) in suffix.into_iter().enumerate()'in projection
        and 'a>=b||a.checked_add(1)!=Some(b)'in projection,'ONE_LINEAR_PREFIX_SUFFIX_MAP_REJECTS_AMBIGUOUS_NFC_CUTS')
    c.require('if ranges.iter().any(|r|r.boundary)'in patch and 'control_edges.get(control)'in patch,
        'CONTROL_BOUNDARIES_INDEXED_ONCE_NOT_ONE_XML_WALK_PER_INSERTION')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_IMMUTABLE_RUN_EXISTS');selection=prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_zero_width_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='3a778f5ec5f29813a07755065b51f4f61935a163caf7ea3a35a3a7b80659608a'
            and baseline['state'].startswith('PASS_')and baseline['total_executed_cases']==29 and baseline['cleanup'],'EXACT_PRIOR_REGEX_PRODUCT_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_SOURCE_INSERTION_MODULE_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_PRODUCT_AUTHORIZATION_WRITER_GUARD_SOURCE_AND_ORIGINAL_TEST_INPUTS_UNCHANGED')
        boundaries(q);core=expected(q);products=prior.expected(q)
        print(json.dumps(dict(state='REGEX_INSERTION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,affected_core_patch_cases=68,affected_v1_product_cases=29,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_insertions_and_sixty_eight_original_core_patch',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_insertion_focused','--','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=snapshot)
        harness.run_one('twenty_nine_original_v1_regex_and_selector_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--','--test-threads=1'],products,guard,audit.environment(),row,observe_capture=snapshot)
        for step in row['steps']:
            limits=step['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
                'ONE_CPU2_ORIGINAL_HARD_CPU_CAP_AND_BELOW_NORMAL_PRIORITY_VERIFIED')
        c.require(inventory(guard.check)==names,'FINAL_REGEX_INSERTION_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_EIGHTEEN_NEW_NINETY_SEVEN_AFFECTED_NOT_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_core_cases=18,affected_core_patch_cases=68,affected_original_product_cases=29,total_executed_cases=115,
            original_v1_zero_width_rejection_and_product_schema_preserved=True,one_capture_pass_one_protected_transaction=True,
            exact_inverse_nfc_cut_and_original_control_bytes_verified=True,other_process_or_common_guard_settings_changed=False,
            next_work='Explicit_v2_zero_width_current_stored_and_strict_product_binding_then_remaining_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_INSERTION_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
