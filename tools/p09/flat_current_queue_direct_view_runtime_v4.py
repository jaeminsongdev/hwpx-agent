"""Preserve v3 connection; load all exact metadata10 tests without CLI import.

No test omitted, helper hidden, source excluded, rate/deadline/guard relaxed.
v3's helper65 preflight remains FAILED. New DATA/preflight004 are independent.
"""
import argparse
import ast
import copy
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
from types import FunctionType, MappingProxyType, SimpleNamespace as NS
import unittest

import flat_preserved129_lean_connection_v2 as lean

base,source,a,c=lean.base,lean.source,lean.a,lean.c
SELF="tools/p09/flat_current_queue_direct_view_runtime_v4.py"
TEST="tools/p09/tests/test_flat_current_queue_direct_view_runtime_v4.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case134-direct-view-test-namespace-code-r372.v1.json"
CODE_PASS="PASS_EXACT_V3_CONNECTION12_METADATA10_AND_TEST_NAMESPACE5_NOT_ACTUAL134"
V3_PIN=dict(path="tools/p09/flat_current_queue_direct_view_runtime_v3.py",bytes=16455,
    sha256="78b95613180d78fb8be5ad21d28dc62b040bbc918701bb580d99778d9b1964f3")
METADATA_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_metadata_connection.py",bytes=4896,
    sha256="3d694c9497eb8354113a2df3969f218bd63fbc438144d64c29325d07ac324026")
FAILED003=dict(path="implementation/p09/evidence/p09-361-case134-direct-view-preflight003.v1.json",bytes=46830,
    sha256="75cf9d3a3650f91d2a10f18cde6ba21324b1809c6d77560483cc917a0705734b")
V3=API=PROOF=None


def require(ok,code):
    if not ok:raise ValueError("DIRECT_TEST_NAMESPACE_"+code)


def project_v3(raw):
    require(type(raw) is bytes and len(raw)==V3_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==V3_PIN['sha256'],'EXACT_V3_RAW')
    tree=ast.parse(raw.decode('utf-8'))
    def selected(n):
        return isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
            isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name)
            and n.value.func.value.id=='_env' and n.value.func.attr=='update')
    nodes=[copy.deepcopy(n) for n in tree.body if selected(n)]
    originals=[ast.dump(n,include_attributes=False) for n in tree.body
        if selected(n)]
    require(len([n for n in nodes if isinstance(n,ast.For)])==1,'ORIGINAL_ONE_FAMILY_INITIALIZATION_LOOP')
    require(len([n for n in nodes if isinstance(n,ast.Expr)])==1,'ORIGINAL_ONE_EXPLICIT_DEPENDENCY_INITIALIZATION')
    require([ast.dump(n,include_attributes=False) for n in nodes]==originals,'ALL_V3_DEFINITION_AND_INITIALIZATION_AST_UNCHANGED')
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,
        contextmanager=contextmanager,hashlib=hashlib,json=json,re=re,sys=sys,
        FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,
        __name__='p09_exact_v3_namespace',__file__=V3_PIN['path'])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),V3_PIN['path'],'exec'),env)
    return NS(**env),dict(all_original_v3_functions_constants_and_initialization_loop_AST_unchanged=True,
        full_v3_module_or_CLI_import_executed=False,imported_modules_hidden_or_removed=False,
        original_default_modules_mutated=False,helper_ceiling_raised=False)


def bootstrap():
    base.stable.stable.prior.build.direct_path(c.ROOT/V3_PIN['path'],file_required=True)
    with (c.ROOT/V3_PIN['path']).open('rb') as stream:raw=stream.read(V3_PIN['bytes']+1)
    return project_v3(raw)


def metadata_test_namespace(raw):
    require(type(raw) is bytes and len(raw)==METADATA_TEST_PIN['bytes']
        and hashlib.sha256(raw).hexdigest()==METADATA_TEST_PIN['sha256'],'EXACT_METADATA10_TEST_RAW')
    nodes=[n for n in ast.parse(raw.decode('utf-8')).body if isinstance(n,ast.ClassDef)]
    require(len(nodes)==1 and nodes[0].name=='ConnectionContracts','ONE_WHOLE_ORIGINAL_TEST_CLASS')
    node=copy.deepcopy(nodes[0])
    require(ast.dump(node,include_attributes=False)==ast.dump(nodes[0],include_attributes=False),'ALL_METADATA10_TEST_AST_UNCHANGED')
    require(len([n for n in node.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')])==10,'ALL10_TEST_METHODS')
    env=dict(ast=ast,copy=copy,Path=Path,sys=sys,threading=threading,NS=NS,unittest=unittest,
        r=source.prior.prior.metadata,accept=source.prior.accepted.prior.metadata,
        __name__='p09_exact_metadata10_namespace')
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),METADATA_TEST_PIN['path'],'exec'),env)
    return NS(**env)


