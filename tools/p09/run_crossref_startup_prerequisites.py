"""Fresh readonly native startup observations plus8 pure contracts; never a native launch/session attempt."""
import ast,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_compiler_recovery as base
import crossref_startup_prerequisites as observed
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-crossref-startup-prerequisites240.v1.json'
DRIVER='tools/p09/run_crossref_startup_prerequisites.py'
MODULE='tools/p09/crossref_startup_prerequisites.py'
TEST='tools/p09/tests/test_crossref_startup_prerequisites.py'
DOC_BASE='implementation/p09/evidence/p09-361-sort-compiler-sync239.v1.json'
NATIVE={'tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py','tools/p09/crossref_owned_host_process.py',
    'tools/p09/crossref_preassigned_readonly.py','tools/p09/crossref_native_host_channel.py',
    'implementation/p09/tools/inspect-crossref-runtime-connection.ps1','implementation/p09/tools/crossref-fixed-batch.ps1',
    'implementation/p09/tools/crossref-native-case-ports.ps1','implementation/p09/tools/sdk-baseline-owned-session.ps1'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'XREF_STARTUP_PREREQUISITES_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_XREF_STARTUP_READONLY_INSPECTION',own_cpu_selection=selection,
        actual_Cargo=False,actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,permission_dialog_requested=False,OS_settings_changed=False,source_or_user_document_mutated=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=q.json(DOC_BASE)
        c.require(q.snapshots[DOC_BASE]['sha256']=='021d3a52307cea1992b3a53476f38b1307a05c0fc97cf58f48dc6fca7379e113'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==39,'EXACT239_PREVIOUS21_CASE_DOC_CLOSURE')
        for name in sorted(NATIVE|{DRIVER,MODULE,TEST,'CURRENT_STATE.md','tools/p09/run_sort_compiler_sync.py'}):q.pin(name)
        tree=ast.parse(q.text(MODULE));forbidden={'CreateProcessW','ResumeThread','TerminateProcess','Popen','run','system','create_suspended','resume','bind_owner','launch_app','create_job'}
        names=[node.func.attr if isinstance(node.func,ast.Attribute)else node.func.id if isinstance(node.func,ast.Name)else '' for node in ast.walk(tree)if isinstance(node,ast.Call)]
        c.require(not(set(names)&forbidden),'READONLY_INSPECTION_HAS_NO_NATIVE_PROCESS_COM_JOB_OR_UI_ACTIVATION_CALLS')
        c.require('P09InspectionDenyReader'in q.text('implementation/p09/tools/inspect-crossref-runtime-connection.ps1')
            and 'INSPECTION_REQUIRES_DENIAL'in q.text('implementation/p09/tools/inspect-crossref-runtime-connection.ps1'),
            'INSPECTED_FIXED_EIGHT_ENTRY_STILL_CLOSED_BEFORE_NATIVE_SLOT')
        funcs=lambda:(observed.startup.limits.validate_plan,observed.startup.read_registered_command,observed.startup.hwp_pids,observed.startup.parent_without_prompt_kill)
        originals=funcs();spec=importlib.util.spec_from_file_location('p09_xref_startup_prerequisite_contracts',c.ROOT/TEST)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();suite.run(result)
        c.require(result.testsRun==8 and not result.skipped and result.wasSuccessful(),'EXACT8_MODELED_READONLY_SOURCE_PREREQUISITE_CONTRACTS_NO_SKIPS')
        c.require(funcs()==originals,'ALL_ORIGINAL_NATIVE_OBSERVATION_FUNCTIONS_RESTORED_BEFORE_ACTUAL_INSPECTION')
        row['modeled_contracts_passed']=8
        executable=Path(observed.startup.limits.EXECUTABLE);image=a.AcceptanceReader(executable.parent,guard.check)
        row['actual_observation']=observed.inspect(guard.windows,guard.check,lambda:image.pin(executable.name))
        c.require(not row['actual_observation']['native_startup_qualified']and not row['actual_observation']['process_created']
            and not row['actual_observation']['COM_activated']and not row['actual_observation']['permission_dialog_requested'],'ACTUAL_READONLY_FACTS_NEVER_PROMOTED_TO_NATIVE_AUTHORITY')
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_STARTUP_PREREQUISITE_OBSERVATIONS_AND8_CONTRACTS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_executable_pins=list(image.snapshots.values()),
            external_final_fresh_hashes=image.final_fresh_hashes,old21_sort19_product20_and_official249_reexecuted=False,
            next_work='qualified_non_killing_native_host_lifecycle_and_complete_fixed_eight_native_provider_not_bypassing_closed_entry')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'XREF_STARTUP_READONLY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','modeled_contracts_passed','actual_observation','fresh_inputs','final_fresh_hashes','external_final_fresh_hashes',
            'cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
