import ast
import copy
import hashlib
import sys
import unittest
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_diagnostic_connection_v1 as connection


def fixture():
    probe=dict(backend=connection.BACKEND,maximum_sample_budget_seconds=.05,total_added_sample_budget_seconds=2.,
               setup_included_in_same_cost_budget=True,maximum_query_calls=128,query_remaining=False,cleanup_confirmed=True,
               PDH_or_WMI_called=False,original_CPU_RAM_guards_replaced=False,second_sampler_thread_or_process=False,
               DPC_and_interrupt_counters_unavailable_not_zero=True,runtime_connection_qualified=False,PC_freeze_resolved=False,
               capture_failure_cleanup_unknown=False,native_capture_handle_cleanup_status="CONFIRMED",
               capture_error_never_promoted_to_successful_cleanup=True,automatic_retry_or_resume=False,
               query_calls=3,samples=2,maximum_added_sample_seconds=.009,total_added_sample_seconds=.026,disabled_reason=None)
    bind=dict(original_entry_bytecode_retained=True,local_dependency_changes=1,
              original_GO_Job_source_byte_resource_and_cleanup_unchanged=True,old_PDH_default_module_not_mutated=True,
              PDH_factory_instantiated=False,second_sampler_thread_or_process=False,actual_factory_instances=1,
              native_backend_source="tools/p09/native_process_cpu_attribution_v2.py",runtime_product_connection_qualified=False,PC_freeze_resolved=False)
    info=dict(backend=connection.BACKEND,existing_observer_instances=1,cold_counter_interval_seconds=8.,
              original_warning_for_forced_read_percent=75,original_CPU_RAM_decisions_replaced=False,
              additional_PDH_queries_explicit=False,additional_native_process_queries_explicit=True,
              second_sampler_thread_or_process=False,interval_identical_to_K32_interval=False,runtime_connection_qualified=False,
              PC_freeze_resolved=False,native_backend_connection=bind,probes=[probe])
    values=dict(total_cpu=20.,DPC_cpu=None,interrupt_cpu=None,
                MsMpEng=dict(pid=None,pid_stable=False,creation_identity_bound=False,machine_cpu_percent=None,status="UNAVAILABLE_OR_NEW_PID"),
                System=dict(pid=4,pid_stable=True,creation_identity_bound=True,machine_cpu_percent=5.,status="OBSERVED"))
    delta=dict(window_seconds=8.,complete_system_CPU_attribution=False,matched_machine_CPU_sum=5.,matched_processes=1,
               new_or_reused_pid_no_baseline=0,negative_delta_unresolved=0,unavailable_current=1,process_list_truncated=False,
               top_processes=[dict(pid=4,parent=0,role="system",machine_CPU_percent=5.)])
    diagnostic=dict(available=True,fresh_for_this_original_resource_sample=True,coverage_complete=False,PDH_or_WMI_called=False,
                    total_cpu_from_original_K32_not_a_second_query=True,DPC_and_interrupt_counters_unavailable_not_zero=True,
                    interval_seconds=8.,identical_to_original_K32_interval=False,causal_trigger_attribution_established=False,
                    values=values,process_deltas=delta)
    return dict(serial_CPU_attribution=info,samples=[dict(system_cpu_percent=20.,serial_cpu_attribution=diagnostic)])


