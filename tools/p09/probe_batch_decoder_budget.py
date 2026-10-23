"""Full162 two-role decoder workload diagnostic, never a Native Frame.

The original metadata/Frame budget classes execute direct decoder operations.
Two fresh passes per role are only a lower bound for actual parent admission.
No synthetic source_frame, candidate, GO, process, timer reset or acceptance.
"""
import json
import re
import sys
import time
from pathlib import Path

SELF='tools/p09/probe_batch_decoder_budget.py'


def workload(descriptors):
    names=[d['semantic_original_pin']['path'] for d in descriptors]
    physical=[d['physical_envelope_pin']['path'] for d in descriptors]
    if len(names)!=162 or len(set(names))!=162 or len(set(physical))!=162:
        raise ValueError('DECODER_PROBE_EXACT_UNIQUE162')
    return tuple((role,number,d) for role in ('metadata','frame')
        for number in (1,2) for d in descriptors)


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
    if sys.argv[1:]:raise ValueError('DECODER_PROBE_NO_EXTRA_ARGUMENTS')
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            raise ValueError('DECODER_PROBE_PROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import batch_engine_connection as entry,owned_source_read_pressure as bytes_policy
    bootstrap=entry.bootstrap_loader(c.ROOT)
    guards,_=bootstrap.load(c.ROOT,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    factory=guards.owned_cpu_baseline_v1.guard_type(guards.terminal_metadata_pressure_v1.guard_type(
        guards.distinct_final_sample_guard_v1.guard_type(a.Guard)))
    guard=factory();source=physical=shared=None;budgets={};progress=[];stage='CONSTRUCTION'
    row=dict(state='FAILED_FULL162_DECODER_LOWER_BOUND_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,actual_Native_Frame_created=False,actual_product_or_worker_executed=False,
        minimum_workload_not_actual_parent_metadata_admission=True,Frame_role_is_direct_budget_not_Native_evidence=True)
    started=time.monotonic()
    try:
        guard.acquire();source=a.AcceptanceReader(c.ROOT,guard.check);source.pin(SELF);source.pin(entry.SELF)
        for pin in entry.BOOTSTRAP:a.exact(source.pin(pin['path']),pin,'ORIGINAL_BOOTSTRAP')
        libraries,_=entry.planning_libraries(c.ROOT,source,a,bootstrap)
        admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
        data=admission.read_plan(source,a,batch,reuse);entry.extend_execution(data,source,batch)
        config_pin=data.planned.logical['tools/p09/current_queue_successor_lossless_runtime_v4.py']
        loader=batch.PacedNamespaceLoader(bootstrap,source,{config_pin['path']:config_pin}).api
        config,_=loader.load(c.ROOT,[config_pin],{})
        entry.private_package_imports(admission,libraries.batch_worker_entry,bootstrap,
            config.current_queue_successor_lossless_runtime_v4)
        connected=admission.connect_package(c.ROOT,source,data,a,batch,bytes_policy)
        binding=connected.graph.binding
        descriptors=entry.current_mappings(binding,data.planned.current);tasks=workload(descriptors)
        required=entry.current_logical(data,binding,guard.check,batch.scope,a.exact)
        projection,_=binding.project(required,guard.check)
        shared=connected.metadata_libraries.shared_metadata_frame_decoder_budget_v1.SharedBudget()
        original=connected.graph.frames.connection.original.DecoderBudget
        for role in ('metadata','frame'):budgets[role]=shared.attach(role,original(guard.check))
        source.finish();guard.check(force=True)
        a.exact(source.final_fresh_hashes,len(source.snapshots),'ALL_CONSTRUCTION_CLOSING')
        row.update(source_pins=list(source.snapshots.values()),source_fresh=len(source.snapshots),
            source_final=source.final_fresh_hashes,planned_direct_decodes=len(tasks),descriptor_count=len(descriptors))
        physical=a.AcceptanceReader(c.ROOT,guard.check);stage='DECODER_WORK'
        for role,number,descriptor in tasks:
            guard.check();pin=descriptor['physical_envelope_pin'];semantic=descriptor['semantic_original_pin']
            actual,raw=physical._read(pin['path'],parse=True);physical._bind(actual['path'],actual)
            a.exact(actual,pin,'FRESH_EXACT_CARRIER_NOT_CACHE')
            raw=bytes(raw)
            decoded=budgets[role].run(lambda check:projection.decode_fresh(semantic['path'],actual,raw,check))
            a.require(type(decoded) is bytes and len(decoded)==semantic['bytes'],'ORIGINAL_FULL_DECODED_BYTES')
            progress.append((role,number))
            del decoded,raw
        physical.finish();guard.check(force=True)
        a.exact(physical.final_fresh_hashes,len(physical.snapshots),'ALL_CARRIER_CLOSING')
        row['state']='PASS_FULL162_DECODER_LOWER_BOUND_NOT_NATIVE_OR_ADMISSION'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        row.update(error_type=type(error).__name__,failure_stage=stage)
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):
            row['error_code']=error.args[0]
    finally:
        guard.close()
        if shared is not None:
            try:row['direct_role_budget_evidence']=shared.evidence()
            finally:shared.restore()
        row['completed_by_role_pass']={role+str(number):progress.count((role,number))
            for role in ('metadata','frame') for number in (1,2)}
        row['completed_direct_decodes']=len(progress)
        if physical is not None:
            row['physical_reader']=dict(fresh_inputs=len(physical.snapshots),final_fresh_hashes=physical.final_fresh_hashes,
                read_passes=physical.read_passes,physical_bytes_read=physical.bytes_read)
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
        print(json.dumps(row))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup is True else 2


if __name__=='__main__':raise SystemExit(main())
