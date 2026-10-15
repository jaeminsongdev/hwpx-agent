from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
import copy
import ast
import unittest


class Tests(unittest.TestCase):
    def connected(self):return MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False)

    def test_exact_frozen_recursive_code_inverse_and_new_private_globals(self):
        linked=self.connected()
        self.assertTrue(linked.whole_original_function_inverse)
        self.assertEqual(linked.main.__globals__["SELF"],MODULE.SELF)
        self.assertEqual(linked.main.__globals__["VERSION"],"v17")
        self.assertEqual(linked.frozen.main.__globals__["SELF"],MODULE.SOURCE["path"])
        self.assertEqual(linked.frozen.main.__globals__["VERSION"],"v10")

    def test_whole_source_hash_not_just_target_literals_required(self):
        linked=self.connected();raw=(ROOT/MODULE.SOURCE["path"]).read_bytes()
        with self.assertRaises(ValueError):MODULE.projected(linked.frozen.main,raw+b"\n",dict(linked.main.__globals__))
        with self.assertRaises(ValueError):MODULE.projected(lambda:None,raw,{})

    def test_graph_context_fixed_current165_run8_and_no_other_stage(self):
        good=["--graph","--case","165","--run","8","--attempt","1"]
        self.assertEqual(MODULE.context(good),"graph")
        for flag in ("--native","--review","--accept","--preflight","--qualify","--bootstrap","--code"):
            with self.assertRaises(ValueError):MODULE.context([flag]+good[1:])
        for index,value in ((2,"164"),(4,"7"),(6,"9"),(6,"True")):
            changed=list(good);changed[index]=value
            with self.assertRaises(ValueError):MODULE.context(changed)

    def test_owned_worker_delegation_does_not_add_GO_or_accept_interface(self):
        self.assertEqual(MODULE.context(["--owned-worker","--task","original-task"]),"worker")
        for args in (["--owned-worker","--task",""],["--owned-worker","--task","--native"],["--owned-worker","--task","original-task","--GO"]):
            with self.assertRaises(ValueError):MODULE.context(args)

    def test_core_adapter_adds_only_explicit_codec_argument(self):
        calls=[];codec=object()
        def install(*args):calls.append(args);return "unchanged-return"
        core=NS(install=install,admit=object(),SPEC={"unchanged":True});adapter=MODULE.core_adapter(core,codec)
        self.assertEqual(adapter.install("private","history"),"unchanged-return")
        self.assertEqual(calls,[("private","history",codec)]);self.assertIs(adapter.admit,core.admit);self.assertIs(adapter.SPEC,core.SPEC)

    def test_private_loader_alias_is_explicit_not_a_sys_modules_replacement(self):
        linked=self.connected();before=ENVELOPE.namespace_bundle.load
        modules,proof=linked.envelope.namespace_bundle.load(ROOT,[MODULE.CORE],{})
        self.assertTrue(hasattr(modules,"xz_ordinary_binding_v1"));self.assertTrue(hasattr(modules,"level6_ordinary_binding_v1"))
        self.assertIsNot(modules.level6_ordinary_binding_v1.install,modules.xz_ordinary_binding_v1.install)
        self.assertIs(before,ENVELOPE.namespace_bundle.load)

    def test_original_profile_retargets_actual_worker_to_new_entry(self):
        linked=self.connected();calls=[]
        namespace=NS(literal_function=lambda fn,mapping:fn,retarget_worker=lambda runtime,entry:calls.append(entry))
        original=NS(load=lambda *args,**kwargs:(NS(expanded_preparation_namespace_v1=namespace),[]))
        core=NS()
        loader=linked.loader_profile(ROOT,original,core,ACCEPTANCE,NS())
        modules,_=loader.load()
        modules.expanded_preparation_namespace_v1.retarget_worker(NS(),"ignored-old-entry")
        self.assertEqual(calls,[MODULE.SELF])

    def test_code_witness_requires_closed_complete_current_sources(self):
        pin=dict(path=MODULE.SELF,bytes=1,sha256="a"*64)
        valid=dict(state=MODULE.CODE_STATE,contracts=dict(run=21,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,fresh_inputs=1,final_fresh_hashes=1,source_pins=[pin])
        valid["metadata_identifier_policy"]=dict(MODULE.IDENTIFIERS)
        class Reader:
            def __init__(self,value):self.value=value;self.calls=[]
            def json(self,path):self.calls.append(path);return self.value
            def pin(self,path):self.calls.append(path);return pin
        reader=Reader(valid);MODULE.code_witness(reader,ACCEPTANCE)
        self.assertEqual(reader.calls,[MODULE.CODE,MODULE.SELF])
        for field,value in (("GO_authorized",True),("final_fresh_hashes",0),("product_or_Native_executed",True)):
            bad=copy.deepcopy(valid);bad[field]=value
            with self.assertRaises(ValueError):MODULE.code_witness(Reader(bad),ACCEPTANCE)

    def test_qualified_reader_adds_connection_before_actual_original_factory(self):
        seen=[]
        class Base:
            def __init__(self,*args,**kwargs):seen.append("base")
            def pin(self,path):seen.append(path);return MODULE.SOURCE if path==MODULE.SOURCE["path"] else {}
        result=NS(connection=NS(binding_api=lambda *args:NS(connect=lambda *args:None)),modules=NS(current_queue_successor_runtime=NS()))
        def original(*items,**kwargs):items[1].AcceptanceReader();seen.append("factory");return result
        fix=NS(load=original);loader=NS(load=lambda:(NS(closed_prebody_factory_admission_fix_v1=fix),[]))
        qualified=MODULE.qualified_loader(loader,ACCEPTANCE);modules,_=qualified.load()
        with patch.object(MODULE,"code_witness",side_effect=lambda q,a:seen.append("closed-code")):
            self.assertIs(modules.closed_prebody_factory_admission_fix_v1.load(ROOT,NS(AcceptanceReader=Base)),result)
        self.assertLess(seen.index("closed-code"),seen.index("factory"));self.assertIn(MODULE.TEST,seen)

    def test_main_orchestration_body_and_guard_calls_not_reimplemented(self):
        linked=self.connected();old=linked.frozen.main.__code__;new=linked.main.__code__
        self.assertEqual(new.co_names,old.co_names);self.assertEqual(new.co_varnames,old.co_varnames)
        self.assertEqual(new.co_argcount,old.co_argcount)
        self.assertEqual(new.co_code,old.co_code)
        self.assertIs(linked.execute,linked.frozen.execute)
        raw=(ROOT/MODULE.SOURCE["path"]).read_bytes();tree=ast.parse(raw);before=ast.dump(tree)
        reused=MODULE.projected(linked.frozen.main,raw,dict(linked.main.__globals__),tree)
        self.assertEqual(reused.__code__,new);self.assertEqual(ast.dump(tree),before)

    def test_preparation_guard_facade_is_graph_only_and_not_worker_or_code(self):
        routed=NS(load=object());calls=[]
        def graph(*args,**kwargs):calls.append(args);return routed,kwargs["instances"]
        with patch.object(MODULE,"graph_loader",side_effect=graph):
            graph_profile=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False,role="graph")
            worker=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False,role="worker")
            code=self.connected()
            self.assertEqual(calls,[])
            graph_profile.main.__globals__["loader_profile"](ROOT,graph_profile.envelope.namespace_bundle,NS(),ACCEPTANCE,NS())
            worker.main.__globals__["loader_profile"](ROOT,worker.envelope.namespace_bundle,NS(),ACCEPTANCE,NS())
        self.assertTrue(graph_profile.preparation_CPU_policy_active)
        self.assertFalse(worker.preparation_CPU_policy_active);self.assertFalse(code.preparation_CPU_policy_active);self.assertEqual(len(calls),1)
        with self.assertRaises(ValueError):MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,role="native")

    def test_real_graph_route_is_qualified_original_preparation_connection(self):
        calls=[]
        # Construction performs no Guard acquire, sampler call, or subprocess.
        with patch.object(MODULE,"graph_loader",wraps=MODULE.graph_loader) as graph:
            linked=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False,role="graph")
            linked.main.__globals__["loader_profile"](ROOT,linked.envelope.namespace_bundle,NS(),ACCEPTANCE,NS())
        graph.assert_called_once();self.assertEqual(linked.preparation_guard_instances,[])
        self.assertEqual(linked.main.__globals__["VERSION"],"v17")

    def test_graph_route_wraps_whole_profile_not_raw_source_loader(self):
        captured=[]
        def route(root,original,a,delivery,envelope,*,instances,tools):
            captured.append((original,envelope.namespace_bundle));return original,instances
        linked=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=True,role="graph")
        with patch.object(MODULE,"graph_loader",side_effect=route):
            result=linked.main.__globals__["loader_profile"](ROOT,linked.envelope.namespace_bundle,NS(),ACCEPTANCE,NS())
        self.assertIs(captured[0][0],captured[0][1]);self.assertIs(result,captured[0][0])
        self.assertIsNot(result.load,ENVELOPE.namespace_bundle.load);self.assertIsNot(result.load,linked.envelope.namespace_bundle.load)

    def test_graph_root_utils_guard_is_preparation_facade_not_legacy75(self):
        linked=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False,role="graph")
        original,_=ENVELOPE.namespace_bundle.load(ROOT,[MODULE.PRESSURE],{})
        actual,_=linked.envelope.namespace_bundle.load(ROOT,[MODULE.PRESSURE],{})
        self.assertNotEqual(actual.terminal_metadata_pressure_v1.guard_type.__code__,original.terminal_metadata_pressure_v1.guard_type.__code__)
        self.assertTrue(callable(actual.terminal_metadata_pressure_v1.summary));self.assertEqual(linked.preparation_guard_instances,[])

    def test_worker_root_guard_is_original_without_preparation_facade(self):
        linked=MODULE.connect(ROOT,ENVELOPE,ACCEPTANCE,DELIVERY,require_code=False,role="worker")
        original,_=ENVELOPE.namespace_bundle.load(ROOT,[MODULE.PRESSURE],{})
        actual,_=linked.envelope.namespace_bundle.load(ROOT,[MODULE.PRESSURE],{})
        self.assertEqual(actual.terminal_metadata_pressure_v1.guard_type.__code__,original.terminal_metadata_pressure_v1.guard_type.__code__)
        self.assertEqual(actual.terminal_metadata_pressure_v1.summary.__code__,original.terminal_metadata_pressure_v1.summary.__code__)
        self.assertEqual(linked.preparation_guard_instances,[])

    def test_projected_actual_worker_keeps_live_dependencies_not_an_old_snapshot(self):
        env=dict(__name__="p09_exact_current_queue_successor_runtime",reconstruct_worker_graph=lambda value:"old")
        exec(compile("def owned_worker_entry(task):\n return reconstruct_worker_graph(task)\n","tools/p09/current_queue_successor_runtime.py","exec"),env)
        fn=env["owned_worker_entry"]
        def literal(fn,mapping):return FunctionType(fn.__code__,dict(fn.__globals__),argdefs=fn.__defaults__,closure=fn.__closure__),dict(exact_entire_code_inverse=True)
        namespace=NS(literal_function=literal)
        MODULE.keep_worker_dependency_family(namespace);changed,proof=namespace.literal_function(fn,{})
        env["reconstruct_worker_graph"]=lambda value:"current"
        self.assertEqual(changed("task"),"current");self.assertIs(changed.__globals__,fn.__globals__)
        self.assertIs(changed.__code__,fn.__code__);self.assertTrue(proof["original_worker_live_dependency_family_retained"])
        before=namespace.literal_function;MODULE.keep_worker_dependency_family(namespace);self.assertIs(before,namespace.literal_function)

    def test_live_worker_fix_does_not_change_other_functions_or_accept_default_globals(self):
        def ordinary(value):return value
        def literal(fn,mapping):return FunctionType(fn.__code__,dict(fn.__globals__),argdefs=fn.__defaults__,closure=fn.__closure__),dict(exact_entire_code_inverse=True)
        namespace=NS(literal_function=literal);MODULE.keep_worker_dependency_family(namespace)
        result,proof=namespace.literal_function(ordinary,{})
        self.assertIsNot(result.__globals__,ordinary.__globals__);self.assertEqual(result(3),3)
        env=dict(__name__="default_unqualified",reconstruct_worker_graph=lambda value:None)
        exec(compile("def owned_worker_entry(task):\n return reconstruct_worker_graph(task)\n","tools/p09/current_queue_successor_runtime.py","exec"),env)
        with self.assertRaises(ValueError):namespace.literal_function(env["owned_worker_entry"],{})

    def private_runtime(self):
        env=dict(__name__="p09_exact_current_queue_successor_runtime")
        exec(compile("def reconstruct_worker_graph(task):\n return 'old'\ndef current_input_scope(*args):\n return 'scope'\ndef owned_worker_entry(task):\n return reconstruct_worker_graph(task)\n","tools/p09/current_queue_successor_runtime.py","exec"),env)
        worker=FunctionType(env["owned_worker_entry"].__code__,dict(env))
        current=dict(__name__="p09_exact_current_queue_successor_runtime")
        exec(compile("def reconstruct_worker_graph(task):\n return 'current'\n","tools/p09/current_queue_successor_runtime.py","exec"),current)
        return NS(owned_worker_entry=worker,reconstruct_worker_graph=current["reconstruct_worker_graph"],current_input_scope=env["current_input_scope"])

    def test_full_namespace_install_then_actual_worker_gets_final_public_functions(self):
        runtime=self.private_runtime();calls=[]
        def literal(fn,mapping):return fn,dict(exact_entire_code_inverse=True)
        def install(runtime):calls.append("whole-original-install");return "original-return"
        def retarget(runtime,path):calls.append(path);return "retarget-return"
        namespace=NS(literal_function=literal,install=install,retarget_worker=retarget)
        original=runtime.owned_worker_entry.__code__;MODULE.keep_worker_dependency_family(namespace)
        self.assertEqual(namespace.install(runtime),"original-return")
        self.assertEqual(namespace.retarget_worker(runtime,"new-entry"),"retarget-return")
        self.assertEqual(calls,["whole-original-install","new-entry"])
        self.assertIs(runtime.owned_worker_entry.__code__,original)
        self.assertIs(runtime.owned_worker_entry.__globals__["reconstruct_worker_graph"],runtime.reconstruct_worker_graph)
        self.assertEqual(runtime.owned_worker_entry("task"),"current")

    def test_dependency_sync_rejects_default_worker_and_unqualified_public_functions(self):
        runtime=self.private_runtime();runtime.reconstruct_worker_graph=lambda *args:None
        with self.assertRaises(ValueError):MODULE.synchronize_worker_dependencies(runtime)

    def test_final_binding_api_keeps_original_result_and_commits_latest_dependency(self):
        runtime=self.private_runtime();calls=[];result=("original-module","whole-original-proof")
        def connect(*items,**kwargs):calls.append((items,kwargs));return result
        connection=NS(binding_api=lambda *args,**kwargs:NS(connect=connect,unchanged="value"))
        MODULE.finish_binding_dependencies(connection,runtime)
        api=connection.binding_api("binding","policy");self.assertEqual(api.unchanged,"value")
        self.assertIs(api.connect("root",index=165),result);self.assertEqual(calls,[(('root',),dict(index=165))])
        self.assertIs(runtime.owned_worker_entry.__globals__["reconstruct_worker_graph"],runtime.reconstruct_worker_graph)
        before=connection.binding_api;MODULE.finish_binding_dependencies(connection,runtime);self.assertIs(connection.binding_api,before)
        with self.assertRaises(ValueError):MODULE.finish_binding_dependencies(connection,self.private_runtime())

    def test_metadata_code_history_extension_does_not_expand_graph_or_native_limits(self):
        for value in (1,8,9,16):self.assertEqual(MODULE.code_identifier(value),value)
        for value in (True,0,17,"9"):
            with self.assertRaises(ValueError):MODULE.code_identifier(value)
        with self.assertRaises(ValueError):MODULE.context(["--graph","--case","165","--run","8","--attempt","9"])
        self.assertEqual(MODULE.IDENTIFIERS["Native_physical_run"],8);self.assertFalse(MODULE.IDENTIFIERS["automatic_retry"])
        runtime=self.private_runtime();runtime.owned_worker_entry=lambda *args:None
        with self.assertRaises(ValueError):MODULE.synchronize_worker_dependencies(runtime)
