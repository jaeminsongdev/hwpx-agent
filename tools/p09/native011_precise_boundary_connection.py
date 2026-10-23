"""One private Native BoundaryReader factory slot, original reader methods intact.

Construction installs no IO, clock, sampler, Frame, process or product. At each
of the original two boundary-factory calls only a fresh pacer may be connected.
"""
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native011_precise_boundary_connection.py'
TEST='tools/p09/tests/test_native011_precise_boundary_connection.py'


def require(ok,label):
    if not ok:raise ValueError('PRECISE_NATIVE_CONNECTION_'+label)


def connect(linked,precise,*,modules=None):
    require(linked.state.attempts==linked.state.calls==0,'BEFORE_ANY_WORKER_ATTEMPT')
    run=linked.engine.run_owned;require(type(run) is FunctionType,'ORIGINAL_ENGINE_FUNCTION')
    env=run.__globals__;modules=tuple(sys.modules.values()) if modules is None else tuple(modules)
    require(not any(getattr(module,'__dict__',None) is env for module in modules),'PRIVATE_NAMESPACE_NOT_DEFAULT_MODULE')
    original=env.get('BoundaryReader');pressure=env.get('byte_policy')
    require(type(original) is type and pressure is not None and hasattr(pressure,'OwnedPacer')
        and issubclass(original,pressure.WeightedReader),'ORIGINAL_BOUNDARY_READER_AND_BYTE_POLICY')
    saved=dict(env);methods={name:getattr(original,name) for name in ('__init__','_read','_bind','fresh_pin','finish','diagnostics')}
    state=NS(attempts=0,completed=0,failed=False,proofs=[])
    def factory(*args,**kwargs):
        require(not state.failed and state.attempts<2,'ORIGINAL_TWO_BOUNDARY_FACTORIES_NO_RETRY')
        state.attempts+=1
        try:
            reader=original(*args,**kwargs)
            require(type(reader) is original,'EXACT_ORIGINAL_BOUNDARY_READER_INSTANCE')
            proof=precise.connect(reader,pressure)
            require(all(getattr(original,name) is method for name,method in methods.items()),
                'ORIGINAL_READER_METHODS_NOT_REWRITTEN')
            state.proofs.append(proof);state.completed+=1;return reader
        except BaseException:state.failed=True;raise
    env['BoundaryReader']=factory
    require(set(env)==set(saved) and all(env[key] is value for key,value in saved.items() if key!='BoundaryReader')
        and linked.engine.run_owned is run and run.__globals__ is env,'ONLY_EXPLICIT_FACTORY_DEPENDENCY_SLOT')
    return NS(state=state,original_reader=original,factory=factory),dict(
        one_private_BoundaryReader_factory_dependency_connected=True,
        original_engine_and_reader_method_code_retained=True,default_modules_changed=False,
        original_two_byte_reads_and_pressure_checkpoints_retained=True,
        only_unused_original_pacer_clock_and_origin_change=True,
        factory_attempts_during_construction=state.attempts,actual_Frame_or_product_qualified=False)
