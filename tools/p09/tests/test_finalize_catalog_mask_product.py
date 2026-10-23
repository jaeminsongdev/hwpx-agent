"""Pure fail-closed completion contracts. No Rust, worker, Native or artifact writes."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

MODULE=None


def fixture():
    names={f'case{i}'for i in range(45)}
    pins=[dict(path=MODULE.RECOVERY if i==0 else f'crates/input{i}.rs',bytes=i,sha256='a'*64)for i in range(851)]
    limits=dict(verified=True,affinity_mask=4,cpu_hard_cap_machine_percent=6.25,priority_class=16384,
        active_process_limit=16,kill_on_close=True,breakaway_disabled=True)
    job={key:True for key in('worker_created','job_assigned','target_authorized','owned_tree_empty','cleanup_confirmed','job_handle_closed')}
    job.update(limits_readback=limits,last_job_accounting=dict(active_processes=0,owned_processes=[],peak_job_private_percent=2.6))
    row=dict(state='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE',error_code='STOP_PREPARATION_SYSTEM_PRESSURE90',
        error_type='ValueError',cleanup=True,installed_config_final_fresh_hashes=1,product_cases_executed=45,
        new_product_cases=42,affected_product_cases=3,complete_compile_input_closure_checked=True,source_pins=pins,
        actual_compiled_test_inputs=[dict(dependency_paths=[p['path']for p in pins[1:14]])],
        steps=[dict(stage='optimized_catalog_products_shared_compiler45',exit_code=0,cleanup=True,diagnostics=[],
            tests=[(name,'ok')for name in sorted(names)],owned_job=job)])
    row.update({key:False for key in('actual_DB_Hangul_or_COM_started','Native011_executed','prior_Native_replayed',
        'official249_replayed','source_document_mutation','ingest_commit_or_publication','native_execution_authorized')})
    return row,names


class Tests(unittest.TestCase):
    def rejection(self,mutate):
        row,names=fixture();mutate(row)
        with self.assertRaises((ValueError,KeyError,TypeError)):MODULE.validate_observation(row,names)

    def test_exact_readonly_observation_is_not_itself_acceptance(self):
        row,names=fixture();self.assertFalse(MODULE.validate_observation(row,names)['product_or_Native_replay_allowed'])
        self.assertFalse(MODULE.successful_exit(row))

    def test_other_stop_is_not_recoverable(self):self.rejection(lambda r:r.update(error_code='OTHER_FAILURE'))
    def test_missing_final_installed_check_rejects(self):self.rejection(lambda r:r.update(installed_config_final_fresh_hashes=0))
    def test_native_replay_is_never_eligible(self):self.rejection(lambda r:r.update(Native011_executed=True))
    def test_source_mutation_is_never_eligible(self):self.rejection(lambda r:r.update(source_document_mutation=True))
    def test_nonzero_body_exit_rejects(self):self.rejection(lambda r:r['steps'][0].update(exit_code=101))
    def test_warnings_reject(self):self.rejection(lambda r:r['steps'][0].update(diagnostics=['warning']))
    def test_failed_body_rejects(self):self.rejection(lambda r:r['steps'][0]['tests'].__setitem__(0,('case0','FAILED')))
    def test_duplicate_passing_name_rejects(self):self.rejection(lambda r:r['steps'][0]['tests'].__setitem__(0,r['steps'][0]['tests'][1]))
    def test_active_job_rejects(self):self.rejection(lambda r:r['steps'][0]['owned_job']['last_job_accounting'].update(active_processes=1))
    def test_unclosed_handle_rejects(self):self.rejection(lambda r:r['steps'][0]['owned_job'].update(job_handle_closed=False))
    def test_multiple_cpu_affinity_rejects(self):self.rejection(lambda r:r['steps'][0]['owned_job']['limits_readback'].update(affinity_mask=3))
    def test_boolean_affinity_rejects(self):self.rejection(lambda r:r['steps'][0]['owned_job']['limits_readback'].update(affinity_mask=True))
    def test_duplicate_source_path_rejects(self):self.rejection(lambda r:r['source_pins'].__setitem__(2,copy.deepcopy(r['source_pins'][1])))
    def test_escaped_source_path_rejects(self):self.rejection(lambda r:r['source_pins'][1].update(path='../outside.rs'))
    def test_boolean_source_size_rejects(self):self.rejection(lambda r:r['source_pins'][1].update(bytes=True))
    def test_missing_actual_test_input_rejects(self):self.rejection(lambda r:r['actual_compiled_test_inputs'][0]['dependency_paths'].__setitem__(0,'crates/unknown.rs'))

    def readers(self,error=None):
        source=NS(snapshots={'a':{},'b':{}},final_fresh_hashes=0)
        def finish():
            source.final_fresh_hashes=1
            if error:raise error
            source.final_fresh_hashes=2
        source.finish=finish
        installed=NS(final_fresh_hashes=0)
        def installed_finish():installed.final_fresh_hashes=1
        installed.finish=installed_finish
        return source,installed

    def test_partial_fresh_failure_retains_counts_and_never_passes(self):
        source,image=self.readers(ValueError('STOP'));row=dict(state=MODULE.OBSERVED)
        with self.assertRaisesRegex(ValueError,'STOP'):MODULE.closing_fresh(row,source,image,NS(check=lambda **_:None))
        self.assertEqual(row['final_fresh_hashes'],1);self.assertEqual(row['installed_config_final_fresh_hashes'],1)
        self.assertEqual(row['state'],MODULE.OBSERVED);self.assertFalse(MODULE.successful_exit(row))

    def test_final_guard_failure_never_passes(self):
        source,image=self.readers();row=dict(state=MODULE.OBSERVED)
        def stop(**_):raise ValueError('STOP')
        with self.assertRaisesRegex(ValueError,'STOP'):MODULE.closing_fresh(row,source,image,NS(check=stop))
        self.assertEqual(row['final_fresh_hashes'],2);self.assertFalse(MODULE.successful_exit(row))

    def test_final_fresh_cannot_reenter_after_failure(self):
        source,image=self.readers(ValueError('STOP'));row={}
        with self.assertRaises(ValueError):MODULE.closing_fresh(row,source,image,NS(check=lambda **_:None))
        with self.assertRaisesRegex(ValueError,'NOT_REENTERED'):MODULE.closing_fresh(row,source,image,NS(check=lambda **_:None))

    def test_complete_fresh_only_becomes_eligible_after_explicit_success_label(self):
        source,image=self.readers();row=dict(state=MODULE.OBSERVED,cleanup=True)
        MODULE.closing_fresh(row,source,image,NS(check=lambda **_:None));self.assertFalse(MODULE.successful_exit(row))
        row['state']=MODULE.PASS;self.assertTrue(MODULE.successful_exit(row))

    def test_pass_label_plus_error_is_failure(self):
        row=dict(state=MODULE.PASS,cleanup=True,fresh_inputs=2,final_fresh_hashes=2,
            installed_config_final_fresh_hashes=1,error_code='STOP')
        self.assertFalse(MODULE.successful_exit(row))

    def test_original_runner_exit_contract_refuses_prior_premature_pass(self):
        path=Path(__file__).resolve().parents[1]/'run_personal_info_catalog_mask_product_recovery.py'
        tree=ast.parse(path.read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='successful_exit')
        namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
        accept=namespace['successful_exit'];row=dict(cleanup=True,state='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE')
        self.assertFalse(accept(row));row.update(fresh_inputs=2,final_fresh_hashes=2);self.assertTrue(accept(row))
        for key in('error_code','error_type','failed_final_fresh_check'):
            changed=dict(row);changed[key]=True if key=='failed_final_fresh_check'else'STOP';self.assertFalse(accept(changed))

    def test_original_runner_installs_pass_only_after_mandatory_finish(self):
        path=Path(__file__).resolve().parents[1]/'run_personal_info_catalog_mask_product_recovery.py'
        tree=ast.parse(path.read_text(encoding='utf-8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        pass_lines=[n.lineno for n in ast.walk(main)if isinstance(n,ast.Constant)and n.value=='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE']
        finish_lines=[n.lineno for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
            and isinstance(n.func.value,ast.Name)and n.func.value.id=='q'and n.func.attr=='finish']
        self.assertEqual(len(pass_lines),1);self.assertGreater(pass_lines[0],min(finish_lines))
