"""One private codec dependency shared by actual metadata and future Frame.

No default class/module mutation, source scope reduction, budget/clock change,
reader/Frame/worker/GO creation or acceptance. Only for the readonly owner.
"""
import ast
import hashlib
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_chunk_join_connection.py'
TEST='tools/p09/tests/test_native011_chunk_join_connection.py'
SOURCE=dict(path='tools/p09/runtime_envelope_source_projection_v1.py',bytes=6401,
    sha256='728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b')
METADATA=dict(path='tools/p09/lossless_metadata_connection_v1.py',bytes=15742,
    sha256='6a29bb5b9a7eea25edab896b8fa32bd5425a7c567a3ee51a8428a2fb813f2524')


def require(ok,label):
    if not ok:raise ValueError('CHUNK_JOIN_CONNECTION_'+label)


def compile_forms(raw,pin):
    require(type(raw) is bytes and len(raw)==pin['bytes']
        and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_ENTIRE_SOURCE')
    tree=ast.parse(raw.decode('utf-8'))
    nodes=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
    return (compile(raw,pin['path'],'exec'),compile(ast.fix_missing_locations(
        ast.Module(body=nodes,type_ignores=[])),pin['path'],'exec'))


def nested(code,*names):
    for name in names:
        found=[value for value in code.co_consts if type(value) is CodeType and value.co_name==name]
        require(len(found)==1,'ONE_EXACT_NESTED_CODE');code=found[0]
    return code


def cells(function):
    require(type(function) is FunctionType and function.__closure__ is not None,'ORIGINAL_CLOSURE')
    return dict(zip(function.__code__.co_freevars,(cell.cell_contents for cell in function.__closure__)))


def connect(linked,owner,declared_projection,candidate,projection_raw,metadata_raw,codec_raw):
    require(owner.phase=='NEW' and owner.shared.metadata is owner.shared.frame is None
        and not owner.shared.restored and linked.state.attempts==linked.state.calls==0,
        'UNUSED_READONLY_PARENT_BEFORE_METADATA_OR_FRAME')
    connection=owner.metadata_connection;run=linked.engine.run_owned
    require(connection.original_run is run and connection.readers==connection.budgets==[]
        and type(run) is FunctionType and not any(getattr(m,'__dict__',None) is run.__globals__
            for m in tuple(sys.modules.values()) if m),'ACTUAL_PRIVATE_UNUSED_ENGINE_METADATA_CONNECTION')
    forms=compile_forms(metadata_raw,METADATA)
    new=run.__globals__['build'].BuildReader.__new__;new_cells=cells(new);router=new_cells['Router']
    require(any(new.__code__==nested(code,'connect_engine','BuildReader','__new__')
        and router.decode_fresh.__code__==nested(code,'connect_engine','Router','decode_fresh')
        and router.__init__.__code__==nested(code,'connect_engine','Router','__init__') for code in forms),
        'ORIGINAL_METADATA_READER_AND_ROUTER_BODIES')
    require(new_cells['readers'] is connection.readers and new_cells['budgets'] is connection.budgets
        and new_cells['shared'] is owner.shared,'ACTUAL_SHARED_METADATA_FACTORY_CLOSURES')
    projection=cells(router.decode_fresh)['projection'];cls=type(projection)
    require(type(declared_projection) is cls and projection.next_case==declared_projection.next_case==165
        and len(projection._bindings)==162 and projection._bindings==declared_projection._bindings
        and all(declared_projection.semantic_pins.get(name)==pin for name,pin in projection.semantic_pins.items()),
        'ACTUAL_METADATA_AND_DECLARED_FRAME_SAME_FULL162_PRIVATE_PROJECTION')
    old=cls.decode_fresh;env=old.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and cls.__module__==env['__name__']
        and not any(getattr(m,'__dict__',None) is env or getattr(m,'__dict__',{}).get('Projection') is cls
            for m in tuple(sys.modules.values()) if m),'NO_DEFAULT_PROJECTION_OR_NAMESPACE_MUTATION')
    source_forms=compile_forms(projection_raw,SOURCE)
    class_node=next(node for node in ast.parse(projection_raw).body if isinstance(node,ast.ClassDef) and node.name=='Projection')
    methods=[node for node in class_node.body if isinstance(node,ast.FunctionDef)]
    slots=next(ast.literal_eval(node.value) for node in class_node.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=='__slots__' for target in node.targets))
    require(type(cls) is type and cls.__bases__==(object,) and cls.__slots__==slots
        and set(vars(cls))=={*(node.name for node in methods),*slots,'__slots__','__module__','__doc__'},
        'EXACT_ORIGINAL_PROJECTION_CLASS_LAYOUT')
    def exact_class(form):
        code=nested(form,'Projection')
        for method in methods:
            value=vars(cls)[method.name]
            if method.decorator_list:
                if type(value) is not property or value.fset is not None or value.fdel is not None:return False
                value=value.fget
            if type(value) is not FunctionType or value.__globals__ is not env or value.__code__!=nested(code,method.name):return False
        return True
    require(any(exact_class(form) for form in source_forms),'ALL_ORIGINAL_PROJECTION_METHOD_AND_PROPERTY_BODIES')
    original_codec=env['codec'];codec_forms=compile_forms(codec_raw,candidate.SOURCE)
    require(any(original_codec.decode.__code__==nested(form,'decode') for form in codec_forms),
        'UNUSED_ORIGINAL_CODEC_NOT_ALREADY_REPLACED')
    selected,codec_proof=candidate.connect(codec_raw,original_codec)
    original_decode=original_codec.decode;saved_env=dict(env);saved_class=dict(vars(cls))
    method=FunctionType(old.__code__,dict(env,codec=selected),argdefs=old.__defaults__,closure=old.__closure__)
    method.__kwdefaults__=old.__kwdefaults__
    cls.decode_fresh=method
    try:
        require(method.__code__ is old.__code__ and set(env)==set(saved_env)
            and all(env[name] is value for name,value in saved_env.items())
            and original_codec.decode is original_decode
            and all(vars(cls)[name] is value for name,value in saved_class.items() if name!='decode_fresh')
            and projection.decode_fresh.__func__ is declared_projection.decode_fresh.__func__ is method,
            'ONE_PRIVATE_CLASS_METHOD_CODEC_DEPENDENCY_ONLY')
    except BaseException:
        cls.decode_fresh=old;raise
    return NS(projection_type=cls,method=method,metadata_projection=projection),dict(
        codec_connection_proof=codec_proof,projection_source_pin=dict(SOURCE),metadata_source_pin=dict(METADATA),
        original_projection_method_and_property_code_retained=True,exact_same_metadata_and_Frame_projection_class=True,
        actual_metadata_factory_closure_verified=True,old_codec_and_all_other_namespace_slots_unchanged=True,
        default_module_or_class_changed=False,reader_or_Frame_or_budget_created=False,
        metadata_and_Frame_decoder5_clock_or_CPU_RAM_policy_changed=False,
        installed_in_product=False,actual_Native_or_product_qualified=False)
