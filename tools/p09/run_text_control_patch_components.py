"""18 exact typed text-control patch cases; unchanged old compiler/product bodies retained."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-text-control-patch-components189.v1.json'
PATCH='crates/hwpx-package/src/patch.rs';LIB='crates/hwpx-package/src/lib.rs';WS='crates/hwpx-package/src/patch/whitespace_atom_ranges.rs'
CORE='crates/hwpx-package/src/patch/text_control_atoms.rs';TEST='crates/hwpx-package/tests/patch_text_control_atoms.rs'
NEW={CORE,TEST};CHANGED={PATCH,LIB,WS}
MODULE='mod text_control_atoms;\npub use text_control_atoms::TextControlAtomReplacement;\npub use whitespace_atom_ranges::WhitespaceControlKind as TextControlKind;\n'
VARIANT='''    /// Exact original tab/lineBreak atoms to validated Text/Tab/LineBreak output, never raw XML.
    ReplaceTextControlAtoms {
        target: XmlElementSelector,
        replacements: Vec<TextControlAtomReplacement>,
    },
'''
ARM='''                PatchIntent::ReplaceTextControlAtoms { target, replacements } => {
                    self.plan_text_control_atoms(target,replacements,origin,&mut whitespace_budget,&mut edits)?;
                }
'''


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    text=q.text(PATCH)
    for marker in(MODULE,VARIANT,ARM,'            Self::ReplaceTextControlAtoms { .. } => formatter.write_str("ReplaceTextControlAtoms(<redacted>)"),\n',
        '        whitespace_budget=whitespace_budget.max(text_control_atoms::preflight(self.intents,self.patch_limits)?);\n'):
        c.require(text.count(marker)==1,'ONE_ADDITIVE_TEXT_CONTROL_DISPATCH_OR_BUDGET');text=text.replace(marker,'')
    audit.inverse(text,old[PATCH],'ENTIRE_OLD_PATCH_ENGINE_TRANSACTIONS_ID_PROFILES_AND_DISPATCH_BODIES_UNCHANGED')
    text=q.text(LIB);marker='    TextControlAtomReplacement, TextControlKind,\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_TEXT_CONTROL_EXPORT')
    audit.inverse(text.replace(marker,''),old[LIB],'ENTIRE_OLD_PACKAGE_PUBLIC_EXPORTS_UNCHANGED')
    text=q.text(WS);marker='    pub(super) fn output_atom_count(&self)->usize{self.output.len()}\n';c.require(text.count(marker)==1,'ONE_READONLY_WHITESPACE_OUTPUT_COUNT_GETTER')
    audit.inverse(text.replace(marker,''),old[WS],'ENTIRE_OLD_WHITESPACE_POLICY_VALIDATION_RENDERER_SCANNER_AND_BUDGET_BODIES_UNCHANGED')
    core=q.text(CORE)
    for marker in('if !intents.iter().any(|i|matches!(i,PatchIntent::ReplaceTextControlAtoms{..})){return Ok(0);}',
        'read_source_text_span(xml,target.element_index)','for(i,a)in span.atoms.iter().enumerate()',
        'r.output_atom_count()','text_control_joint_ranges','text_control_joint_output_atoms','text_control_joint_output_bytes',
        'ch.encode_utf8(&mut buf)','node.start_name_span()','r.expected!=kind'):
        c.require(marker in core,'ORIGINAL_QUALIFIED_READER_ONE_CONTROL_CURSOR_NAMESPACE_TYPED_KIND_STREAMED_ESCAPE_AND_JOINT_LIMITS')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==18,'EXACT18_NEW_TEXT_CONTROL_PATCH_IDENTITIES');return set(names)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_CONTROL_PATCH_IMMUTABLE_RUN_EXISTS');selection=prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_CONTROL_PATCH_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,text_control_source_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='a5a5da0058370b59835fc4e5d5e00539d11a3119e25bcf64c703a5917ef3ed75'
            and baseline['state']=='PASS_WHITESPACE_TWENTY_FOUR_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==703 and baseline['new_product_cases']==24,'EXACT187_PRIOR_PRODUCT_AND_SOURCE_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_TEXT_CONTROL_PATCH_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OLD_COMPILERS_GUARDS_READBACK_PRODUCTS_TESTS_FIXTURES_AND_OLD_ATOM_SCANNERS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='TEXT_CONTROL_PATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_patch_cases=18,old_cases_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_typed_original_text_control_patch_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','patch_text_control_atoms','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        prior.prior.base.prior.base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_TEXT_CONTROL_PATCH_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_CONTROL_PATCH18_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_patch_cases=18,old_patch_and_source_products242_or_official249_reexecuted=False,all_old_patch_and_whitespace_bodies_inverse_verified=True,
            old_intents_early_zero_budget_and_original_control_rejection_preserved=True,all_four_range_families_share_joint_budgets_and_target_exclusion=True,
            next_work='SEARCH009_exact_original_control_search_selection_protection_compiler_and_readback_then_other_control_families_and_full_product_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_CONTROL_PATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_CONTROL_PATCH_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
