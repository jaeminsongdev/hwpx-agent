"""Original whole engine code with explicit physical Frame/row dependencies.

Bootstrap keeps every original pin. The original runtime budget projects its
physical IO, and the original Frame methods operate on that same projection.
No observed byte counter is relabelled as semantic IO. The full product oracle
and real worker transport still require independent qualification.
"""
from types import FunctionType, SimpleNamespace as NS
from unittest.mock import patch
import runtime_envelope_frame_connection_v1 as frames
import runtime_envelope_raw_access_policy_v1 as access

SELF="tools/p09/runtime_envelope_parent_connection_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_parent_connection_v1.py"
source=access.source


def connect_engine(engine, binding):
    original=engine.run_owned;env=original.__globals__
    source.require(type(original) is FunctionType and type(binding) is source.Binding,
        "PARENT_CONNECTION_EXACT_TYPES")
    source.require(all(n in env for n in ("native","runtime_budget","binding","json","c")),
        "PARENT_CONNECTION_WHOLE_ENGINE_INTERFACE")
    source.require(hasattr(env["native"],"frames"),"PARENT_CONNECTION_ORIGINAL_FRAMES")
    state=NS(attempts=0,bootstrap_calls=0,budget_calls=0,dump_calls=0,frames=[],
        original=original,original_worker=engine.worker,metadata_guard=None)
    projected=frames.frame_type(env["native"].frames.Frame,binding)

    class Frame(projected):
        def __init__(self,registry,required,checkpoint,held=None):
            source.require(not state.frames,"PARENT_CONNECTION_ONE_ORIGINAL_FRAME")
            super().__init__(registry,required,checkpoint,held=held)
            self.raw_policy=access.Policy(env["c"].ROOT,binding,lambda:registry.active is self,checkpoint)
            self.policy_context=None;self.policy_installed_once=False
            state.frames.append(self)

        def acquire(self):
            source.require(self.policy_context is None and not self.policy_installed_once,
                "PARENT_CONNECTION_ONE_LIVE_POLICY_INSTALL")
            self.policy_context=self.raw_policy.install()
            self.policy_context.__enter__();self.policy_installed_once=True
            return super().acquire()

        def restore_policy(self):
            if self.policy_context is not None:
                context=self.policy_context;self.policy_context=None
                context.__exit__(None,None,None)

        def close(self):
            result=super().close()
            if result:self.restore_policy()
            return result

        def summary(self):
            return dict(super().summary(),parent_python_live_raw_access_policy=self.raw_policy.evidence(),
                parent_live_raw_policy_installed=self.policy_installed_once,
                worker_process_and_full_product_connection_qualified=False)

    native=NS(**{**vars(env["native"]),"frames":NS(**{**vars(env["native"].frames),"Frame":Frame})})

    checks=source;patcher=patch
    def execute(run):
        checks.require(type(run) is int and run==1 and state.attempts==0,
            "PARENT_CONNECTION_EXACT_RUN_NO_RETRY")
        state.attempts+=1
        old_binding=env["binding"];old_budget=env["runtime_budget"];json=env["json"];old_dump=json.dump
        def bootstrap(reader):
            checks.require(callable(reader.checkpoint),"PARENT_CONNECTION_ORIGINAL_METADATA_GUARD")
            state.metadata_guard=reader.checkpoint;state.bootstrap_calls+=1
            return old_binding(reader)
        def budget(required,requests):
            checks.require(callable(state.metadata_guard),"PARENT_CONNECTION_BOOTSTRAP_BEFORE_COST")
            state.budget_calls+=1
            return binding.runtime_budget(required,requests,old_budget,state.metadata_guard)
        def dump(row,stream,**kwargs):
            checks.require(type(row) is dict,"PARENT_CONNECTION_ORIGINAL_RUNTIME_ROW")
            state.dump_calls+=1
            frame=row.get("source_frame")
            if frame is not None:
                checks.require(len(state.frames)==1,"PARENT_CONNECTION_REAL_FRAME_BEFORE_ROW")
                actual=state.frames[0]
                checks.exact(frame,actual.summary(),"PARENT_CONNECTION_SAME_UNMODIFIED_FRAME_SUMMARY")
                row["source_input_representation"]=frame["explicit_source_input_representation"]
                row["aggregate_envelope_decoder"]=frame["aggregate_envelope_decoder"]
                row["parent_live_raw_access_policy"]=frame["parent_python_live_raw_access_policy"]
                if row.get("current_generation_runtime_candidate_qualified") is True:
                    binding.validate_scope_evidence(row,{n:dict(p) for n,p in actual.semantic_inputs.items()},
                        actual.checkpoint)
                    checks.require(actual.raw_policy.restored and not actual.raw_policy.installed,
                        "PARENT_CONNECTION_POLICY_RESTORED_BEFORE_CANDIDATE")
            return old_dump(row,stream,**kwargs)
        try:
            with patcher.dict(env,dict(binding=bootstrap,runtime_budget=budget,native=native)), \
                    patcher.object(json,"dump",dump):
                return original(run)
        finally:
            for frame in state.frames:frame.restore_policy()
    # Same private globals are necessary for the existing entry to supply its
    # complete binding before this wrapper runs. Do not clone a stale dictionary.
    connected=FunctionType(execute.__code__,env,argdefs=execute.__defaults__,closure=execute.__closure__)
    source.require(connected.__globals__ is env,"PARENT_CONNECTION_SAME_PRIVATE_BINDING_ENV")
    return NS(**{**vars(engine),"run_owned":connected}),state


def evidence(state):
    return dict(original_whole_engine_and_worker_functions_retained=True,
        same_private_binding_environment_retained=True,attempts=state.attempts,
        original_bootstrap_calls=state.bootstrap_calls,projected_budget_calls=state.budget_calls,
        serialized_runtime_rows=state.dump_calls,actual_frames=len(state.frames),
        original_GO_Job_byte_read_inventory_and_cleanup_bodies_not_replaced=True,
        bootstrap_original_scope_pins_not_removed=True,
        semantic_and_physical_accounting_explicit=True,
        original_metadata_guard_reused_not_new_sampler=True,
        full_current158_parent_worker_or_oracle_qualified=False,GO_authorized=False)
