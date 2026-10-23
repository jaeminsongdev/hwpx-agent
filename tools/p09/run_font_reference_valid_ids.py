"""303: valid contiguous declaration IDs in the derivative fixture; original reader preserved."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_reference_fixture_recovery as previous
prior=previous.prior
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-reference-valid-ids303.v1.json'
DRIVER='tools/p09/run_font_reference_valid_ids.py';SCRATCH='target/p09-font-reference-scratch-303'

def inverse(text,old):
    changes=[
        ('if !fonts.iter().enumerate().all(|(i,n)|native(n).is_ok_and(|id|id==i as u32)) {return Err("fixture original contiguous ids".into());}',
         'if fonts.iter().any(|n| native(n).is_ok_and(|id| id>=900_000)) {return Err("fixture reserved id".into());}'),
        ('for (suffix,id) in [fonts.len(),fonts.len()+1].into_iter().enumerate() {','for id in [900_000,900_001] {'),
        ('Some(format!("P09-FONT-{}",if suffix==0{"A"}else{"B"}))','Some(format!("P09-FONT-{id}"))'),
        ('    let target=fonts.definitions().iter().find(|d|d.language==language&&d.declared.face=="P09-FONT-A").ok_or("declared replacement font")?;\n    Ok(M{language,from_native_id:old.declared.id,to_native_id:target.declared.id})',
         '    Ok(M{language,from_native_id:old.declared.id,to_native_id:900_000})'),
        ('fn spare(fonts:&ImportedDocumentFonts<\'_, \'_, \'_, \'_>,language:L)->Result<u32,Box<dyn Error>> {\n    Ok(fonts.definitions().iter().find(|d|d.language==language&&d.declared.face=="P09-FONT-B").ok_or("declared spare font")?.declared.id)\n}\n',''),
        ('if let Some(m)=mappings.iter().find(|m|m.language==link.language){assert_eq!(d.declared.id,m.to_native_id);}',
         'if mappings.iter().any(|m|m.language==link.language){assert_eq!(d.declared.id,900_000);}'),
        ('    let last=with_fonts(original,|f|spare(f,m.language))?;\n    let c=candidate(original,&[m,M{language:m.language,from_native_id:m.to_native_id,to_native_id:last}],Limits::default())?;',
         '    let c=candidate(original,&[m,M{language:m.language,from_native_id:900_000,to_native_id:900_001}],Limits::default())?;'),
        ('assert_ne!(d.declared.id,last);','assert_ne!(d.declared.id,900_001);'),
        ('for target in [m.to_native_id,spare(f,m.language)?]','for target in [m.to_native_id,900_001]'),
        ('let unused=M{from_native_id:spare(f,m.language)?,..m};','let unused=M{from_native_id:900_001,..m};'),
    ]
    for new,before in changes:
        c.require(text.count(new)==1,'EXACT_DECLARED_ID_FIXTURE_CHANGE');text=text.replace(new,before)
    audit.inverse(text,old,'ONLY_VALID_FIXTURE_IDS_AND_TARGET_LOOKUPS_NO_ASSERTION_REMOVAL')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_VALID_IDS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_VALID_IDS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_or_scoped_product_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='a266a0b6c5d415aa8a98a6c974521971cb7142a5ac319879e1f6fecfa59a169a'and failed['cleanup']
            and len(failed['steps'][0]['tests'])==14 and all(s=='FAILED'for _,s in failed['steps'][0]['tests']),'EXACT302_ZERO_PASSES_ORIGINAL_CHARACTER_READER_REJECTION')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=prior.TEST:c.require(q.snapshots[n]==old[n],'ALL302_PRODUCTION_AND_READER_AND_PROTECTION_INPUTS_UNCHANGED')
        inverse(q.text(prior.TEST),old[prior.TEST]);q.pin(DRIVER)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(prior.TEST)));c.require(cases=={n for n,_ in failed['steps'][0]['tests']},'SAME14_PREVIOUSLY_FAILED_CASE_IDENTITIES')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_VALID_IDS_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_VALID_IDS_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),prior249_replayed=False)),flush=True)
        harness.run_one('font_reference14_valid_contiguous_source_ids',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_VALID_IDS_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REFERENCE_SOURCE14_NOT_SCOPED_SEARCH_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=14,
            official249_and_other_old_suites_replayed=False,next_work='font_name_query_and_scoped_selection_then_current_stored_and_product_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_VALID_IDS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_VALID_IDS_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
