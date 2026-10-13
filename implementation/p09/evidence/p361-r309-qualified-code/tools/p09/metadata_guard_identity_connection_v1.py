"""Private full metadata engine dependency connection for identity dedup.
Keep original engine/summary bytecodes and unrelated closure/global dependencies.
Only metadata class and its exact summary type predicate are versioned locally.
"""
from types import FunctionType,SimpleNamespace as NS
import metadata_guard_identity_dedup_v1 as optimization

SELF="tools/p09/metadata_guard_identity_connection_v1.py"
TEST="tools/p09/tests/test_metadata_guard_identity_connection_v1.py"

def require(ok,code):
    if not ok:raise ValueError("METADATA_GUARD_CONNECTION_"+code)

def summary_projection(function,old,new):
    active=set();state=dict(functions=[],type_dependency_changes=0,closure_links=0)
    def cell(value):
        def capture():return value
        return capture.__closure__[0]
    def clone(fn,depth=0):
        require(type(fn) is FunctionType and fn.__name__ in ("pressure_summary","summary") and depth<=8
          and id(fn) not in active,"BOUNDED_SUMMARY_CHAIN")
        active.add(id(fn));env=dict(fn.__globals__);changed=[]
        if "MetadataCheckpoint" in fn.__code__.co_names:
            require(env.get("MetadataCheckpoint") is old,"EXACT_ORIGINAL_SUMMARY_TYPE")
            env["MetadataCheckpoint"]=new;state["type_dependency_changes"]+=1
            changed.append("MetadataCheckpoint")
        require(fn.__name__!="summary" or changed==["MetadataCheckpoint"],"EXACT_TYPED_SUMMARY_LEAF")
        closure=fn.__closure__
        if closure is not None:
            cells=[];closure_changed=False
            for name,original in zip(fn.__code__.co_freevars,closure):
                value=original.cell_contents
                if name=="original_summary":
                    require(type(value) is FunctionType and value.__name__ in ("pressure_summary","summary"),
                      "EXACT_ORIGINAL_SUMMARY_CLOSURE")
                    replacement=clone(value,depth+1)
                    if replacement is value:cells.append(original)
                    else:
                        cells.append(cell(replacement));state["closure_links"]+=1;closure_changed=True
                else:cells.append(original)
            if closure_changed:closure=tuple(cells)
        if not changed and closure is fn.__closure__:
            active.remove(id(fn));return fn
        result=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=closure)
        result.__kwdefaults__=fn.__kwdefaults__
        require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
          and all(env[k] is v for k,v in fn.__globals__.items() if k not in changed),
          "ORIGINAL_SUMMARY_CODE_AND_OTHER_GLOBALS")
        state["functions"].append(dict(name=fn.__name__,file=fn.__code__.co_filename,code_unchanged=True))
        active.remove(id(fn));return result
    result=clone(function)
    require(state["type_dependency_changes"]==1,"ONE_EXACT_SUMMARY_TYPE_DEPENDENCY")
    return result,state

def connect(engine,raw):
    require(type(engine.run_owned) is FunctionType,"ORIGINAL_ENGINE_FUNCTION")
    env=engine.run_owned.__globals__;before=dict(env);build=env["build"]
    old=build.pressure.PreSaturationReadCheckpoint
    new,projection=optimization.checkpoint_type(old,raw)
    summary,summary_proof=summary_projection(build.pressure_summary,old,new)
    pressure=NS(**{**vars(build.pressure),"PreSaturationReadCheckpoint":new})
    private=NS(**{**vars(build),"pressure":pressure,"pressure_summary":summary})
    require(all(getattr(private,k) is v for k,v in vars(build).items()
      if k not in ("pressure","pressure_summary")),"OTHER_BUILD_VALUES_UNCHANGED")
    env["build"]=private
    require(set(env)==set(before) and all(env[k] is v for k,v in before.items() if k!="build"),
      "ONLY_PRIVATE_BUILD_DEPENDENCY_CHANGE")
    return dict(metadata_checkpoint_projection=projection,summary_projection=summary_proof,
      original_engine_bytecode_and_original_worker_retained=True,
      original_build_namespace_not_mutated=True,original_summary_fields_and_code_retained=True,
      Native_boundary_reader_or_scope_not_replaced=True,
      source_reads_hashes_rates_deadlines_and_original_guard_criteria_retained=True,
      extra_sampler_or_native_query=False,actual_product_connection_qualified=False,
      PC_freeze_resolved=False)