class Tests(unittest.TestCase):
    def reject(self,row):
        with self.assertRaises((ValueError,KeyError,TypeError)):connection.validate(row)

    def test_valid_native_schema_not_product_oracle(self):
        proof=connection.validate(fixture())
        self.assertEqual(proof["available_native_diagnostics"],1)
        self.assertFalse(proof["full_product_source_resource_oracle_replaced"])

    def test_old_PDH_not_relabelled(self):
        row=fixture();row["serial_CPU_attribution"]["backend"]="PDH";self.reject(row)

    def test_extra_observer_and_boolean_count_rejected(self):
        for value in (2,True):
            row=fixture();row["serial_CPU_attribution"]["existing_observer_instances"]=value;self.reject(row)

    def test_PDH_or_weakened_original_guard_rejected(self):
        for key in ("PDH_factory_instantiated","second_sampler_thread_or_process"):
            row=fixture();row["serial_CPU_attribution"]["native_backend_connection"][key]=True;self.reject(row)
        row=fixture();row["serial_CPU_attribution"]["original_CPU_RAM_decisions_replaced"]=True;self.reject(row)

    def test_unknown_cleanup_rejected(self):
        row=fixture();row["serial_CPU_attribution"]["probes"][0]["capture_failure_cleanup_unknown"]=True;self.reject(row)

    def test_cost_increase_and_invalid_counter_rejected(self):
        for key,value in (("maximum_sample_budget_seconds",.1),("maximum_query_calls",129),("query_calls",True)):
            row=fixture();row["serial_CPU_attribution"]["probes"][0][key]=value;self.reject(row)

    def test_DPC_zero_and_false_K32_value_rejected(self):
        for key,value in (("DPC_cpu",0.),("total_cpu",21.)):
            row=fixture();row["samples"][0]["serial_cpu_attribution"]["values"][key]=value;self.reject(row)

    def test_PID_stability_and_System4_enforced(self):
        row=fixture();row["samples"][0]["serial_cpu_attribution"]["values"]["System"]["pid"]=5;self.reject(row)
        row=fixture();row["samples"][0]["serial_cpu_attribution"]["values"]["MsMpEng"]["machine_cpu_percent"]=0.;self.reject(row)

    def test_top_process_privacy_and_duplicates(self):
        row=fixture();row["samples"][0]["serial_cpu_attribution"]["process_deltas"]["top_processes"][0]["command"]="MUST_NOT_EXPOSE";self.reject(row)
        row=fixture();top=row["samples"][0]["serial_cpu_attribution"]["process_deltas"]["top_processes"];top.append(copy.deepcopy(top[0]));self.reject(row)

    def test_unavailable_and_cold_interval_truthful(self):
        row=fixture();row["samples"][0]["serial_cpu_attribution"]=dict(available=False,values=None,reason="NOT_SAMPLED_COLD_INTERVAL",fresh_for_this_original_resource_sample=False)
        self.assertEqual(connection.validate(row)["available_native_diagnostics"],0)
        row["samples"][0]["serial_cpu_attribution"]["fresh_for_this_original_resource_sample"]=True;self.reject(row)

    def test_definitions_exact_no_CLI_or_registration(self):
        raw=b"import missing_module\nVALUE=3\ndef function():return VALUE\nif __name__=='__main__':raise AssertionError()\n"
        pin=dict(path="fixture.py",bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        ns,proof=connection.definitions(raw,pin,{})
        self.assertEqual(ns.function(),3);self.assertFalse(proof["full_module_or_CLI_import_executed"])
        with self.assertRaises(ValueError):connection.definitions(raw+b" ",pin,{})

    def test_connector_only_local_dependency_preserves_bytecode(self):
        def run():return attribution
        old_attribution=object()
        fn=FunctionType(run.__code__,dict(attribution=old_attribution))
        api=NS(run_owned=fn);calls=[]
        old=NS(bind_entry=lambda a,r:calls.append("original_proof"))
        backend=NS(SELF="tools/p09/native_process_cpu_attribution_v2.py",windows_type=lambda *a:None,
                   close=lambda *a:True,summary=lambda *a:dict(backend=connection.BACKEND))
        state=dict(actual_local_bindings=0)
        connection.connect_entry(api,b"raw",old,backend,state)
        self.assertEqual(calls,["original_proof"]);self.assertIs(api.run_owned.__code__,run.__code__)
        self.assertEqual(state["actual_local_bindings"],1)
        self.assertIsNot(api.run_owned(),old_attribution)

    def test_unrelated_leaf_or_missing_chain_rejected(self):
        def fn():return 1
        with self.assertRaises(ValueError):connection.connect_run(fn,NS())

    def test_clone_chain_and_original_namespace_unchanged(self):
        def leaf():return connection
        leaf=FunctionType(leaf.__code__.replace(co_filename=connection.LEAF),dict(connection=NS(bind_entry=lambda *a:None)))
        original=NS(run_owned=leaf)
        def outer():return source.run_owned()
        outer=FunctionType(outer.__code__,dict(source=original))
        cloned,state=connection.connect_run(outer,NS())
        self.assertIs(cloned.__code__,outer.__code__);self.assertIs(original.run_owned,leaf)
        self.assertEqual(len(state["cloned_functions"]),2);self.assertEqual(state["static_leaf_connections"],1)


if __name__=="__main__":unittest.main()
