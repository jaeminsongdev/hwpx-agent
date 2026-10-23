"""Explicit authority dependency in a fresh original product-parent instance.

The default CLI only constructs a permanently denied route. A caller supplying
a dependency must separately hold external execution authority; this module
does not grant it or execute a Native/product/GO/intent operation.
"""
import ast
import copy
import hashlib
from pathlib import Path
import re
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_product_authority_connection.py'
TEST='tools/p09/tests/test_native011_product_authority_connection.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-product-authority-construct002.v1.json'
SOURCE=dict(path='tools/p09/native011_product_parent_handoff.py',bytes=17663,
    sha256='9b72f412a29cbe4c374ece3ffa84e810d27ecbbb1b21552933d531ea997ba4e8')
CONNECTION=dict(path='tools/p09/native011_full_frame_worker_connection.py',bytes=21292,
    sha256='db312476f2e8515abcda357214f9f6494a074bd1a243642f9424302c3dd4ff19')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_AUTHORITY_CONNECTION_'+code)


def exact(raw,pin):
    require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
        'EXACT_ORIGINAL_SOURCE');return raw


def attest(raw,pin,function):
    exact(raw,pin);require(type(function) is FunctionType,'ORIGINAL_FUNCTION')
    filename=function.__code__.co_filename
    require(filename.replace('\\','/').endswith(pin['path']),'EXPECTED_FUNCTION_SOURCE')
    tree=ast.parse(raw)
    def matches(code):
        found=[value for value in code.co_consts if type(value) is CodeType and value.co_name==function.__name__]
        return len(found)==1 and found[0]==function.__code__
    matched=matches(compile(raw,filename,'exec'))
    if not matched:
        matched=matches(compile(ast.fix_missing_locations(ast.Module(body=[node for node in tree.body
            if not isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[])),filename,'exec'))
    require(matched,'ENTIRE_ORIGINAL_DRIVER_FUNCTION_CODE')
    return tree


def project(raw,parent,*,authorize=None):
    require(authorize is None or callable(authorize),'EXPLICIT_EXTERNAL_DEPENDENCY_NOT_APPROVAL_FLAG')
    tree=attest(raw,SOURCE,parent.driver_type)
    require('_external_authorize' not in parent.driver_type.__globals__,'UNUSED_PRIVATE_AUTHORITY_SLOT')
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='driver_type']
    require(len(nodes)==1,'ONE_WHOLE_DRIVER_DEFINITION');before=nodes[0];selected=copy.deepcopy(before)
    count=dict(install=0,evidence=0)
    evidence=ast.dump(ast.parse("proof['authorization_dependency_present'] is False",mode='eval').body,include_attributes=False)
    class Select(ast.NodeTransformer):
        def visit_Call(self,node):
            node=self.generic_visit(node)
            if isinstance(node.func,ast.Name) and node.func.id=='install':
                require(not node.keywords,'ORIGINAL_INSTALL_HAS_NO_AUTHORITY_DEPENDENCY')
                revised=copy.deepcopy(node);revised.keywords.append(ast.keyword(arg='authorize',value=ast.Name(id='_external_authorize',ctx=ast.Load())))
                revised._authority_before=copy.deepcopy(node);count['install']+=1;return revised
            return node
        def visit_Compare(self,node):
            if ast.dump(node,include_attributes=False)==evidence:
                revised=copy.deepcopy(node)
                revised.comparators=[ast.parse('_external_authorize is not None',mode='eval').body]
                revised._authority_before=copy.deepcopy(node);count['evidence']+=1;return revised
            return self.generic_visit(node)
    selected=Select().visit(selected)
    require(count==dict(install=1,evidence=1),'EXACT_TWO_AUTHORITY_CONNECTION_SITES')
    class Undo(ast.NodeTransformer):
        def visit(self,node):
            if hasattr(node,'_authority_before'):return copy.deepcopy(node._authority_before)
            return super().visit(node)
    require(ast.dump(Undo().visit(copy.deepcopy(selected)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_ORIGINAL_DRIVER_AST_INVERSE')
    env=dict(parent.driver_type.__globals__,_external_authorize=authorize)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[selected],type_ignores=[])),
        parent.driver_type.__code__.co_filename,'exec'),env)
    return env['driver_type'],dict(entire_original_driver_AST_inverse=True,exact_changed_sites=count,
        original_install_and_execute_Job_Frame_READY15_window10_code_retained=True,
        default_None_instance_permanently_denied=True,dependency_called_during_projection=False,
        external_authority_supplied=authorize is not None,GO_authorized=False,
        product_or_Native_or_intent_executed=False)


