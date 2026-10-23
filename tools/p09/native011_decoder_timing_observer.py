"""Diagnostic timing alongside, never instead of, the original decoder clock.

The original budget/check/run bodies, five-second limit and sticky failures
remain authoritative. No product connection, clock replacement or time credit.
"""
import math
import time
import hashlib
import ast
from types import FunctionType, SimpleNamespace as NS
import runtime_envelope_physical_io_v1 as original

SELF='tools/p09/native011_decoder_timing_observer.py'
TEST='tools/p09/tests/test_native011_decoder_timing_observer.py'
SHARED=dict(path='tools/p09/shared_metadata_frame_decoder_budget_v1.py',bytes=7823,
    sha256='fb9440e5c89ad684fda6d076a57a940fb2f44114c26d88051d272a4a60a609f6')
BUDGET=dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,
    sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c')


def require(ok,label):
    if not ok:raise ValueError('DECODER_TIMING_OBSERVER_'+label)


def attach(budget,*,wall=time.perf_counter,cpu=time.process_time):
    require(type(budget) is original.DecoderBudget and budget.elapsed==0
        and budget.attempts==budget.completed==0 and budget.active is None
        and budget.error is None and 'run' not in vars(budget),'FRESH_ORIGINAL_BUDGET_ONLY')
    require(callable(wall) and callable(cpu),'OBSERVATION_CLOCKS')
    run=budget.run;clock=budget.clock;check=budget.check
    state=NS(attempts=0,completed=0,failed=False,rows=[])

    def stamp():
        pair=(wall(),cpu())
        require(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in pair),
            'FINITE_NONNEGATIVE_OBSERVATION')
        return pair

    def selected(operation):
        require(not state.failed and state.attempts<649,'NO_FAILED_RETRY_OR_UNBOUNDED_LOG')
        try:
            require(budget.clock is clock and budget.check==check,'ORIGINAL_CLOCK_AND_CHECK_UNCHANGED')
            begin=stamp()
        except BaseException:
            state.failed=True;raise
        before=budget.elapsed;state.attempts+=1;error=None
        try:
            value=run(operation)
        except BaseException as caught:
            state.failed=True;error=caught
        finally:
            # An observation error must never replace an original guard error.
            try:
                end=stamp()
                require(all(after>=old for after,old in zip(end,begin)), 'MONOTONIC_OBSERVATIONS')
                state.rows.append(dict(original_elapsed_delta=budget.elapsed-before,
                    observed_wall_seconds=end[0]-begin[0],observed_CPU_seconds=end[1]-begin[1],
                    original_call_failed=error is not None))
            except BaseException:
                state.failed=True
                if error is None:raise
        if error is not None:raise error
        state.completed+=1;return value

    budget.run=selected

    def evidence():
        require(budget.active is None and budget.run is selected,'TERMINAL_ORIGINAL_OWNER')
        return dict(attempts=state.attempts,completed=state.completed,failed=state.failed,
            original_budget=budget.evidence(),rows=list(state.rows),
            observed_wall_total=sum(r['observed_wall_seconds'] for r in state.rows),
            observed_CPU_total=sum(r['observed_CPU_seconds'] for r in state.rows),
            original_clock_resolution=time.get_clock_info('monotonic').resolution,
            observation_clock_resolution=time.get_clock_info('perf_counter').resolution,
            original_clock_check_run_body_and_limit_unchanged=True,
            observation_not_used_for_admission_or_budget=True,product_or_full_Native_qualified=False)
    return NS(state=state,evidence=evidence,original_run=run)


