"""Reuse typed catalog anchors without rescanning XML; only19 affected style cases, retain40 originals."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_replacement_components as base
harness,shared,c,a,audit=base.harness,base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-style-replacement-target127.v1.json'
OLD='''        let header=self.inspection.text.original.source().parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or(E::Definition)?;
        let xml=header.xml().ok_or(E::Definition)?;
        let i=xml.elements().iter().position(|n|n.name().namespace()==Some(crate::HANCOM_2020_HEAD_NAMESPACE)&&n.name().local_name()=="charPr"
            &&n.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="id"&&a.semantic_value().parse::<u32>()==Ok(id))).ok_or(E::Definition)?;
        header.element_anchor(i).cloned().ok_or(E::Definition)
'''
FIELD='    character_declarations:BTreeMap<u32,SourceAnchorHandle>,\n'
BUILD='''        drop(ids);
        let character_declarations=definitions.into_iter().filter(|d|d.kind==CatalogKind::CharacterProperty).map(|d|(d.native_id,d.source_anchor)).collect();
'''
NEW_TEST='''#[test]
fn style_replacement_target_receipt_uses_exact_original_typed_catalog_declaration()->TestResult {
    use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,ImportedCatalogKind}}};
    let raw=plain("ABC")?;let f=forms(&raw)?;let fields=ImportedDocumentFields::import(&f)?;
    let semantics=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&semantics)?;
    let expected=&catalog.definitions().iter().find(|d|d.kind==ImportedCatalogKind::CharacterProperty&&d.native_id==1).ok_or("declaration")?.source_anchor;
    let out=replace(&f,&raw,"B",Scope::Document,all())?;assert_eq!(&out.receipt().target_declaration,expected);
    assert_eq!(out.receipt().character_property,1);output(&raw,&out)?;Ok(())
}
'''


def inverse(q,old):
    text=q.text(base.DEFS)
    for marker in(FIELD,BUILD,'self.character_declarations.get(&id).cloned().ok_or(E::Definition)',
        'SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt,character_declarations}'):
        c.require(text.count(marker)==1,'ONLY_MOVED_TYPED_DECLARATION_ANCHOR_INDEX_AND_LOOKUP')
    restored=text.replace(FIELD,'').replace(BUILD,'').replace('        self.character_declarations.get(&id).cloned().ok_or(E::Definition)\n',OLD)
    restored=restored.replace('SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt,character_declarations}','SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt}')
    audit.inverse(restored,old[base.DEFS],'WHOLE_ORIGINAL_TYPED_STYLE_MATCHER_UNCHANGED_OUTSIDE_MOVED_ANCHOR_INDEX')
    text=q.text(base.TEST);c.require(text.endswith(NEW_TEST)and text.count(NEW_TEST)==1,'ONE_INDEPENDENT_TYPED_CATALOG_DECLARATION_IDENTITY_ORACLE')
    audit.inverse(text[:-len(NEW_TEST)],old[base.TEST],'ALL_EIGHTEEN_PREVIOUS_STYLE_CASE_BODIES_UNCHANGED')


def snapshot(capture,expected):
    result=base.prior.snapshot(capture,expected)
    with capture.lock:stderr=bytes(capture.buffers['stderr']).decode('utf-8','replace').replace('\\','/')
    rows=[]
    for path,line,column,message in re.findall(r'(?m)^(crates/[A-Za-z0-9_./-]+\.rs):([0-9]+):([0-9]+): warning: ([^\r\n]+)',stderr):
        kind='dead_code'if'never used'in message else'unused_import'if'unused import'in message else'unused_variable'if'unused variable'in message else'other_warning'
        symbols=re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`',message)[:4]
        rows.append(dict(path=path,line=int(line),column=int(column),kind=kind,symbols=symbols))
    result['safe_warning_locations']=rows[:16];return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_TARGET_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_REPLACEMENT_TARGET',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(base.OUTPUT);c.require(q.snapshots[base.OUTPUT]['sha256']=='9e8ca0a778f97c7aa43118ae9b897616dc7cdb650414a51ee4f8d01d9737192c'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==58
            and previous['fresh_inputs']==previous['final_fresh_hashes']==603,'EXACT_PRIOR_FIFTY_EIGHT_STYLE_COMPONENT_PASSES_AND_FULL_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for name in names-{base.DEFS,base.TEST}:c.require(q.snapshots[name]==old[name],'NO_RENDERER_PROTECTION_FIELD_WRITER_MATCHER_OR_PREVIOUS_ORIGINAL_TEST_INPUT_CHANGE')
        inverse(q,old);step=previous['steps'][0];retained={n for n,s in step['tests']if s=='ok'and not n.startswith('style_replacement::')}
        c.require(len(retained)==40 and len(step['tests'])==58 and all(s=='ok'for n,s in step['tests']),'EXACT_FORTY_UNCHANGED_ORIGINAL_PASSES_RETAINED')
        cases={'style_replacement::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))};c.require(len(cases)==19,'EXACT_NINETEEN_AFFECTED_STYLE_CASES')
        print(json.dumps(dict(state='STYLE_TARGET_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),affected_style_cases=19,retained_original_cases=40)),flush=True)
        harness.run_one('nineteen_style_cases_with_exact_typed_catalog_target',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','style_replacement_focused','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(base.inventory(guard.check)==names,'FINAL_STYLE_TARGET_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_REPLACEMENT_NINETEEN_AFFECTED_FORTY_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_current_cases=19,retained_original_cases=40,total_distinct_cases=59,previous_original_cases_reexecuted=False,
            original_matcher_inverse_outside_private_typed_anchor_index=True,target_anchor_from_same_original_typed_catalog_not_extra_header_scan=True,
            next_work='Current_stored_and_strict_product_binding_of_partial_character_style_candidates_then_paragraph_named_effective_style_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_TARGET_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_TARGET_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'warnings':s.get('bounded_output_observation',{}).get('safe_warning_locations',[]),'short_errors':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
