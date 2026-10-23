"""Whitespace-only typed atom patch foundation24 plus19 affected range regressions; no full product claim."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_width_product_components as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-whitespace-patch-components181.v1.json'
FAILED='implementation/p09/evidence/p09-361-whitespace-patch-components180.v1.json'
PATCH='crates/hwpx-package/src/patch.rs';LIB='crates/hwpx-package/src/lib.rs';OLD_ATOMS='crates/hwpx-package/src/patch/text_atom_ranges.rs'
CORE='crates/hwpx-package/src/patch/whitespace_atom_ranges.rs';TEST='crates/hwpx-package/tests/patch_whitespace_atom_ranges.rs'
BUNDLE='crates/hwpx-package/tests/whitespace_patch_focused.rs';NEW={CORE,TEST,BUNDLE};CHANGED={PATCH,LIB,OLD_ATOMS}
EXPORT='    WhitespaceText, WhitespaceOutputAtom, WhitespaceControlKind, WhitespaceAtomRangeReplacement,\n'
MODULE='mod whitespace_atom_ranges;\npub use whitespace_atom_ranges::{WhitespaceText,WhitespaceOutputAtom,WhitespaceControlKind,WhitespaceAtomRangeReplacement};\n'
VARIANT='''    /// Whitespace-only original Text scalar ranges or exact qualified tab/lineBreak atoms.
    /// The separate typed output cannot inject arbitrary XML or delete non-whitespace text.
    ReplaceWhitespaceAtomRanges {
        target: XmlElementSelector,
        ranges: Vec<WhitespaceAtomRangeReplacement>,
    },
'''
ARM='''                PatchIntent::ReplaceWhitespaceAtomRanges { target, ranges } => {
                    self.plan_whitespace_atom_ranges(target,ranges,origin,&mut whitespace_budget,&mut edits)?;
                }
'''


def inventory(check):return prior.inventory(check)|NEW


def one(text,marker):
    c.require(text.count(marker)==1,'ONE_ADDITIVE_WHITESPACE_PATCH_DISPATCH_OR_EXPORT');return text.replace(marker,'')


def inverse(q,old):
    text=q.text(PATCH)
    for marker in(MODULE,VARIANT,ARM,'            Self::ReplaceWhitespaceAtomRanges { .. } => formatter.write_str("ReplaceWhitespaceAtomRanges(<redacted>)"),\n',
        '        let mut whitespace_budget=whitespace_atom_ranges::preflight(self.intents,self.patch_limits)?;\n'):text=one(text,marker)
    audit.inverse(text,old[PATCH],'ENTIRE_OLD_PATCH_ENGINE_ID_PROFILES_TRANSACTIONS_DISPATCH_AND_VALIDATION_BODIES_UNCHANGED')
    audit.inverse(one(q.text(LIB),EXPORT),old[LIB],'ENTIRE_OLD_PUBLIC_EXPORTS_UNCHANGED')
    audit.inverse(one(q.text(OLD_ATOMS),'    pub(super) fn replacement_value(&self)->&str{self.range.data().2}\n'),old[OLD_ATOMS],
        'ENTIRE_OLD_ATOM_COORDINATE_CONTROL_REJECTION_AND_SCANNER_BODIES_UNCHANGED')
    core=q.text(CORE)
    c.require('read_source_text_span(xml,target.element_index)'in core and 'text_atom_ranges::scalar_edges('in core and 'let mut chars=text.chars();let mut consumed=0u32;'in core
        and 'node.start_name_span()'in core and 'whitespace_joint_output_bytes'in core and 'whitespace_joint_ranges'in core
        and 'Kind::Control(expected)'in core and 'Kind::Empty'in core,'QUALIFIED_SOURCE_ONE_CURSOR_PER_ATOM_DERIVED_NAMESPACE_TYPED_CONTROL_EMPTY_AND_JOINT_LIMITS')


def expected(q):
    result=set()
    for name,module,count in[(TEST,'whitespace',24),('crates/hwpx-package/tests/patch_text_atom_ranges.rs','atoms',10),('crates/hwpx-package/tests/patch_leaf_scalar_ranges.rs','leaf',9)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name));c.require(len(names)==len(set(names))==count,'EXACT24_NEW10_ATOM9_LEAF_IDENTITIES');result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_PATCH_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_PATCH_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,whitespace_source_compiler_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='37e2065b5df76f9ff8732911e647e1d563ef0b720fe827f298b5543c562ce41c'
            and baseline['state']=='PASS_WIDTH_TWENTY_FOUR_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==688 and baseline['new_product_cases']==24,'EXACT_PRIOR_WIDTH_PRODUCT_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_WHITESPACE_PATCH_FILES_ARE_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_COMPILERS_GUARDS_WRITERS_PRODUCTS_TESTS_AND_FIXTURES_UNCHANGED')
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='908a2b240edcb10ca7c27034ea3a1bcbaef5661905c079fde70af6ec5547b6dd'
            and failed['state']=='FAILED_WHITESPACE_PATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL180_COMPILE_FAILURE_PRESERVED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and not step['tests']and step['cleanup']and step['owned_job']['owned_tree_empty']
            and step['owned_job']['job_handle_closed']and step['bounded_output_observation']['rust_error_codes']==['E0308'],'EXACT180_TYPE_MISMATCH_ZERO_TESTS_AND_TERMINAL_JOB')
        failed_pins={p['path']:p for p in failed['source_pins']}
        for name in names-{CORE}:c.require(q.snapshots[name]==failed_pins[name],'ALL_OTHER_PRODUCTION_TESTS_FIXTURES_AND_GUARDS_UNCHANGED_AFTER180')
        repair='''            let control=&xml.elements()[at];let outer=control.outer_span().ok_or(PatchError::FragmentInvalid)?;
            controls.insert(u32::try_from(i).map_err(|_|PatchError::AllocationFailed)?,outer.start()..outer.end());child=control.next_sibling();}
'''
        original='''            let control=&xml.elements()[at];controls.insert(u32::try_from(i).map_err(|_|PatchError::AllocationFailed)?,control.outer_span().ok_or(PatchError::FragmentInvalid)?);child=control.next_sibling();}
'''
        text=q.text(CORE);c.require(text.count(repair)==1,'ONE_XML_BYTE_SPAN_TO_ORDINARY_RANGE_CORRECTION');audit.inverse(text.replace(repair,original),failed_pins[CORE],'EXACT180_CORE_RESTORED_BY_UNDOING_ONLY_XML_SPAN_TYPE_CONVERSION')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='WHITESPACE_PATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,affected_cases=19,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_typed_whitespace_patch_and_nineteen_range_regressions',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','whitespace_patch_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_WHITESPACE_PATCH_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE_PATCH24_RANGE19_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_patch_cases=24,affected_range_cases=19,total_executed_cases=43,old218_products_and_unrelated_source_reexecuted=False,
            original_patch_engine_and_all_old_range_bodies_inverse_verified=True,
            old_control_rejection_unchanged_and_new_typed_whitespace_only_operation=True,
            next_work='SEARCH023_original_source_whitespace_policy_selection_protection_compiler_and_readback_then_current_store_product_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_PATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WHITESPACE_PATCH_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