def connect_shared(shared,raw,budget_raw):
    """Observe the actual fresh budgets after their unchanged shared attach.

    Compile the exact shared source before Native; no reader, IO or budget is
    constructed. The shared source, private budget class and default modules
    stay unchanged. This hook is for the closed readonly diagnostic only.
    """
    require(type(raw) is bytes and len(raw)==SHARED['bytes']
        and hashlib.sha256(raw).hexdigest()==SHARED['sha256'],'EXACT_SHARED_SOURCE')
    require(type(budget_raw) is bytes and len(budget_raw)==BUDGET['bytes']
        and hashlib.sha256(budget_raw).hexdigest()==BUDGET['sha256'],'EXACT_BUDGET_SOURCE')
    env=dict(__name__='p09_observed_exact_shared_source',__file__=SHARED['path'])
    exec(compile(raw,SHARED['path'],'exec'),env)
    expected=env['SharedBudget'];actual=type(shared)
    require(set(vars(actual))==set(vars(expected)),'EXACT_SHARED_CLASS_LAYOUT')
    def private_class(data,pin,namespace,name):
        # Exact original namespace-loader compiler context: imports are
        # dependency slots, all other AST nodes remain in their original order.
        tree=ast.parse(data.decode('utf-8'))
        nodes=[node for node in tree.body if not isinstance(node,(ast.Import,ast.ImportFrom))]
        selected=dict(namespace,__name__='p09_observed_exact_private_source')
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),pin['path'],'exec'),selected)
        return selected[name]
    private_shared=private_class(raw,SHARED,env,'SharedBudget')
    private_budget=private_class(budget_raw,BUDGET,vars(original),'DecoderBudget')
    def matches(cls,reference):
        return set(vars(cls))==set(vars(reference)) and all(type(vars(cls)[name]) is FunctionType
            and vars(cls)[name].__code__==method.__code__ for name,method in vars(reference).items()
            if type(method) is FunctionType)
    require(any(matches(actual,variant) for variant in (expected,private_shared)),
        'ONE_COMPLETE_EXACT_ORIGINAL_SHARED_COMPILE_FORM')
    require(actual.check.__globals__['LIMIT_SECONDS']==5.
        and actual.check.__globals__['require'].__code__==env['require'].__code__,'ORIGINAL_SHARED_LIMIT_AND_REJECTIONS')
    require(shared.metadata is shared.frame is shared.error is None and not shared.restored
        and shared.original_checks=={} and shared.checks==0 and 'attach' not in vars(shared),
        'UNUSED_SHARED_OWNER_ONLY')
    previous=shared.attach;state=NS(attempts=0,completed=0,failed=False,observers={})

    def selected(role,budget):
        try:
            require(not state.failed and state.attempts<2
                and role==('metadata' if state.attempts==0 else 'frame'),'EXACT_METADATA_THEN_FRAME_NO_RETRY')
            state.attempts+=1
            cls=type(budget)
            require(cls.__bases__==(object,) and set(vars(cls))==set(vars(original.DecoderBudget)),
                'EXACT_PRIVATE_BUDGET_CLASS_LAYOUT')
            require(any(matches(cls,variant) for variant in (original.DecoderBudget,private_budget)),
                'ONE_COMPLETE_EXACT_ORIGINAL_PRIVATE_BUDGET_COMPILE_FORM')
            require(cls.check.__globals__['DECODE_SECONDS']==5.
                and cls.check.__globals__['require'].__code__==original.require.__code__,
                'ORIGINAL_PRIVATE_BUDGET_LIMIT_AND_REJECTIONS')
            require(previous(role,budget) is budget,'ORIGINAL_SHARED_ATTACH_RESULT')
            observed=FunctionType(attach.__code__,dict(attach.__globals__,original=NS(DecoderBudget=cls)),
                argdefs=attach.__defaults__,closure=attach.__closure__)
            observed.__kwdefaults__=attach.__kwdefaults__
            state.observers[role]=observed(budget);state.completed+=1
            return budget
        except BaseException:
            state.failed=True;raise
    shared.attach=selected

    def evidence():
        return dict(attempts=state.attempts,completed=state.completed,failed=state.failed,
            roles={role:observer.evidence() for role,observer in state.observers.items()},
            original_shared=shared.evidence(),original_shared_and_budget_method_bodies_retained=True,
            private_class_dependency_only=True,default_module_changed=False,
            installed_in_product=False,actual_Native_or_product_qualified=False)
    return NS(state=state,evidence=evidence),dict(shared_source_pin=dict(SHARED),
        budget_source_pin=dict(BUDGET),exact_whole_source_or_original_import_slot_compilation_only=True,
        exact_original_shared_class_and_method_bodies=True,private_budget_verified_on_actual_attach=True,
        original_shared_attach_called_before_observer=True,budgets_constructed_during_connection=0,
        original_clock_limit_counters_checks_and_sticky_errors_retained=True,
        installed_in_product=False,actual_Native_or_product_qualified=False)
