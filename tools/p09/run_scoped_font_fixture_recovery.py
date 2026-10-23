"""313: actual style font fixture, failed8 + affected3; retain other9 successes unchanged."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_scoped_font_path_recovery as previous
base=previous.base
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-scoped-font-fixture-recovery313.v1.json';DRIVER='tools/p09/run_scoped_font_fixture_recovery.py'
STYLE_NAME='''fn style_name(raw:&[u8],style:u32)->Result<String,Box<dyn Error>>{
    let header=archive::read_part(raw,"Contents/header.xml")?;
    let catalog=hwpx_package::CharacterStyleCatalogReader::read(&header,Default::default())?;
    let native=catalog.styles.get(style as usize).filter(|s|s.id==style).ok_or("fixture character property")?.font_refs.hangul;
    with_fonts(raw,|fonts|Ok(fonts.definitions().iter().find(|d|d.language==L::Hangul&&d.declared.id==native).ok_or("actual style font")?.declared.face.clone()))
}
'''
HELPER='''    let values=scalar_styles(raw)?;let first=values.first().ok_or("fixture text")?;
    let style=match axis{Axis::RunProperty=>first.1,Axis::TextStyle=>first.2}.ok_or("fixture explicit axis")?;
    Ok(forms.lower_scoped_font_candidate(raw,query(&style_name(raw,style)?),scope,policy(),axis,Default::default(),Default::default())?)
'''
OLD_HELPER='    Ok(forms.lower_scoped_font_candidate(raw,query(&source_name(raw)?),scope,policy(),axis,Default::default(),Default::default())?)\n'
TWO='''    let forms=original::forms(&raw,"scoped-font")?;
    let request=Query{query:".+",regex:true,..query(TARGET)};
    let out=forms.lower_scoped_font_candidate(&raw,request,Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default())?;
    let output=bytes(&out)?;let values=scalar_styles(&output)?;assert_ne!(values[0].1,values[1].1);assert_eq!(out.receipt().cloned_character_properties,2);
'''
OLD_TWO='''    let forms=original::forms(&raw,"scoped-font")?;let out=lower(&forms,&raw,Scope::Document,Axis::RunProperty)?;
    let output=bytes(&out)?;let values=scalar_styles(&output)?;assert_ne!(values[0].1,values[1].1);assert_eq!(out.receipt().cloned_character_properties,2);
'''
EXTRA='    assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default()),Err(E::Compile(Compile::NoMatches))));Ok(())\n'

def inverse(q,old):
    text=q.text(base.TEST)
    for current,before in [(STYLE_NAME,''),(HELPER,OLD_HELPER),(TWO,OLD_TWO),(EXTRA,'    Ok(())\n')]:
        c.require(text.count(current)==1,'EXACT_DECLARED_STYLE_FONT_FIXTURE_DELTA');text=text.replace(current,before)
    text=text.replace('Err(E::Compile(Compile::NoMatches))));\n    Ok(())','Err(E::Compile(Compile::NoMatches))));Ok(())')
    current='forms.lower_scoped_font_candidate(&raw,query(&style_name(&raw,0)?),Scope::Document,policy(),Axis::RunProperty,'
    c.require(text.count(current)==2,'ONLY_TWO_FAILED_BUDGET_TEST_INPUTS_CORRECTED');text=text.replace(current,current.replace('style_name(&raw,0)','source_name(&raw)'))
    current='assert!(matches!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),writer),Err(E::Compile(Compile::Writer))));'
    c.require(text.count(current)==1,'ONE_STRONGER_WRITER_FAILURE_ASSERTION')
    text=text.replace(current,'assert!(forms.lower_scoped_font_candidate(&raw,query(&source_name(&raw)?),Scope::Document,policy(),Axis::RunProperty,Default::default(),writer).is_err());')
    audit.inverse(text,old,'ALL_OTHER_TEST_BODIES_PRESERVED_AND_ONLY_FAILED_FIXTURE_EXPECTATIONS_STRENGTHENED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCOPED_FIXTURE_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SCOPED_FIXTURE_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='db4c26c1ea711de5337ce422ffbbbc07e34bc7179ffdef51f3fe81b14a56772d'and failed['cleanup'],'EXACT312_PARTIAL_RESULT_PRESERVED')
        passed={n for n,s in failed['steps'][0]['tests']if s=='ok'};missing={n for n,s in failed['steps'][0]['tests']if s!='ok'}
        affected={'scoped::explicit_text_style_splits_text_without_changing_run_or_unselected_text_axis','scoped::stale_whole_source_and_stale_selector_are_rejected','scoped::empty_selection_and_unmatched_selected_properties_do_not_publish_a_clone'}
        c.require(len(passed)==12 and len(missing)==8 and affected<=passed,'ORIGINAL12_PASS8_FAIL_AND_ONLY3_AFFECTED_PASS_CASES')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=base.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCT_NAME_SCOPE_CLONE_RENDER_PROTECTION_AND_READBACK_CODE_UNCHANGED')
        q.pin(DRIVER);inverse(q,old[base.TEST])
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        all_cases={'scoped::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}
        c.require(all_cases==passed|missing,'SAME20_IDENTITIES_NO_TEST_REMOVED');cases=missing|affected
        scratch=c.ROOT/'target/p09-scoped-font-scratch-313';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'SCOPED_FIXTURE_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='SCOPED_FIXTURE_PREFLIGHT',inputs=len(q.snapshots),failed_cases=8,affected_cases=3,retained_passes=9)),flush=True)
        harness.run_one('scoped_font_failed8_and_affected3',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_scoped_fonts',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'SCOPED_FIXTURE_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPED_FONT_RETAINED9_RECOVERED8_AFFECTED3_NOT_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_cases=11,retained_passes=9,distinct_current_cases=20,product_code_changed_from312=False,old24_and_official249_replayed=False,
            next_work='current_stored_access_and_strict_product_binding_of_scoped_font_candidates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'SCOPED_FIXTURE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'SCOPED_FIXTURE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
