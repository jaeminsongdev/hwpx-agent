"""Same17 regex cases in a focused target on logical CPU2; all original resource limits remain."""
import ctypes,json,re,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_replacement_recovery as prior
shared,c,a,audit=prior.shared,prior.c,prior.a,prior.audit
base=prior.base
OUTPUT='implementation/p09/evidence/p09-361-regex-replacement-focused114.v1.json'
FOCUSED='crates/hwpx-package/tests/regex_replacement_focused.rs'


def select_own_single_cpu():
    # Only this newly launched verifier is changed. Do not open or alter any other process.
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.GetProcessAffinityMask.argtypes=[w.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)];kernel.GetProcessAffinityMask.restype=w.BOOL
    kernel.SetProcessAffinityMask.argtypes=[w.HANDLE,ctypes.c_size_t];kernel.SetProcessAffinityMask.restype=w.BOOL
    handle=kernel.GetCurrentProcess();allowed=ctypes.c_size_t();system=ctypes.c_size_t();mask=4
    c.require(kernel.GetProcessAffinityMask(handle,ctypes.byref(allowed),ctypes.byref(system))and allowed.value&mask==mask,'FOCUSED_SINGLE_CPU_NOT_ALLOWED')
    before=allowed.value;c.require(mask.bit_count()==1 and kernel.SetProcessAffinityMask(handle,mask),'FOCUSED_OWN_SINGLE_CPU_NOT_SET')
    c.require(kernel.GetProcessAffinityMask(handle,ctypes.byref(allowed),ctypes.byref(system))and allowed.value==mask,'FOCUSED_OWN_SINGLE_CPU_READBACK')
    return dict(initial_allowed_mask=before,selected_logical_cpu=2,selected_mask=mask,selected_cpu_count=1,only_current_verifier_changed=True)


def inventory(check):return base.inventory(check)|{FOCUSED}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_FOCUSED_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_REPLACEMENT_FOCUSED',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_zero_width_or_native_qualification_added=False)
    try:
        guard.acquire();c.require(guard.windows.mask==4 and guard.windows.mask.bit_count()==1,'SAME_ONE_CPU_LIMIT_ON_SEPARATE_LOGICAL_CPU')
        q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        stopped=q.json(prior.OUTPUT);failed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='69de98f688e2dbf7caa21fecfdf6b7670658990b5da179d1c81c48364053e083'
            and stopped['state']=='FAILED_REGEX_REPLACEMENT_RECOVERY'and stopped['error_code']=='STOP_SOURCE_NOTE_API_COMMAND_DEADLINE'and stopped['cleanup'],
            'ORIGINAL_CPU0_BUILD_DEADLINE_AND_UNCONFIRMED_TEST_EXECUTION_PRESERVED')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='f53fd16a7e66e637f3bdfb9cf9c303ae757f118a1b86280bc6222207fc28459b'
            and failed['cleanup'],'ORIGINAL_EIGHTY_SIX_PASSES_TWO_FAILURES_PRESERVED')
        paused={p['path']:p for p in stopped['source_pins']};initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        expected_names={n for n in paused if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.prior.prior.base.CAPTURE}}
        c.require(names==expected_names|{FOCUSED},'ONLY_ONE_NEW_FOCUSED_TARGET_NO_NEW_SOURCE_FIXTURE_OR_TEST_BODY')
        for name in names-{FOCUSED}:c.require(q.snapshots[name]==paused[name],'NO_REGEX_PRODUCT_MATCHER_PROTECTION_OR_TEST_SOURCE_CHANGE_SINCE_TIMED_OUT_RUN')
        c.require(q.text(FOCUSED)=='//! Only the same17 regex cases; no compiled copies of the72 retained original case bodies.\n#[path="document_import_regex_replacement.rs"] mod regex_replacement;\n',
            'ONLY_EXACT_ORIGINAL_SEVENTEEN_CASE_MODULE_INCLUDED')
        base.inverse(q,old);prior.budget_inverse(q,initial);prior.test_inverse(q,initial);cases=prior.expected(q)
        step=failed['steps'][0];c.require(len(step['tests'])==88 and {n for n,s in step['tests']if s!='ok'}==prior.FAILED
            and len([n for n,s in step['tests']if s=='ok'and not n.startswith('regex_replacement::')])==72,'EXACT_UNCHANGED_SEVENTY_TWO_ORIGINAL_PASSES_RETAINED')
        print(json.dumps(dict(state='REGEX_FOCUSED_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_original_cases=72,focused_cases=17,one_cpu_mask=4,global_helpers_changed=False)),flush=True)
        base.harness.run_one('same_seventeen_regex_cases_focused_single_cpu2',[base.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_replacement_focused','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.prior.snapshot)
        job=row['steps'][0]['owned_job'];limits=job['limits_readback']
        c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ONE_CPU2_AND_ORIGINAL_CPU_CAP_PRIORITY_LIMITS_ACTUALLY_VERIFIED')
        c.require(inventory(guard.check)==names,'FINAL_REGEX_FOCUSED_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_REPLACEMENT_SEVENTY_TWO_RETAINED_SEVENTEEN_FOCUSED_NOT_STORED_PRODUCT_ZERO_WIDTH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=17,retained_original_cases=72,total_distinct_core_cases=89,
            actual_current_cases=17,previous_failed_and_deadline_runs_preserved=True,common_guard_or_other_process_settings_changed=False,
            capture_expansion_work_bounded_independently_of_output_bytes=True,one_regex_pass_and_one_original_protected_writer_for_variable_capture_expansions=True,
            next_work='Current_stored_and_strict_product_binding_of_regex_capture_candidates_then_remaining_full_contract_and_zero_width_insertions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_FOCUSED_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_FOCUSED_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