def driver_type(base,projection,*,authorize=None):
    """Name two new inputs before construction; verify them freshly afterwards."""
    require(projection['external_authority_supplied'] is (authorize is not None),'SAME_EXPLICIT_AUTHORITY_DEPENDENCY')
    class Driver(base):
        def __init__(self):super().__init__();self.output=OUTPUT;self.authority_declared=False
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);before=control.admit
            def declared(*args,**kwargs):
                require(not self.authority_declared,'ONE_EXPLICIT_AUTHORITY_CONTROL_DECLARATION')
                value=before(*args,**kwargs);self.authority_declared=True
                require(len(value.control_names)==70 and not {SELF,TEST}&set(value.control_names),
                    'EXACT72_EXPLICIT_AUTHORITY_INPUTS_NOT_OBSERVED_UNION')
                return NS(**{**vars(value),'control_names':value.control_names+(SELF,TEST)})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            evidence=self.parent_handoff.evidence()
            require(self.authority_declared and self.construct_only and self.native is None
                and evidence['execution_attempts']==evidence['component_connections']==0
                and evidence['original_owner']['observed_original_Jobs']==0
                and evidence['authorization_dependency_present'] is (authorize is not None),
                'SAME_ORIGINAL_PRODUCT_ROUTE_INERT_NOT_EXECUTION')
            reader=a.AcceptanceReader(root,q.checkpoint)
            for name in (SELF,TEST):a.exact(reader.pin(name),dict(data.planned.current[name]),'DIRECT_CURRENT_AUTHORITY_CONNECTION_SOURCE')
            reader.finish();reader.checkpoint()
            require(reader.final_fresh_hashes==len(reader.snapshots)==2,'TWO_FRESH_AUTHORITY_INPUTS_AND_CLOSING_ONCE')
            return dict(value,state='PASS_PRODUCT_AUTHORITY_CONNECTION_CONSTRUCTION_NOT_EXECUTION',
                product_authority_connection=dict(projection=projection,external_dependency_supplied=authorize is not None,
                    original_parent_evidence=evidence,connection_fresh_inputs=2,connection_final_fresh_hashes=2,
                    connection_source_pins=list(reader.snapshots.values()),original_closed_reader_reused_or_reset=False,
                    actual_Native_or_product_or_GO_or_intent_executed=False,GO_authorized=False,accepted_count_delta=0))
    return Driver


def direct(root,pin):
    path=root/pin['path']
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCES')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    return exact(raw,pin)


def construct(*,authorize=None,output=OUTPUT,wrap=None):
    require(authorize is None or callable(authorize),'EXPLICIT_EXTERNAL_DEPENDENCY_NOT_APPROVAL_FLAG')
    require(wrap is None or callable(wrap),'EXPLICIT_OUTER_CONSTRUCTION_DRIVER')
    require(type(output) is str and re.fullmatch(
        r'implementation/p09/evidence/p09-361-native011-[A-Za-z0-9-]{1,120}\.v1\.json',output)
        and (wrap is not None or output==OUTPUT),'BOUNDED_CONSTRUCTION_OUTPUT_NOT_CANONICAL_RUNTIME')
    root=Path(__file__).resolve().parents[2]
    require(not(root/output).exists(),'EXCLUSIVE_NEW_CONSTRUCTION')
    env=dict(__name__='p09_product_authority_bootstrap',__file__=LOADER['path'])
    exec(compile(direct(root,LOADER),LOADER['path'],'exec'),env)
    # Both complete sources are explicit, pinned private dependencies. Do not
    # add a default project import to the unchanged Native helper64 inventory.
    libraries,_=NS(**env).load(root,[SOURCE,CONNECTION],{})
    parent=libraries.native011_product_parent_handoff;connection=libraries.native011_full_frame_worker_connection
    attest(direct(root,CONNECTION),CONNECTION,connection.driver_type)
    selected,projection=project(direct(root,SOURCE),parent,authorize=authorize)
    audit=connection.AuditSelection(root,direct(root,connection.AUDIT),sys.addaudithook)
    def choose(base):
        original=driver_type(connection.driver_type(selected(base),audit,execute_whole=False),projection,authorize=authorize)
        revised=original if wrap is None else wrap(original)
        require(type(revised) is type and issubclass(revised,original),'OUTER_DRIVER_RETAINS_ORIGINAL_CONSTRUCTION_CHAIN')
        return revised
    original=parent.main
    entry=FunctionType(original.__code__,dict(original.__globals__,OUTPUT=output,driver_type=choose),
        argdefs=original.__defaults__,closure=original.__closure__);entry.__kwdefaults__=original.__kwdefaults__
    return entry()


def main():
    require(not sys.argv[1:],'CONSTRUCTION_ONLY_NO_GO_OR_RUNTIME_ARGUMENTS');sys.dont_write_bytecode=True
    return construct()


if __name__=='__main__':raise SystemExit(main())
