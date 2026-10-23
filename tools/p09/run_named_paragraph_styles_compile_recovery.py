"""339: explicitly qualify two regex crate references; all26 unexecuted tests remain unchanged."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_paragraph_styles_recovery as previous
base=previous.previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles-compile-recovery339.v1.json';DRIVER='tools/p09/run_named_paragraph_styles_compile_recovery.py'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_COMPILE_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_COMPILE_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,stored_product_common_dispatch_or_preview_connected=False,
        tests_and_legacy_algorithms_unchanged_from337=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='782c42f5c6b4347e45882a32fe0b9a0c1154f106004ed56218ffcee5191d08b5'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==787 and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101
            and failed['steps'][0]['tests']==[]and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0425','E0433'],'EXACT338_TWO_REGEX_NAMESPACE_COMPILE_ERRORS_NO_EXECUTED_TESTS')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n!=base.NAMED:c.require(q.snapshots[n]==old[n],'ALL_TESTS_LEGACY_PRODUCTION_FIXTURES_AND_VERIFIERS_UNCHANGED')
        text=q.text(base.NAMED);c.require(text.count('::regex::escape')==text.count('::regex::RegexBuilder')==1,'EXACT_TWO_CRATE_QUALIFIERS')
        audit.inverse(text.replace('::regex::escape','regex::escape').replace('::regex::RegexBuilder','regex::RegexBuilder'),old[base.NAMED],'ALL_OTHER_NAMES_RESOLUTION_SELECTION_GUARDS_PATCH_AND_READBACK_CODE_UNCHANGED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}|base.AFFECTED;c.require(len(cases)==26,'SAME26_UNEXECUTED_SOURCE_AND_AFFECTED_CASES')
        scratch=c.ROOT/'target/p09-named-paragraph-style-scratch-339';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_PARAGRAPH_COMPILE_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_PARAGRAPH_COMPILE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=7,two_crate_qualifiers_only=True)),flush=True)
        harness.run_one('named_paragraph_styles19_affected_original7_explicit_regex_crate',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_paragraph_style_replacement',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_PARAGRAPH_COMPILE_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARAGRAPH_STYLE_SOURCE_BATCH19_AFFECTED7_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=7,next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_COMPILE_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples]
            c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_PARAGRAPH_COMPILE_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
