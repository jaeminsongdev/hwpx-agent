"""Require a real FINAL same-owner resource sample after Native closing.

Fast identity/close can finish before0.5s cadence; do not make missing samples
zero or shorten the cadence. Charge at most0.5s explicit nominal wait, use the
existing post_guard before/after wait, and preserve every deadline/decision.
"""
import ast
import copy
import hashlib
import math
import time

import postcleanup_sampler_handoff as h

SELF='tools/p09/postcleanup_final_sample.py'
WAIT_ALLOWANCE=.5


def require(ok,code):
    if not ok:raise ValueError('POSTCLEANUP_FINAL_'+code)


def sample(guard,last_time,count,*,clock=time.monotonic,sleeper=time.sleep):
    require(callable(guard) and callable(last_time) and callable(count),'ORIGINAL_POST_GUARD_CALLBACKS')
    before=count();require(type(before) is int and before>=0,'ACTUAL_SAMPLE_COUNT')
    guard()  # original hard deadlines/decisions, not a new observer
    after=count();require(type(after) is int and after>=before,'MONOTONIC_SAMPLE_COUNT')
    if after==before:
        stamp=last_time();now=clock()
        require(type(stamp) in (int,float) and type(now) in (int,float)
            and math.isfinite(stamp) and math.isfinite(now) and 0<=stamp<=now,'REAL_SAME_OWNER_CLOCK')
        wait=WAIT_ALLOWANCE-(now-stamp)
        require(0<wait<=WAIT_ALLOWANCE,'NO_SUPPRESSED_DUE_SAMPLE')
        sleeper(wait)
        guard()  # the SAME callback checks deadline then obtains fresh CPU/RAM
    require(type(count()) is int and count()>before,'REAL_FINAL_SAMPLE_REQUIRED')


def project(raw,original_engine,seeded_engine,index,before):
    # Requalify the entire pre-existing timestamp-only engine's code footprint.
    fixed,handoff_proof=h.project(raw,original_engine,index,before)
    require(h.footprint(fixed.__code__)==h.footprint(seeded_engine.__code__),'EXACT_TIMESTAMP_ENGINE_BASELINE')
    pin=h.TEMPLATE_PIN
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_ORIGINAL_BYTES')
    node=copy.deepcopy(next(n for n in ast.parse(raw.decode('utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='run_owned'))
    counts=dict(index=0,before=0,path=0,schema=0)
    class Metadata(ast.NodeTransformer):
        def visit_Constant(self,n):
            if type(n.value) is int and n.value==112:n.value=index;counts['index']+=1
            elif type(n.value) is int and n.value==105:n.value=before;counts['before']+=1
            elif n.value=='implementation/p09/evidence/p09-361-case112-current-runtime-run':
                n.value=f'implementation/p09/evidence/p09-361-case{index}-current-runtime-run';counts['path']+=1
            elif n.value=='hwpx-agent.p09-case112-current-native-runtime-candidate/v1':
                n.value='hwpx-agent.p09-current-queue-native-runtime-candidate/v1';counts['schema']+=1
            return n
    node=Metadata().visit(node)
    require(counts==dict(index=3,before=1,path=1,schema=1),'CLOSED_METADATA')
    marker=ast.dump(ast.parse('owner.checkpoint_io=post_guard').body[0],include_attributes=False)
    seeds=0
    class Seed(ast.NodeTransformer):
        def visit_Assign(self,n):
            nonlocal seeds
            if ast.dump(n,include_attributes=False)==marker:
                seeds+=1;return [ast.parse('post_time=handoff_timestamp(last_parent)').body[0],n]
            return self.generic_visit(n)
    node=Seed().visit(node);require(seeds==1,'ONE_ORIGINAL_TIMESTAMP_SEED')
    namespace=dict(fixed.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),pin['path'],'exec'),namespace)
    require(h.footprint(namespace['run_owned'].__code__)==h.footprint(fixed.__code__),'ALL_BASELINE_GUARDS_CODE_EXACT')
    baseline=ast.dump(node,include_attributes=False)
    marker=ast.dump(ast.parse('final_frame=frame.commit(row)').body[0],include_attributes=False)
    inserts=0
    class Final(ast.NodeTransformer):
        def visit_Assign(self,n):
            nonlocal inserts
            if ast.dump(n,include_attributes=False)==marker:
                extra=ast.parse('final_resource_sample(post_guard, lambda: post_time, lambda: len(post_samples))').body[0]
                extra._final_resource_requirement=True;inserts+=1;return [n,extra]
            return self.generic_visit(n)
    node=Final().visit(node);require(inserts==1,'ONE_AFTER_COMMIT_BEFORE_ACCEPT')
    class Undo(ast.NodeTransformer):
        def visit_Expr(self,n):
            if hasattr(n,'_final_resource_requirement'):return None
            return self.generic_visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==baseline,'ALL_PREEXISTING_ENGINE_STATEMENTS_RETAINED')
    namespace=dict(fixed.__globals__);namespace['final_resource_sample']=sample
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),pin['path'],'exec'),namespace)
    return namespace['run_owned'],dict(timestamp_handoff=handoff_proof,
        preexisting_engine_code_exact=True,all_preexisting_engine_AST_restored_exactly=True,
        final_original_guard_requirement_added_once=True,maximum_nominal_distinct_sample_wait_seconds=.5,
        new_observer_or_thread_or_zero_CPU_fabricated=False,original_deadlines_and_cadence_relaxed=False)
