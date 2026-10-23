"""One metadata selector in the original common Native preparation validator.

The complete validator and common entry bodies stay intact. Only the original
metadata factory call selects the already-qualified owned-assignment adapter.
No reader, Native Frame, worker, GO or product runs during this projection.
"""
import ast
import copy
import hashlib
from types import CodeType, FunctionType

SELF='tools/p09/native011_engine_owned_metadata_validation.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_validation.py'
SOURCE=dict(path='tools/p09/native011_ready_native_construction.py',bytes=12961,
    sha256='13d075acad8a5c6d388611d83e87fcfca9f32236064d0eb34a55affa44411b2a')
OWNED='tools/p09/native011_engine_owned_metadata_connection.py'
ADOPTION='tools/p09/native011_engine_owned_metadata_adoption.py'


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_VALIDATION_'+code)


def checked(raw,original,name):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'WHOLE_ORIGINAL_COMMON_PREPARATION_SOURCE')
    require(type(original) is FunctionType and original.__closure__ is None,'EXACT_ORIGINAL_COMMON_FUNCTION_CODE')
    tree=ast.parse(raw)
    def matches(form):
        return any(original.__code__==code for code in form.co_consts if type(code) is CodeType and code.co_name==name)
    matched=matches(compile(raw,SOURCE['path'],'exec'))
    if not matched:
        # Same disjunction as before, evaluated lazily within this fresh call.
        # No source/AST/code-image cache or earlier validation credit is kept.
        matched=matches(compile(ast.fix_missing_locations(ast.Module(
            body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),SOURCE['path'],'exec'))
    require(matched,'EXACT_ORIGINAL_COMMON_FUNCTION_CODE')
    return tree


def select(owned,adoption,connection,linked,owner,pins,candidate,exact,pressure,chunk,raw,metadata_raw,build_raw,codes):
    return owned.connect(linked,owner,pins,connection,candidate,adoption,exact,pressure,chunk,raw,metadata_raw,build_raw,codes)


def project(raw,original):
    tree=checked(raw,original,'validate')
    require(original.__defaults__ is None and original.__kwdefaults__==dict(exact_owner=None),
        'ORIGINAL_VALIDATOR_CALL_DEFAULTS')
    before=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
    hits=[]
    class Replace(ast.NodeTransformer):
        def visit_Call(self,item):
            if (isinstance(item.func,ast.Attribute) and isinstance(item.func.value,ast.Name)
                and item.func.value.id=='metadata_connection' and item.func.attr=='connect'):
                require(not item.keywords and len(item.args)==11,'ORIGINAL_METADATA_FACTORY_ARGUMENTS')
                changed=copy.deepcopy(item);changed.func=ast.Name(id='_select_engine_owned_metadata',ctx=ast.Load())
                changed.args=[ast.parse('private_source('+repr(name)+')',mode='eval').body for name in (OWNED,ADOPTION)]
                changed.args+=[ast.Name(id='metadata_connection',ctx=ast.Load())]+copy.deepcopy(item.args)
                changed._engine_owned_before=copy.deepcopy(item);hits.append(1);return ast.copy_location(changed,item)
            return self.generic_visit(item)
    selected=Replace().visit(copy.deepcopy(before));require(len(hits)==1,'ONE_ORIGINAL_METADATA_SELECTOR_SITE')
    class Undo(ast.NodeTransformer):
        def visit(self,item):
            if hasattr(item,'_engine_owned_before'):return copy.deepcopy(item._engine_owned_before)
            return super().visit(item)
    require(ast.dump(Undo().visit(copy.deepcopy(selected)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_ORIGINAL_VALIDATOR_BODY_INVERSE')
    env=dict(original.__globals__)
    require('_select_engine_owned_metadata' not in env,'NO_PRIVATE_DEPENDENCY_COLLISION')
    env['_select_engine_owned_metadata']=select
    exec(compile(ast.fix_missing_locations(ast.Module(body=[selected],type_ignores=[])),SOURCE['path'],'exec'),env)
    return env['validate'],dict(whole_original_common_source=dict(SOURCE),entire_original_validator_AST_inverse=True,
        metadata_selector_sites=1,owned_dependencies_loaded_by_original_fresh_private_source_reader=True,
        original_engine_checker_complete_budget_source201_shared5_and_guards_retained=True,
        original_unused_factory_1_2_MiB_assignment_selector_connected=True,
        original_modules_or_entry_body_mutated=False,reader_or_budget_or_Frame_or_worker_created=False,
        Native_or_product_or_GO_authorized=False)


def bind_entry(raw,original,validator):
    checked(raw,original,'main')
    require(original.__defaults__ is None and original.__kwdefaults__==dict(driver=None)
        and type(validator) is FunctionType and validator.__name__=='validate',
        'ORIGINAL_ENTRY_DEFAULTS_AND_EXPLICIT_VALIDATOR')
    before=original.__globals__;env=dict(before,validate=validator)
    require(set(env)==set(before) and all(env[n] is v for n,v in before.items() if n!='validate'),
        'ONE_PRIVATE_VALIDATOR_DEPENDENCY_SLOT')
    selected=FunctionType(original.__code__,env,name=original.__name__,argdefs=original.__defaults__,closure=original.__closure__)
    selected.__kwdefaults__=dict(original.__kwdefaults__)
    return selected,dict(original_common_entry_code_defaults_and_closure_retained=True,
        only_validator_dependency_changed=True,original_default_namespace_mutated=False,
        actual_common_entry_or_Native_or_product_executed=False,GO_authorized=False)