def metadata_tests(q):
    pin,raw=q._read(METADATA_TEST_PIN['path'],parse=True);q._bind(pin['path'],pin)
    a.exact(pin,METADATA_TEST_PIN,'FRESH_WHOLE_ORIGINAL_METADATA10_TEST_SOURCE')
    return metadata_test_namespace(bytes(raw))


def data_path(index):
    require(type(index) is int and 134<=index<=249,'SUCCESSOR_RANGE')
    return f'implementation/p09/evidence/p09-361-case{index}-direct-view-connection-data004.v1.json'


def validate_data(row,step):
    require(type(row) is dict and set(row)=={'schema_version','index','before','run','base_step_pin',
        'prior_source_data_pin','original_base_runtime_pin','parent_qualification_pin','lean_qualification_pin',
        'connection_qualification_pin','connection_code_pins','prior_v3_data_pin','v3_namespace_pin',
        'metadata_test_pin','failed003_pin'},'CLOSED_V4_DATA')
    a.fields(row,dict(schema_version='hwpx-agent.p09-direct-held-view-test-namespace/v4',
        index=step.index,before=step.before,run=1,base_step_pin=step.pin,
        original_base_runtime_pin=V3.OLD.PRISTINE.BASE_PIN,parent_qualification_pin=V3.OLD.PRISTINE.PARENT_QUAL,
        lean_qualification_pin=V3.OLD.PRISTINE.LEAN_QUAL,v3_namespace_pin=V3_PIN,
        metadata_test_pin=METADATA_TEST_PIN,failed003_pin=FAILED003),'EXACT_V4_LINEAGE')
    require(set(base.scope.pins(row['connection_code_pins'],2))=={SELF,TEST},'ALL_V4_CODE2')
    a.exact(row['connection_qualification_pin']['path'],QUAL_PATH,'V4_QUAL_PATH')
    a.exact(row['prior_v3_data_pin']['path'],V3.data_path(step.index),'V3_DATA_PATH')
    a.exact(row['prior_source_data_pin']['path'],source.data_path(step.index),'ORIGINAL_SOURCE_DATA_PATH')
    return row


