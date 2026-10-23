"""One private original metadata-factory closure dependency, no byte IO.

Preserves the real allocator's 2.5/4MiB byte policy, existing source/workspace
wrappers, original Router/decoder/shared budget and reader tracking. No default
module/class mutation or Native/worker/product execution is performed here.
"""
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native011_metadata_tail_connection.py'
TEST='tools/p09/tests/test_native011_metadata_tail_connection.py'
METADATA=dict(path='tools/p09/lossless_metadata_connection_v1.py',bytes=15742,
    sha256='6a29bb5b9a7eea25edab896b8fa32bd5425a7c567a3ee51a8428a2fb813f2524')
BUILD=dict(path='tools/p09/build_case112_current_stored.py',bytes=24527,
    sha256='366f35c2ec22fee9e2b5344402cd2ae79eb9bbc8e3c021e769024ffccd765faa')


def require(ok,code):
    if not ok:raise ValueError('METADATA_TAIL_CONNECTION_'+code)


def connect(linked,owner,pins,candidate,exact,pressure,chunk_api,raw,metadata_raw,build_raw,code_api):
    connection=owner.metadata_connection;run=linked.engine.run_owned;env=run.__globals__
    require(owner.phase=='NEW' and owner.shared.metadata is owner.shared.frame is None and not owner.shared.restored
        and connection.readers==connection.budgets==[] and linked.state.attempts==linked.state.calls==0,
        'UNUSED_PARENT_BEFORE_METADATA_BUDGET_OR_WORKER')
    require(type(run) is FunctionType and connection.original_run is run and not any(
        getattr(module,'__dict__',None) is env for module in tuple(sys.modules.values()) if module),
        'ACTUAL_PRIVATE_ENGINE_ONLY')
    require(type(pins) is dict and pins=={name:dict(pin) for name,pin in owner.whole.items()},
        'COMPLETE_DECLARED_PHYSICAL_WHOLE_NOT_OBSERVED_MODULE_UNION')
    old_build=env['build'];old_factory=old_build.BuildReader;new=old_factory.__new__
    forms=code_api.compile_forms(metadata_raw,METADATA)
    require(type(new) is FunctionType and any(new.__code__==code_api.nested(form,
        'connect_engine','BuildReader','__new__') for form in forms),'ENTIRE_ORIGINAL_METADATA_FACTORY_CODE')
    cells=code_api.cells(new);base=cells['old_reader'];router=cells['Router']
    require(base is connection.original_reader and cells['readers'] is connection.readers
        and cells['budgets'] is connection.budgets and cells['shared'] is owner.shared,
        'ORIGINAL_ALLOCATOR_ROUTER_TRACKING_AND_SHARED_OWNER')
    require(any(router.__init__.__code__==code_api.nested(form,'connect_engine','Router','__init__')
        and router.decode_fresh.__code__==code_api.nested(form,'connect_engine','Router','decode_fresh')
        for form in forms),'ENTIRE_ORIGINAL_ROUTER_AND_CHECKPOINT_BODY')
    build_forms=code_api.compile_forms(build_raw,BUILD)
    originals=[cls for cls in base.__mro__ if cls.__name__=='BuildReader' and '_read' in vars(cls)
        and vars(cls)['_read'].__code__.co_filename.replace('\\','/').endswith(BUILD['path'])]
    require(len(originals)==1,'EXACT_ONE_ORIGINAL_BUILD_WRAPPER')
    original=originals[0]
    require(any(all(getattr(original,name).__code__==code_api.nested(form,'BuildReader',name)
        for name in ('__init__','_read','_source')) for form in build_forms),
        'WHOLE_ORIGINAL_BUILD_OPEN_SOURCE_AND_CONSTRUCTOR_METHODS')
    query_type=original.__init__.__globals__['QueryPacer']
    Selected,proof=candidate.reader_type(base,pins,exact,pressure,chunk_api.original,chunk_api,raw,
        precise=True,query_type=query_type,pacer_policy='metadata_weighted')
    def cell(value):return (lambda:value).__closure__[0]
    selected=FunctionType(new.__code__,new.__globals__,argdefs=new.__defaults__,closure=tuple(
        cell(Selected) if name=='old_reader' else previous
        for name,previous in zip(new.__code__.co_freevars,new.__closure__)))
    selected.__kwdefaults__=new.__kwdefaults__
    require(selected.__code__ is new.__code__ and selected.__globals__ is new.__globals__ and all(
        name=='old_reader' or before is after for name,before,after in zip(
            new.__code__.co_freevars,new.__closure__,selected.__closure__)),
        'ONLY_ORIGINAL_READER_CLASS_CLOSURE_DEPENDENCY')
    class Factory(old_factory):
        __new__=staticmethod(selected)
    saved=dict(env);previous=env['build'];replacement=NS(**{**vars(previous),'BuildReader':Factory})
    env['build']=replacement
    try:
        require(set(env)==set(saved) and all(env[key] is value for key,value in saved.items() if key!='build')
            and linked.engine.run_owned is run and old_build.BuildReader is old_factory
            and all(getattr(replacement,key) is value for key,value in vars(previous).items() if key!='BuildReader')
            and connection.readers==connection.budgets==[] and owner.shared.metadata is None,
            'ONE_PRIVATE_BUILD_FACTORY_SLOT_WITHOUT_ALLOCATION')
    except BaseException:
        env['build']=previous;raise
    return NS(factory=Factory,previous=old_factory,selected_reader=Selected,original_reader=base),dict(proof,
        entire_original_metadata_factory_and_Router_code_retained=True,
        original_BuildReader_open_path_and_constructor_code_retained=True,
        complete_physical_scope_declared_before_connection=True,metadata_reader_allocations_during_connection=0,
        original_factory_closure_only_reader_class_changed=True,default_modules_classes_or_ctors_changed=False,
        original_decoder_shared_budget_and_reader_tracking_retained=True,
        actual_Native_Frame_or_worker_or_GO_or_product_created=False)
