"""One failed case, unchanged source: collect closed compiler variants, never raw XML/logs."""
import json,re,time,sys
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_style_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-text-style-failure133.v1.json'
CASE='text_style_partial_entity_spelling_and_run_shell_are_preserved'


def snapshot(capture,expected):
    result=base.snapshot(capture,expected)
    with capture.lock:
        raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    allowed={'Source','Search','Value','Selection','Protection','FieldContent','NoMatches','NoChange','Limit','Patch','Writer','Readback','Preservation'}
    result['closed_compile_error_variants']=[n for n in re.findall(r'Error: Compile\(([A-Za-z_]+)',raw)if n in allowed]
    # Static patch error codes contain no source names/values; retain only this constrained domain.
    result['closed_patch_codes']=re.findall(r'Error: Compile\(Patch\("(PATCH_[A-Z0-9_]{1,96})"\)\)',raw)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_STYLE_DIAGNOSTIC_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_STYLE_DIAGNOSTIC',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,diagnostic_only=True,formal_case_acceptance=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        failed=q.json('implementation/p09/evidence/p09-361-text-style-recovery132.v1.json')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-text-style-recovery132.v1.json']['sha256']=='30bf84adfdb437c1c4f7f00cda02813332106f23b9d4a90748c1b1c684f4e08f'
            and failed['cleanup']and sum(s=='ok'for n,s in failed['steps'][0]['tests'])==5
            and CASE in {n for n,s in failed['steps'][0]['tests']if s!='ok'},'EXACT_FIVE_PASSED_ELEVEN_FAILED_RECORD_PRESERVED')
        pins={p['path']:p for p in failed['source_pins']};names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name);c.require(q.snapshots[name]==pins[name],'NO_PRODUCT_TEST_FIXTURE_OR_CORE_CHANGE_FOR_SINGLE_FAILURE_DIAGNOSIS')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        try:
            base.harness.run_one('one_failed_text_style_closed_error_diagnostic',[base.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
                '--test','text_style_replacement','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,base.audit.environment(),row,observe_capture=snapshot)
        except ValueError as error:
            c.require(str(error)=='SOURCE_NOTE_API_COMMAND_FAILED','EXPECTED_FAILED_DIAGNOSTIC_COMMAND_ONLY')
        step=row['steps'][0];observation=step['bounded_output_observation']
        c.require(len(step['tests'])==1 and step['tests'][0][0]==CASE and step['tests'][0][1]!='ok'
            and step['exit_code']==101 and len(observation['closed_compile_error_variants'])==1,'ONE_FAILED_CASE_CLOSED_VARIANT_CAPTURED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_STYLE_CLOSED_FAILURE_DIAGNOSIS_NOT_PRODUCT_OR_COMPONENT_PASS',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            closed_compile_error_variants=observation['closed_compile_error_variants'],closed_patch_codes=observation['closed_patch_codes'],unchanged_passed_five_reexecuted=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_STYLE_DIAGNOSTIC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','closed_compile_error_variants','closed_patch_codes','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
