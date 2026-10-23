"""Preparation-only original full metadata audit with the owned allocator.

Only the reader allocation dependency changes. The complete pinned audit body,
callback, projection, helper reads, semantic hashes, JSON and finish are retained.
This is not the complete product input_pins, a Native epoch or a GO permission.
"""
import ast
import copy
import hashlib
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_engine_owned_metadata_callback.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_callback.py'
SOURCE=dict(path='tools/p09/native011_metadata_audit.py',bytes=10082,
    sha256='b52d887dbd4330ab39d4e4a6ea13f45868c3e9eda0c2db9b5cf086271f50c0bd')


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_CALLBACK_'+code)


def project(raw,original,engine_raw,connection):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'WHOLE_ORIGINAL_METADATA_SOURCE')
    engine=connection.ENGINE
    require(type(engine_raw) is bytes and len(engine_raw)==engine['bytes']
        and hashlib.sha256(engine_raw).hexdigest()==engine['sha256'],'WHOLE_ORIGINAL_ENGINE_SOURCE')
    tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='metadata']
    require(len(nodes)==1 and type(original) is FunctionType and original.__closure__ is None
        and original.__defaults__ is original.__kwdefaults__ is None,'ONE_ORIGINAL_METADATA_FUNCTION')
    forms=(compile(raw,SOURCE['path'],'exec'),compile(ast.fix_missing_locations(ast.Module(
        body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),SOURCE['path'],'exec'))
    require(any(original.__code__==code for form in forms for code in form.co_consts
        if type(code) is CodeType and code.co_name=='metadata'),'EXACT_ORIGINAL_METADATA_FUNCTION_CODE')
    before=copy.deepcopy(nodes[0]);changed=copy.deepcopy(before)
    expected=ast.parse('reader=build.BuildReader(root,epochs.check)').body[0];hits=[]
    for index,node in enumerate(changed.body):
        if ast.dump(node,include_attributes=False)==ast.dump(expected,include_attributes=False):
            changed.body[index]=ast.copy_location(ast.parse('reader=_owned_preparation_allocate(root,epochs,context)').body[0],node)
            hits.append(index)
    require(len(hits)==1,'ONE_ORIGINAL_METADATA_ALLOCATION_SITE')
    inverse=copy.deepcopy(changed);inverse.body[hits[0]]=copy.deepcopy(before.body[hits[0]])
    require(ast.dump(inverse,include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_ORIGINAL_CALLBACK_BODY_INVERSE')
    state=NS(attempts=0,completed=0,failed=False,prefix=None)
    def allocate(root,epochs,context):
        owner=context.data.planned.batch
        require(owner.phase=='READY' and owner.metadata_connection.readers==owner.metadata_connection.budgets==[]
            and owner.shared.metadata is owner.shared.frame is None,'ORIGINAL_UNUSED_FACTORY_AFTER_REAL_OPENING')
        run=context.prepared.linked.engine.run_owned
        reader,prefix=connection.allocate_original_prefix(engine_raw,run.__globals__['build'],root,epochs.check,
            run.__globals__['byte_policy'])
        state.prefix=prefix
        return reader
    env=dict(original.__globals__)
    require('_owned_preparation_allocate' not in env,'NO_DEPENDENCY_NAME_COLLISION')
    env['_owned_preparation_allocate']=allocate
    exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),SOURCE['path'],'exec'),env)
    selected=env['metadata']
    def callback(root,epochs,context,a):
        try:
            epochs.check()
            require(state.attempts==0 and not state.failed,'ONE_PREPARATION_CALLBACK_NO_RETRY')
            state.attempts+=1
            result=selected(root,epochs,context,a)
            require(state.prefix is not None,'ORIGINAL_TWO_STATEMENTS_EXECUTED')
            state.completed+=1
            return dict(result,original_owned_allocation_assignment_prefix=state.prefix,
                preparation_only_owned_allocation=True,complete_product_input_pins_qualified=False)
        except BaseException:state.failed=True;raise
    return NS(callback=callback,state=state),dict(whole_original_metadata_source=dict(SOURCE),
        whole_original_engine_source=dict(engine),entire_original_metadata_body_inverse=True,
        changed_allocation_dependency_sites=1,original_callback_projection_helpers_and_closing_retained=True,
        default_function_or_engine_modified=False,reader_or_budget_allocated_during_projection=False,
        original_engine_metadata_input_body_or_Native_or_worker_or_product_executed=False,
        shared_decoder_or_deadlines_or_resource_checks_modified=False,GO_authorized=False)