def own_inputs(q):
    text=q.text(data_path(base.CONFIG.index));require(0<len(text.encode())<=16384,'BOUNDED_V4_DATA')
    row=validate_data(json.loads(text,object_pairs_hook=base.unique),base.CONFIG)
    pin,raw=q._read(V3_PIN['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,V3_PIN,'FRESH_V3_CODE')
    fresh,_=project_v3(bytes(raw))
    a.exact(fresh.template.__code__==V3.template.__code__,True,'FRESH_SAME_QUALIFIED_V3_TEMPLATE')
    V3.own_inputs(q)
    a.exact(q.snapshots[V3.data_path(base.CONFIG.index)],row['prior_v3_data_pin'],'WHOLE_ORIGINAL_DATA003')
    a.exact(q.pin(source.data_path(base.CONFIG.index)),row['prior_source_data_pin'],'ORIGINAL_SOURCE_DATA')
    a.exact(q.pin(METADATA_TEST_PIN['path']),METADATA_TEST_PIN,'UNCHANGED_ORIGINAL_TEST10')
    failed=a.read_exact(q,FAILED003)
    a.fields(failed,dict(state='FAILED_NOT_ACCEPTED',error_code='METADATA_CONNECTION_ORIGINAL_HELPER_BOUND',
        product_worker_or_Native_frame_executed=False,accepted_count_delta=0,cleanup_confirmed=True),'FAILED003_NEVER_PROMOTED')
    code=a.read_exact(q,row['connection_qualification_pin'])
    a.fields(code,dict(state=CODE_PASS,contracts=dict(run=27,errors=0,failures=0,skipped=0),
        original_connection12_retained=True,original_metadata10_tests_retained=True,
        original_whole_previous133_oracle_checked=True,accepted_count_after=127,
        accepted_count_delta=0,actual134_product_or_Native_executed=False,cleanup_confirmed=True),'REAL_CODE27')
    a.exact(code['new_code_pins'],row['connection_code_pins'],'TESTED_CURRENT_V4_CODE')
    for p in row['connection_code_pins']:
        a.exact(q.pin(p['path']),p,'CURRENT_V4_CODE')
        archive='implementation/p09/evidence/p361-case134-direct-view-test-namespace-qualified-code/'+p['path']
        a.exact(q.pin(archive),dict(p,path=archive),'EXACT_V4_ARCHIVES')
    return row


def context(step):return NS(**{**vars(V3.context(step)),'SELF':SELF,'TEST':TEST})


def validator(raw,ctx,flat=True):
    project,proof=V3.validator(raw,ctx,flat)
    project.__globals__['CONTROLLERS']=tuple(dict.fromkeys(project.__globals__['CONTROLLERS']+(SELF,TEST)))
    return project,dict(proof,exact_v4_controller_pins_inside_whole_scope=True)


def template():
    engine,proof=V3.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,original_v3_engine_code_and_backend_unchanged=True)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=133:return V3.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    original=V3.OLD.API.previous_validation
    return FunctionType(original.__code__,dict(original.__globals__,source=V3.CONNECTED_SOURCE,
        validator=validator,context=context),argdefs=original.__defaults__)(q,row,listing,oldbody,fresh,oldctx,flat)


def binding(q):
    pin,raw=q._read(V3.OLD.API.BASE_PIN['path'],parse=True);q._bind(pin['path'],pin)
    a.exact(pin,V3.OLD.API.BASE_PIN,'ORIGINAL_BINDING_SOURCE')
    fn,_=V3.OLD.API.binding_projection(bytes(raw),replacement=previous_validation)
    return fn(q)


def preflight_projection(raw,leaf):
    old=V3.preflight_projection(raw,leaf)  # All original raw pins/factories first.
    node=copy.deepcopy(next(n for n in ast.parse(raw.decode('utf-8')).body
        if isinstance(n,ast.FunctionDef) and n.name=='preflight'))
    before=ast.dump(node,include_attributes=False);changes=[]
    class Project(ast.NodeTransformer):
        def visit_Import(self,n):
            if len(n.names)==1 and n.names[0].name=='test_flat_current_queue_metadata_connection' and n.names[0].asname=='tests':
                new=ast.parse('tests=metadata_tests(q)').body[0];new._old=copy.deepcopy(n);changes.append('whole_test10_namespace');return new
            return n
        def visit_Constant(self,n):
            if n.value=='-metadata-preflight001.v1.json':
                new=ast.Constant('-direct-view-preflight004.v1.json');new._old=copy.deepcopy(n);changes.append('new004_destination');return new
            return n
    node=Project().visit(node)
    require(sorted(changes)==['new004_destination','whole_test10_namespace'],'ONLY_TWO_PREFLIGHT_AST_DEPENDENCIES')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_old'):return copy.deepcopy(n._old)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_ORIGINAL_PREFLIGHT_TESTS_SCOPE_GUARDS_AND_STATEMENTS_RESTORED')
    env=dict(old.__globals__,SELF=SELF,TEST=TEST,template=template,binding_attempt=API.binding_attempt,
        data_path=data_path,connection_data=lambda q:own_inputs(q),metadata_tests=metadata_tests)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
        source.prior.prior.prior.METADATA_PIN['path'],'exec'),env)
    return env['preflight']


def preflight():
    return FunctionType(V3.OLD.API.preflight.__code__,dict(V3.OLD.API.preflight.__globals__,
        preflight_projection=preflight_projection),argdefs=V3.OLD.API.preflight.__defaults__)()


V3,PROOF=bootstrap()
_family=V3.API.prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,
    own_inputs=own_inputs,validate_data=validate_data,data_path=data_path,validator=validator,
    template=template,context=context,binding=binding,previous_validation=previous_validation)
API=NS(**_env)

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:
            base.configure(base.task_index(sys.argv[3]));raise SystemExit(API.worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument('--case',type=int,required=True)
        parser.add_argument('--run',type=int);parser.add_argument('--preflight',action='store_true')
        parser.add_argument('--accept',action='store_true');parser.add_argument('--root-bytes',type=int);parser.add_argument('--root-sha256')
        args=parser.parse_args();data_path(args.case);base.configure(args.case)
        require(sum((args.run is not None,args.preflight,args.accept))==1,'ONE_MODE')
        if args.accept:
            pin=dict(path=source.root_path(base.CONFIG),bytes=args.root_bytes,sha256=args.root_sha256)
            base.scope.pins([pin],1);raise SystemExit(API.accept(pin))
        require(args.root_bytes is None and args.root_sha256 is None,'ACCEPT_ARGUMENTS_ONLY')
        raise SystemExit(preflight() if args.preflight else API.run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        code=str(e) if isinstance(e,ValueError) else 'REDACTED_DIRECT_TEST_CONNECTION_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if re.fullmatch('[A-Z0-9_]{1,256}',code)
            else 'REDACTED_DIRECT_TEST_CONNECTION_FAILURE')));raise SystemExit(2) from None
