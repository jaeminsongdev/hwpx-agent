"""Seed post-Job cadence from the SAME observer's last successful sample.

No missing sample becomes zero, no retry/sleep/new query/thread, no relaxed
CPU/RAM/600/720/1200 guard. One explicit timestamp assignment is inserted;
undo must restore the exact already-qualified engine AST/code footprint.
"""
import ast
import copy
import hashlib
import math
import time
from types import CodeType

SELF='tools/p09/postcleanup_sampler_handoff.py'
TEST='tools/p09/tests/test_postcleanup_sampler_handoff.py'
TEMPLATE_PIN=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')


def require(ok,code):
    if not ok:raise ValueError('POSTCLEANUP_HANDOFF_'+code)


def timestamp(last_parent,clock=time.monotonic):
    require(type(last_parent) is tuple and len(last_parent)==2,'LAST_SUCCESSFUL_SAMPLE_REQUIRED')
    tick,cpu=last_parent;now=clock()
    require(type(tick) in (int,float) and type(cpu) in (int,float) and type(now) in (int,float)
        and all(math.isfinite(x) for x in (tick,cpu,now)) and 0<=tick<=now and cpu>=0,'VALID_ORIGINAL_SAMPLE_CLOCK')
    return tick


def footprint(code):
    require(isinstance(code,CodeType),'CODE_OBJECT')
    return (code.co_code,tuple(footprint(x) if isinstance(x,CodeType) else x for x in code.co_consts),
        code.co_names,code.co_varnames,code.co_freevars,code.co_cellvars,code.co_argcount,
        code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,code.co_exceptiontable)


def project(raw,engine,index,before):
    require(type(raw) is bytes and len(raw)==TEMPLATE_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==TEMPLATE_PIN['sha256'],'EXACT_ORIGINAL_TEMPLATE')
    require(type(index) is int and type(before) is int and 114<=index<=249 and before<index,'EXPLICIT_METADATA')
    tree=ast.parse(raw.decode('utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_owned']
    require(len(nodes)==1,'ONE_ORIGINAL_ENGINE')
    node=copy.deepcopy(nodes[0]);counts=dict(index=0,before=0,path=0,schema=0)
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
    require(counts==dict(index=3,before=1,path=1,schema=1),'CLOSED_ALREADY_QUALIFIED_METADATA')
    namespace=dict(engine.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),TEMPLATE_PIN['path'],'exec'),namespace)
    require(footprint(namespace['run_owned'].__code__)==footprint(engine.__code__),'EXACT_BASELINE_ENGINE_CODE')
    baseline=ast.dump(node,include_attributes=False);inserted=0
    marker=ast.dump(ast.parse('owner.checkpoint_io=post_guard').body[0],include_attributes=False)
    class Seed(ast.NodeTransformer):
        def visit_Assign(self,n):
            nonlocal inserted
            if ast.dump(n,include_attributes=False)==marker:
                extra=ast.parse('post_time=handoff_timestamp(last_parent)').body[0]
                extra._handoff_timestamp_assignment=True;inserted+=1
                return [extra,n]
            return self.generic_visit(n)
    node=Seed().visit(node);require(inserted==1,'ONE_POST_JOB_HANDOFF_ONLY')
    class Undo(ast.NodeTransformer):
        def visit_Assign(self,n):
            if hasattr(n,'_handoff_timestamp_assignment'):return None
            return self.generic_visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==baseline,'ALL_ORIGINAL_GUARDS_AND_DECISIONS_RETAINED')
    namespace=dict(engine.__globals__);namespace['handoff_timestamp']=timestamp
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),TEMPLATE_PIN['path'],'exec'),namespace)
    return namespace['run_owned'],dict(exact_original_engine_code_verified_before_change=True,
        engine_AST_restored_exactly=True,added_timestamp_assignments=1,
        previous_valid_sample_or_0_percent_fabricated=False,original_sample_interval_seconds=.5,
        CPU_RAM_native_deadlines_extended=False,extra_sampler_query_thread_or_process=False,
        missing_interval_errors_suppressed=False,actual114_body_replay_authorized=False)
