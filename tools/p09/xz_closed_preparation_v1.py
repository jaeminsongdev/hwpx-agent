"""v17 XZ61 parent/worker graph profile on whole frozen orchestration.

Only metadata literals and CODE13 reference differ from the frozen v10 entry.
No Native/review/accept/preflight/dispatch CLI yet. The original worker entry
keeps its full Job/GO/product protections. Default modules stay unchanged.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import ast
import copy
import hashlib
import json
import re
import sys

SELF="tools/p09/xz_closed_preparation_v1.py"
TEST="tools/p09/tests/test_xz_closed_preparation_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
SOURCE=dict(path="tools/p09/level6_closed_preparation_v1.py",bytes=24229,
    sha256="7caea0f722b6205ad9691d35ff217e9c299da490ad2c22dfe98e1300367c55eb")
CORE=dict(path="tools/p09/xz_ordinary_binding_v1.py",bytes=14211,
    sha256="1ed4280073c804753de316887b7091ef507146dadb5bcb539b0c223b65bfae20")
CORE_CODE=dict(path=PREFIX+"xz-binding-code001.v1.json",bytes=23432,
    sha256="761ba28ea064fb8c7a7337b7ba6d2ffe1ee2f70d4953951e5993aa90168359a8")
CODE=PREFIX+"xz-profile-connection-code009.v1.json"
CODE_STATE="PASS_XZ_PROFILE_METADATA_CONNECTION_CODE21_NOT_GRAPH_WORKER_OR_PRODUCT"
VERSION="v17"
IDENTIFIERS=dict(profile_CODE_record_max=16,graph_attempt_max=8,Native_physical_run=8,automatic_retry=False,existing_records_overwritten=False)
PRESSURE=dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,
    sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd")


def require(ok,label):
    if not ok:raise ValueError("XZ_PROFILE_"+label)


def context(arguments):
    require(type(arguments) is list and all(type(v) is str for v in arguments),"EXPLICIT_ARGUMENTS")
    if len(arguments)==3 and arguments[:2]==["--owned-worker","--task"]:
        require(0<len(arguments[2])<=256 and arguments[2].isascii() and not arguments[2].startswith("--"),"ORIGINAL_WORKER_TASK_STILL_VALIDATED_BY_ORIGINAL_BODY")
        return "worker"
    require(not any(v.split("=",1)[0] in ("--native","--review","--accept","--preflight","--qualify","--bootstrap","--code","--owned-worker") for v in arguments),"NO_UNQUALIFIED_RUNTIME_OR_OTHER_STAGE")
    require(len(arguments)==7 and arguments[0]=="--graph" and arguments[1::2]==["--case","--run","--attempt"],"ONLY_EXPLICIT_GRAPH_CONTEXT")
    require(arguments[2]=="165" and arguments[4]=="8" and re.fullmatch("[1-8]",arguments[6]),"EXACT_CURRENT165_RUN008_GRAPH")
    return "graph"


def code_identifier(value):
    require(type(value) is int and 1<=value<=16,"FINITE_METADATA_CODE_IDENTIFIER_NOT_NATIVE")
    return value


def projected(original,source,env,source_tree=None):
    require(type(original) is FunctionType and original.__code__.co_filename.replace("\\","/")==SOURCE["path"]
        and original.__name__ in ("loader_profile","main"),"EXACT_FROZEN_FUNCTION_FAMILY")
    require(type(source) is bytes and len(source)==SOURCE["bytes"] and hashlib.sha256(source).hexdigest()==SOURCE["sha256"],"WHOLE_FROZEN_SOURCE")
    if source_tree is None:source_tree=ast.parse(source)
    require(isinstance(source_tree,ast.Module),"PARSED_SOURCE_MODULE")
    node=copy.deepcopy(next(n for n in source_tree.body if isinstance(n,ast.FunctionDef) and n.name==original.__name__))
    def compile_one(value):
        namespace=dict(original.__globals__)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[value],type_ignores=[])),original.__code__.co_filename,"exec",dont_inherit=True),namespace)
        return namespace[original.__name__]
    require(compile_one(copy.deepcopy(node)).__code__==original.__code__,"ENTIRE_FROZEN_FUNCTION_BEFORE_PROJECTION")
    if original.__name__=="loader_profile":
        changes={
            (str,"level6-binding-code005.v1.json"):"xz-binding-code001.v1.json",
            (str,"PASS_LEVEL6_ORDINARY_BINDING_CODE10_NOT_ENTRY_OR_PRODUCT"):"PASS_XZ_ORDINARY_BINDING_CODE13_NOT_ENTRY_OR_PRODUCT",
            (int,10):13,
            (str,r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-worker-capsule([0-9]{3})\.compact\.v10\.json"):
                r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-worker-capsule([0-9]{3})\.compact\.v17\.json",
            (str,"-successor-level6-factory"):"-successor-xz-factory"}
    else:changes={(str,"level6-entry-"):"xz-entry-",(str,"successor-level6-"):"successor-xz-"}
    counts={key:0 for key in changes};before=ast.dump(node,include_attributes=False)
    class Rewrite(ast.NodeTransformer):
        def visit_Constant(self,value):
            key=(type(value.value),value.value)
            if key in changes:
                counts[key]+=1;new=ast.copy_location(ast.Constant(value=changes[key]),value);new._xz_before=value;return new
            return value
    node=Rewrite().visit(node)
    require(set(counts.values())=={1},"EXACT_ONE_OF_EACH_ALLOWED_METADATA_LITERAL")
    class Undo(ast.NodeTransformer):
        def visit(self,value):
            if hasattr(value,"_xz_before"):return copy.deepcopy(value._xz_before)
            return super().visit(value)
    restored=Undo().visit(copy.deepcopy(node))
    require(ast.dump(restored,include_attributes=False)==before and compile_one(restored).__code__==original.__code__,"ENTIRE_RECURSIVE_CODE_AND_AST_INVERSE")
    fn=compile_one(node)
    result=FunctionType(fn.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    result.__kwdefaults__=original.__kwdefaults__
    return result


def core_adapter(core,xz):
    def install(module,historical_pairs):return core.install(module,historical_pairs,xz)
    return NS(**{**vars(core),"install":install})


def code_witness(q,a):
    row=q.json(CODE)
    a.fields(row,dict(state=CODE_STATE,contracts=dict(run=21,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"CURRENT_PROFILE_CONNECTION_CODE")
    a.exact(row["metadata_identifier_policy"],IDENTIFIERS,"FINITE_CODE_HISTORY_NOT_NATIVE_RUN_EXPANSION")
    require(type(row["fresh_inputs"]) is int and row["fresh_inputs"]==row["final_fresh_hashes"]>0,"FULL_PROFILE_CODE_CLOSURE")
    for pin in row["source_pins"]:a.exact(q.pin(pin["path"]),pin,"EVERY_CURRENT_PROFILE_CODE_SOURCE")


def synchronize_worker_dependencies(runtime):
    worker=runtime.owned_worker_entry
    require(type(worker) is FunctionType and worker.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_runtime")
        and worker.__code__.co_filename.replace("\\","/")=="tools/p09/current_queue_successor_runtime.py","ACTUAL_PRIVATE_WORKER_AFTER_FULL_INSTALL")
    for name in ("reconstruct_worker_graph","current_input_scope"):
        value=getattr(runtime,name)
        require(type(value) is FunctionType and value.__globals__.get("__name__","").startswith("p09_exact_"),"QUALIFIED_PRIVATE_PUBLIC_DEPENDENCY")
        worker.__globals__[name]=value
        require(worker.__globals__[name] is getattr(runtime,name),"SAME_PUBLIC_AND_ACTUAL_WORKER_DEPENDENCY")


def finish_binding_dependencies(connection,runtime):
    if hasattr(connection,"xz_worker_binding_owner"):
        require(connection.xz_worker_binding_owner is runtime,"ONE_PRIVATE_BINDING_DEPENDENCY_OWNER");return
    whole=connection.binding_api;sync=synchronize_worker_dependencies
    def binding_api(*args,**kwargs):
        api=whole(*args,**kwargs);original=api.connect
        def connect(*items,**options):
            result=original(*items,**options)
            # All namespace/binding construction finishes before committing the
            # public dependencies used by the unchanged actual worker body.
            sync(runtime)
            return result
        return NS(**{**vars(api),"connect":connect})
    connection.binding_api=binding_api;connection.xz_worker_binding_owner=runtime


def keep_worker_dependency_family(namespace):
    if getattr(namespace,"xz_live_worker_literals",False):return
    whole=namespace.literal_function;checked=require;make=FunctionType
    def literal(fn,mapping):
        changed,proof=whole(fn,mapping)
        if fn.__name__=="owned_worker_entry":
            checked(fn.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_runtime")
                and fn.__code__.co_filename.replace("\\","/")=="tools/p09/current_queue_successor_runtime.py","PRIVATE_ACTUAL_WORKER_FAMILY_ONLY")
            checked(proof.get("exact_entire_code_inverse") is True and changed.__code__.co_code==fn.__code__.co_code
                and changed.__code__.co_names==fn.__code__.co_names,"WHOLE_ORIGINAL_WORKER_BODY_AND_METADATA_INVERSE")
            live=make(changed.__code__,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
            live.__kwdefaults__=fn.__kwdefaults__
            checked(live.__code__ is changed.__code__ and live.__defaults__ is fn.__defaults__
                and live.__closure__ is fn.__closure__,"ONLY_LIVE_ORIGINAL_DEPENDENCY_FAMILY")
            return live,dict(proof,original_worker_live_dependency_family_retained=True)
        return changed,proof
    literal=FunctionType(literal.__code__,whole.__globals__,argdefs=literal.__defaults__,closure=literal.__closure__)
    whole.__globals__["literal_function"]=literal;namespace.literal_function=literal
    sync=synchronize_worker_dependencies
    install=getattr(namespace,"install",None)
    if install is not None:
        def installed(runtime):
            result=install(runtime);sync(runtime);return result
        installed=FunctionType(installed.__code__,install.__globals__,argdefs=installed.__defaults__,closure=installed.__closure__)
        install.__globals__["install"]=installed;namespace.install=installed
    retarget=getattr(namespace,"retarget_worker",None)
    if retarget is not None:
        def retargeted(runtime,path):
            result=retarget(runtime,path);sync(runtime);return result
        retargeted=FunctionType(retargeted.__code__,retarget.__globals__,argdefs=retargeted.__defaults__,closure=retargeted.__closure__)
        retarget.__globals__["retarget_worker"]=retargeted;namespace.retarget_worker=retargeted
    namespace.xz_live_worker_literals=True


def qualified_loader(original,a):
    def load(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        namespace=getattr(modules,"expanded_preparation_namespace_v1",None)
        if namespace is not None:keep_worker_dependency_family(namespace)
        fix=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if fix is not None and not getattr(fix,"xz_connection_qualified_reader",False):
            whole=fix.load
            def connected(*items,**options):
                values=list(items);api=values[1]
                class Reader(api.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs)
                        for path in (SELF,TEST):self.pin(path)
                        a.exact(self.pin(SOURCE["path"]),SOURCE,"WHOLE_FROZEN_PROFILE_SOURCE")
                        code_witness(self,a)
                values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                linked=whole(*values,**options)
                finish_binding_dependencies(linked.connection,linked.modules.current_queue_successor_runtime)
                return linked
            fix.load=connected;fix.xz_connection_qualified_reader=True
        return modules,proof
    return NS(**{**vars(original),"load":load})


def graph_tools(root,original,delivery):
    def dynamic(path):
        data=(root/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entries,_=original.load(root,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entries.preparation_attributed_entry_v1
    raw,_=original.load(root,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS+[delivery.BASELINE],{})
    policy=raw.preparation_attributed_cpu_v1;baseline=raw.owned_cpu_baseline_v1
    def guarded(original,*,role):
        return baseline.guard_type(policy.guard_type(original,role=role))
    return NS(entry=entry,policy=NS(**{**vars(policy),"guard_type":guarded}))


def graph_loader(root,original,a,delivery,envelope,*,instances=None,tools=None):
    """Qualified preparation-only facade; never selected by the worker path."""
    if tools is None:tools=graph_tools(root,original,delivery)
    if instances is None:instances=[]
    routed=tools.entry.route_loader(root,original,tools.policy,a,"whole_metadata_preflight",instances,
        require_connection=True,connection_attempt=10,envelope=envelope)
    return routed,instances


def connect(root,envelope,a,delivery,*,require_code=True,role="code"):
    require(type(require_code) is bool,"EXPLICIT_CONNECTION_QUALIFICATION")
    require(role in ("graph","worker","code"),"ONLY_GRAPH_HAS_PREPARATION_CPU_POLICY")
    original=envelope.namespace_bundle
    namespaces,_=original.load(root,[SOURCE],{})
    frozen=namespaces.level6_closed_preparation_v1
    source=(root/SOURCE["path"]).read_bytes()
    codecs,_=original.load(root,[delivery.OLD_ENCODE,delivery.OLD,delivery.XZ],{})
    xz=codecs.receipt_xz_envelope_v1
    instances=[];tools=graph_tools(root,original,delivery) if role=="graph" else None
    def alias_load(*items,**options):
        modules,proof=original.load(*items,**options)
        namespace=getattr(modules,"expanded_preparation_namespace_v1",None)
        if namespace is not None:keep_worker_dependency_family(namespace)
        pressure=getattr(modules,"terminal_metadata_pressure_v1",None)
        if tools is not None and pressure is not None:
            # Frozen graph main asks its root loader for utils, not its profiled
            # loader. Change only this Guard facade; do not bind root imports
            # below the complete profile or change worker/Native namespaces.
            modules.terminal_metadata_pressure_v1=tools.entry.pressure_facade(pressure,tools.policy,"whole_metadata_preflight",instances)
        core=getattr(modules,"xz_ordinary_binding_v1",None)
        if core is not None:modules.level6_ordinary_binding_v1=core_adapter(core,xz)
        return modules,proof
    alias=NS(**{**vars(original),"load":alias_load})
    proxy=NS(**{**vars(envelope),"namespace_bundle":alias})
    env=dict(frozen.main.__globals__,SELF=SELF,VERSION=VERSION,CORE=CORE,__file__=SELF)
    source_tree=ast.parse(source)
    loader=projected(frozen.loader_profile,source,env,source_tree)
    def profile(*args,**kwargs):
        base=loader(*args,**kwargs)
        if require_code:base=qualified_loader(base,a)
        if role=="graph":
            # Bind late imports to the whole profiled/qualified loader, not to
            # raw sources below its reconstruction and fixed-codec hooks.
            base,_=graph_loader(root,base,a,delivery,NS(**{**vars(envelope),"namespace_bundle":base}),instances=instances,tools=tools)
        return base
    env["loader_profile"]=profile
    main=projected(frozen.main,source,env,source_tree)
    return NS(main=main,execute=frozen.execute,frozen=frozen,loader_profile=loader,
        envelope=proxy,preparation_guard_instances=instances,preparation_CPU_policy_active=(role=="graph"),
        whole_original_function_inverse=True,old_version="v10",version=VERSION)


def qualify(attempt,c,a,envelope,delivery):
    import io,time,unittest
    code_identifier(attempt);output=PREFIX+f"xz-profile-connection-code{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_PROFILE_CODE")
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entry_ns,_=envelope.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entry_ns.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    helpers,_=envelope.namespace_bundle.load(c.ROOT,[delivery.BASELINE],{})
    resource_summary={};phase=dict(value="bootstrap_policy")
    old=delivery.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),resource_summary,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return delivery.observed_guard(helpers.owned_cpu_baseline_v1.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight")),resource_summary,phase)()
    guards=[];started=time.monotonic()
    row=dict(state="FAILED_XZ_PROFILE_CONNECTION_CODE_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
        actual_parent_worker_graph_or_product_NOT_RUN=True,Native_policy_changed=False,metadata_identifier_policy=dict(IDENTIFIERS))
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            a.exact(q.pin(delivery.BASELINE["path"]),delivery.BASELINE,"MEASURED_BASELINE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            for path in (SELF,TEST):q.pin(path)
            for pin in (SOURCE,CORE,CORE_CODE,delivery.XZ):a.exact(q.pin(pin["path"]),pin,"FROZEN_PROFILE_AND_QUALIFIED_EXTENSION")
            code=a.read_exact(q,CORE_CODE)
            a.fields(code,dict(state="PASS_XZ_ORDINARY_BINDING_CODE13_NOT_ENTRY_OR_PRODUCT",contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_XZ_BINDING_CODE13")
            for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_BINDING_CODE_SOURCES")
            from tests import test_xz_closed_preparation_v1 as tests
            tests.MODULE=sys.modules[__name__];tests.ROOT=c.ROOT;tests.ENVELOPE=envelope;tests.ACCEPTANCE=a;tests.DELIVERY=delivery
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
            a.exact(row["contracts"],dict(run=21,errors=0,failures=0,skipped=0),"ALL_PROFILE_CONNECTION21")
        q,proof=entry.closed_bootstrap(c.ROOT,a,old,prep,verify_policy,verify,guards)
        row.update(state=CODE_STATE,bootstrap_policy_validation=proof,source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_Native_and_GO_bodies_unchanged=True,all_recursive_projected_code_inverses_equal=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        samples=[s for g in guards for s in g.samples]
        row.update(cleanup_confirmed=all(g.cleanup for g in guards),elapsed_seconds=time.monotonic()-started,
            original_fresh_sample_resource_summary=resource_summary,
            terminal_resource_sample=None if not samples else {k:samples[-1].get(k) for k in ("system_cpu_percent","parent_cpu_machine_percent","available_ram_percent","parent_private_percent")},
            resource_observer_extra_sampler_or_Windows_calls=False,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_PROFILE_CODE_GUARDS_CLOSED");raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_errors","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"]==CODE_STATE else 1


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    import xz_corpus_delivery_v1 as delivery
    # Same explicit host RAM profile as the current recovery producer.
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c)
    arguments=sys.argv[1:]
    if len(arguments)==3 and arguments[:2]==["--connection-code","--attempt"]:
        require(re.fullmatch("[1-9]|1[0-6]",arguments[2]),"FINITE_CODE_ATTEMPT")
        return qualify(int(arguments[2]),c,a,envelope,delivery)
    role=context(arguments)
    connected=connect(c.ROOT,envelope,a,delivery,role=role)
    return connected.execute(connected.main,connected.envelope)


if __name__=="__main__":raise SystemExit(main())
