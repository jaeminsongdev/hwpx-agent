"""Preparation-only connection of the existing fresh Rust inventory predicates.

No Native entry, default mutation, inventory cache, skipped byte pass or changed
guard. Clone only the private template's build dependency and run_owned globals.
"""
import ast
import copy
import hashlib
from types import CodeType,FunctionType,SimpleNamespace as NS

SELF="tools/p09/preparation_rust_inventory_snapshot_v1.py"
TEST="tools/p09/tests/test_preparation_rust_inventory_snapshot_v1.py"


def require(ok,label):
    if not ok:raise ValueError("PREPARATION_INVENTORY_"+label)


def canonical_inventory(original,raw,pin):
    """Prove full-module compiler context before selecting the same frozen AST.

    Imported-module symbol information changes LOAD_ATTR call setup on CPython.
    Do not disable the leaf's exact AST-only bytecode check or accept arbitrary
    equivalent-looking opcodes. The actual function must match full frozen code.
    """
    require(type(raw) is bytes and len(raw)==pin["bytes"] and
        hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_FROZEN_INVENTORY_SOURCE")
    require(type(original) is FunctionType and original.__name__=="rust_inputs" and
        original.__defaults__ is None and original.__closure__ is None,"EXACT_INVENTORY_FUNCTION")
    filename=original.__code__.co_filename
    compiled=compile(raw.decode("utf-8"),filename,"exec",dont_inherit=True)
    matches=[v for v in compiled.co_consts if type(v) is CodeType and v.co_name=="rust_inputs"]
    require(len(matches)==1 and original.__code__==matches[0],"EXACT_FROZEN_FULL_MODULE_CONTEXT")
    nodes=[n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="rust_inputs"]
    require(len(nodes)==1,"ONE_FROZEN_INVENTORY_BODY")
    env=dict(original.__globals__)
    exec(compile(ast.Module(body=[copy.deepcopy(nodes[0])],type_ignores=[]),filename,"exec",dont_inherit=True),env)
    return env["rust_inputs"]


def engine(engine,snapshot,raw):
    original=engine.run_owned;build=original.__globals__["build"]
    require(type(original) is FunctionType,"EXACT_TEMPLATE_FUNCTION")
    inventory,counters=snapshot.projection(build.base.inputs.rust_inputs,raw)
    inputs=NS(**{**vars(build.base.inputs),"rust_inputs":inventory})
    base=NS(**{**vars(build.base),"inputs":inputs})
    private=NS(**{**vars(build),"base":base})
    execute=FunctionType(original.__code__,dict(original.__globals__,build=private),
        argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    require(execute.__code__ is original.__code__ and execute.__defaults__ is original.__defaults__
        and execute.__closure__ is original.__closure__,"ENTIRE_ORIGINAL_RUN_FUNCTION")
    return NS(**{**vars(engine),"run_owned":execute}),counters


def connect(runtime,snapshot,raw):
    original=runtime.connect_factory;traces=[]
    def factory(*args,**kwargs):
        template,identity,proof=original(*args,**kwargs)
        def template_with_inventory():
            old,proof=template()
            adapter=NS(projection=lambda fn,raw:snapshot.projection(canonical_inventory(fn,raw,snapshot.ORIGINAL_PIN),raw))
            new,counters=engine(old,adapter,raw)
            require(old.run_owned is not new.run_owned and old.worker is new.worker,"PRIVATE_ENGINE_ONLY")
            traces.append(counters)
            return new,dict(proof,preparation_Rust_inventory_snapshot=dict(
                original_run_code_defaults_closure_and_worker_retained=True,
                original_inventory_walk_checkpoint_filters_and_budget_retained=True,
                exact_full_module_compiler_context_verified_before_AST_selection=True,
                shared_default_build_and_inputs_not_mutated=True,Native_or_product_executed=False))
        return template_with_inventory,identity,proof
    # The exact private runtime's other functions use this same family.
    require(original.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_RUNTIME_REQUIRED")
    original.__globals__["connect_factory"]=factory;runtime.connect_factory=factory
    return traces


def compact_report(function):
    """Same whole producer; only its exact final JSON whitespace profile."""
    require(type(function) is FunctionType and function.__name__=="run_preflight" and
        function.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_PREFLIGHT_PRODUCER")
    import json
    counters=NS(final_report_calls=0,other_calls=0)
    def dumps(row,**options):
        if options==dict(ensure_ascii=True,allow_nan=False,indent=2):
            counters.final_report_calls+=1
            return json.dumps(row,ensure_ascii=True,allow_nan=False,indent=None,separators=(",",":"))
        counters.other_calls+=1
        return json.dumps(row,**options)
    private=NS(**{**vars(json),"dumps":dumps});prior=function.__builtins__["__import__"]
    def imports(name,globals=None,locals=None,fromlist=(),level=0):
        if level==0 and name=="json":return private
        return prior(name,globals,locals,fromlist,level)
    env=dict(function.__globals__,__builtins__={**function.__builtins__,"__import__":imports})
    result=FunctionType(function.__code__,env,argdefs=function.__defaults__,closure=function.__closure__)
    result.__kwdefaults__=function.__kwdefaults__
    require(result.__code__ is function.__code__ and result.__defaults__ is function.__defaults__ and
        result.__closure__ is function.__closure__,"WHOLE_PRODUCER_RETAINED")
    return result,counters


def lossless_api(a,fresh,projection,descriptors,budget_type):
    """One preparation reader; fresh physical IO, semantic pins, shared5 work."""
    readers=[]
    class Router:
        semantic_pins=projection.semantic_pins;physical_pins=projection.physical_pins
        next_case=projection.next_case
        def __init__(self):self.budget=None;self.counts={}
        def decode_fresh(self,name,pin,raw,checkpoint):
            require(self.budget is not None,"PREPARATION_DECODER_OWNER")
            prior=self.budget.checkpoint
            def guarded():prior();checkpoint()
            self.budget.checkpoint=guarded
            try:
                value=self.budget.run(lambda check:projection.decode_fresh(name,pin,raw,check))
                self.counts[name]=self.counts.get(name,0)+1
                return value
            finally:self.budget.checkpoint=prior
    router=Router();Routed=fresh.reader_type(a.AcceptanceReader,router,descriptors)
    class Reader(Routed):
        def __init__(self,*args,**kwargs):
            require(not readers and router.budget is None and len(args)>=2 and callable(args[1]),"ONE_PREPARATION_READER_OWNER")
            router.budget=budget_type(args[1])
            super().__init__(*args,**kwargs)
            readers.append(self)
    def summary():
        require(len(readers)==1,"ACTUAL_PREPARATION_READER")
        return dict(fresh.summary(readers[0]),semantic_read_counts=dict(router.counts),
            decoder=router.budget.evidence(),Native_Frame_or_product_qualified=False)
    return NS(**{**vars(a),"AcceptanceReader":Reader}),summary


def reader_api(a,snapshot,qualification_path):
    readers=[]
    class Reader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for name in (SELF,TEST,snapshot.SELF,snapshot.TEST):self.pin(name)
            row=self.json(qualification_path)
            a.fields(row,dict(state="PASS_PREPARATION_RUST_INVENTORY_CODE35_NOT_NATIVE_OR_PRODUCT",
                contracts=dict(run=35,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                product_or_Native_executed=False,accepted_count_delta=0),"CURRENT_CODE35")
            a.require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"CLOSED_CODE35_HASHES")
            for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"CURRENT_INVENTORY_CONNECTION_SOURCES")
            readers.append(self)
    return NS(**{**vars(a),"AcceptanceReader":Reader}),readers
