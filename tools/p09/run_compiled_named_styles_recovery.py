"""346: only move the new test module after fixture macros; original345 compile failure retained."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_compiled_named_styles as base
shared,c,a,tools,compact,harness,audit=base.shared,base.c,base.a,base.tools,base.compact,base.harness,base.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-named-styles-recovery346.v1.json';DRIVER='tools/p09/run_compiled_named_styles_recovery.py'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_NAMED_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_NAMED_STYLE_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_giant_suite_executed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a28972345759ca8830bc6549208134af9000be1e379779baf472609ca48eae89'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==804 and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['macro_not_in_scope_observed'],'EXACT345_TEST_MODULE_MACRO_ORDER_COMPILE_FAILURE_NO_TESTS')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n!=base.PARENT:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_TEST_BODIES_AND_GUARDS_UNCHANGED_AFTER345')
        text=q.text(base.PARENT);restored=base.remove(text,base.LINK);first=restored.splitlines(keepends=True)[0]
        audit.inverse(restored.replace(first,first+base.LINK,1),old[base.PARENT],'ONLY_NEW_MODULE_DECLARATION_MOVED_AFTER_FIXTURE_MACROS')
        passed=compact.unpack(q.json(base.previous.OUTPUT));base.inverse(q,{p['path']:p for p in passed['source_pins']})
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled_named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))};c.require(len(cases)==19,'EXACT19_NEW_NAMED_COMMON_CASES')
        scratch=c.ROOT/'target/p09-compiled-named-styles-recovery-scratch-346';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_NAMED_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='COMPILED_NAMED_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=12)),flush=True)
        for binary,label,selected in [('named_style_product','compiled_named_new19_affected3',cases|base.AFFECTED_NAMED),('scoped_font_product','affected_common_font_and_legacy9',base.AFFECTED_FONT)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,
                observe_capture=base.previous.previous.previous.base.snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'COMPILED_NAMED_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_NAMED_STYLE_MUTATION_COMPILER_SEPARATE_PREVIEW19_AFFECTED12_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=12,mutation_families=21,preview_never_enters_mutation_compiler=True,full_named_output_receipt_bound_to_plan=True,
            next_work='named_character_styles_filters_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_NAMED_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_NAMED_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
