"""Original metadata factory with an explicit owned-assignment reader selector.

No engine body, allocation, IO, Frame, worker or GO runs during connection.
The original connection verifies its complete factory/Router/BuildReader code.
An allocator's unused default rate is not mistaken for the product IO policy.
"""
import ast
import copy
import hashlib
from types import SimpleNamespace as NS

SELF='tools/p09/native011_engine_owned_metadata_connection.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_connection.py'
ENGINE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_CONNECTION_'+code)


def connect(linked,owner,pins,connection,candidate,adoption,exact,pressure,chunk_api,
        raw,metadata_raw,build_raw,code_api):
    previous=linked.engine.run_owned.__globals__['build'];calls=[]
    original_selector=candidate.reader_type
    def selector(*args,**kwargs):
        require(not calls and kwargs.get('pacer_policy')=='metadata_weighted' and kwargs.get('precise') is True,
            'ONE_ORIGINAL_UNUSED_ALLOCATOR_SELECTOR')
        Selected,allocator_proof=original_selector(*args,**kwargs)
        Product,assignment_proof=adoption.reader_type(Selected,exact,pressure,precise=True)
        calls.append((Selected,Product))
        return Product,dict(unused_allocator_stage=allocator_proof,engine_assignment_stage=assignment_proof)
    selected=NS(**{**vars(candidate),'reader_type':selector})
    try:
        link,proof=connection.connect(linked,owner,pins,selected,exact,pressure,chunk_api,
            raw,metadata_raw,build_raw,code_api)
        require(len(calls)==1 and link.selected_reader is calls[0][1]
            and candidate.reader_type is original_selector and owner.metadata_connection.readers==[]
            and owner.metadata_connection.budgets==[] and owner.shared.metadata is owner.shared.frame is None,
            'UNALLOCATED_ORIGINAL_FACTORY_WITH_OWNED_ASSIGNMENT_SELECTOR')
    except BaseException:
        linked.engine.run_owned.__globals__['build']=previous;raise
    return link,dict(metadata_factory_connection=proof,original_engine_owned_assignment_required=True,
        original_engine_metadata_IO_rates=dict(binary=1048576,other=2097152),
        default_candidate_or_original_classes_mutated=False,reader_allocations_during_connection=0,
        actual_metadata_body_or_Native_or_worker_or_product_executed=False,GO_authorized=False)


def allocate_original_prefix(raw,build,root,checkpoint,pressure):
    """Execute ONLY the two original allocation/assignment statements.

    The complete input_pins function is not called. In this component probe its
    `guarded` name is the existing preparation checkpoint, not a product/Native
    epoch. This cannot qualify the complete engine callback or its deadlines.
    """
    require(type(raw) is bytes and len(raw)==ENGINE['bytes']
        and hashlib.sha256(raw).hexdigest()==ENGINE['sha256'],'WHOLE_ORIGINAL_ENGINE_SOURCE_PIN')
    tree=ast.parse(raw)
    outer=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run_owned')
    inner=next(node for node in outer.body if isinstance(node,ast.FunctionDef) and node.name=='input_pins')
    branch=next(node for node in inner.body if isinstance(node,ast.If)
        and ast.dump(node.test,include_attributes=False)==ast.dump(ast.parse('frame is None',mode='eval').body,include_attributes=False))
    expected=ast.parse('q=build.BuildReader(c.ROOT,guarded)\nq.pacer=byte_policy.OwnedPacer()').body
    nodes=branch.body[:2]
    require(len(nodes)==2 and [ast.dump(n,include_attributes=False) for n in nodes]
        ==[ast.dump(n,include_attributes=False) for n in expected],'EXACT_TWO_UNMODIFIED_ORIGINAL_STATEMENTS')
    env=dict(build=build,c=NS(ROOT=root),guarded=checkpoint,byte_policy=pressure)
    exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),ENGINE['path'],'exec'),env)
    return env['q'],dict(whole_original_engine_source_pin=dict(ENGINE),original_statements_executed=2,
        actual_factory_and_byte_policy_dependencies_used=True,
        original_metadata_input_body_or_Native_or_product_executed=False,
        preparation_checkpoint_not_new_Native_epoch=True,GO_authorized=False)
