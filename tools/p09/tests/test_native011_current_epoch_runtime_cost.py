"""Whole original budget family with synthetic cost data, not Native evidence."""
import ast
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
import unittest
import native011_current_epoch_inventory_budget as inventory
import native011_current_epoch_runtime_cost as costs


def fixture():
    root=Path(__file__).resolve().parents[3]
    nodes=[node for node in ast.parse((root/costs.ORACLE).read_bytes()).body
        if isinstance(node,ast.FunctionDef) and node.name in ('runtime_budget','cost','retained_evidence','project_checker')]
    def require(ok,code):
        if not ok:raise ValueError(code)
    def model(required,requests):
        return dict(predicted_runtime_combined_seconds=100+requests/20,
            unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60)
    env=dict(require=require,views=NS(model=model),INVENTORY_REQUESTS=167,FINAL_SAMPLE_SECONDS=.5,
        FunctionType=FunctionType,NS=NS,mechanics_projection=object())
    exec(compile(ast.Module(body=nodes,type_ignores=[]),costs.ORACLE,'exec'),env)
    return NS(**env)


class RuntimeCostContracts(unittest.TestCase):
    def test_original_whole_code_and_same_count_across_all_four_paths(self):
        original=fixture();current,proof=costs.bind_family(original,170,inventory.bind)
        for name in ('runtime_budget','cost','retained_evidence','project_checker'):
            self.assertIs(getattr(current,name).__code__,getattr(original,name).__code__)
        self.assertEqual(current.cost({},14),current.runtime_budget({},170))
        self.assertIs(current.retained_evidence.__globals__['runtime_budget'],current.runtime_budget)
        self.assertEqual(original.INVENTORY_REQUESTS,167)
        self.assertFalse(proof['original_direct_namespace_mutated'])

    def test_original_count_equality_and_second_bind_refusal_retained(self):
        current,_=costs.bind_family(fixture(),170,inventory.bind)
        for value in (167,169,True):
            with self.assertRaisesRegex(ValueError,'UNCHANGED_WHOLE_RUST_INVENTORY'):
                current.runtime_budget({},value)
        with self.assertRaises(ValueError):costs.bind_family(current,170,inventory.bind)

    def test_full_projector_gets_current_cost_without_code_change(self):
        current,_=costs.bind_family(fixture(),170,inventory.bind)
        env=dict(mechanics_projection=object(),ORACLE_SCOPE=NS())
        exec('def selected():return ORACLE_SCOPE.cost({},14)',env)
        projected=current.project_checker(env['selected'],NS())
        self.assertIs(projected.__code__,env['selected'].__code__)
        self.assertEqual(projected(),current.runtime_budget({},170))
        self.assertIs(projected.__globals__['mechanics_projection'],current.mechanics_projection)

    def test_actual_private_engine_slot_only_and_default_namespace_refused(self):
        direct=fixture();env=dict(runtime_budget=direct.runtime_budget,keep=object())
        exec('def run_owned():raise AssertionError("MODEL_ENGINE_NEVER_EXECUTED")',env)
        function=env['run_owned'];engine=NS(run_owned=function)
        class Default:
            @property
            def __dict__(self):return env
        with self.assertRaisesRegex(ValueError,'PRIVATE_ENGINE_NOT_DEFAULT_MODULE'):
            costs.connect_engine(engine,direct,170,inventory.bind,modules=[Default()])
        keep=env['keep'];current,_=costs.connect_engine(engine,direct,170,inventory.bind,modules=[])
        self.assertIs(engine.run_owned,function);self.assertIs(env['keep'],keep)
        self.assertIs(env['runtime_budget'],current.runtime_budget)
        self.assertIsNot(env['runtime_budget'],direct.runtime_budget)

    def test_current_unexecuted_checker_keeps_validator_and_original_prior(self):
        original=NS(DIRECT=fixture(),keep=object());validator=object()
        env=dict(prior=original,base=NS(CONFIG=NS(index=165)),validator=validator)
        checker=NS(environment=env,projectors=[])
        direct,proof=costs.connect_checker(checker,170,inventory.bind)
        self.assertIs(env['validator'],validator);self.assertIs(env['prior'].keep,original.keep)
        self.assertIs(env['prior'].DIRECT,direct);self.assertEqual(original.DIRECT.INVENTORY_REQUESTS,167)
        self.assertFalse(proof['independent_checker_body_executed'])
        checker.projectors.append(object())
        with self.assertRaisesRegex(ValueError,'ACTUAL_CURRENT165_CHECKER_UNEXECUTED'):
            costs.connect_checker(checker,170,inventory.bind)

    def test_complete_cost_data_slot_inverse_keeps_all_original_limits(self):
        root=Path(__file__).resolve().parents[3]
        node=next(node for node in ast.parse((root/costs.PARENT_ORACLE).read_bytes()).body
            if isinstance(node,ast.FunctionDef) and node.name=='complete_cost')
        def require(ok,code):
            if not ok:raise ValueError(code)
        env=dict(require=require);exec(compile(ast.Module(body=[node],type_ignores=[]),costs.PARENT_ORACLE,'exec'),env)
        def connect():pass
        original=NS(complete_cost=env['complete_cost'],connect=connect)
        current,proof=costs.oracle_connection(original,170)
        seen=[]
        def runtime_budget(required,count,budget,checkpoint):
            seen.append(count)
            return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
                aggregate_envelope_decoder_allowance_seconds=5.0,predicted_runtime_combined_seconds=110)
        value=current.complete_cost(NS(runtime_budget=runtime_budget),{},None,lambda:None)
        self.assertEqual(seen,[170]);self.assertEqual(value['with_preparation15_seconds'],125)
        self.assertTrue(proof['entire_original_complete_cost_code_inverse'])
        self.assertFalse(proof['original600_margin60_shared5_readiness15_product10_changed'])
