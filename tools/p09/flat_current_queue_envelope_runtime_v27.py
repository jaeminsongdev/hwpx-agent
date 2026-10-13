"""Exact159 controller with fresh private helper graph and original bound64.
All raw helper/controller/test sources remain pinned inputs. No actual project
module is imported and then hidden, and no sys.modules entry is changed.
"""
import argparse
import json
import re
import sys
from types import CodeType,FunctionType,SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF="tools/p09/flat_current_queue_envelope_runtime_v27.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v27.py"
RAW_PINS=[{"path":"tools/p09/runtime_successor_binding_v1.py","bytes":6084,"sha256":"cc63a2d635e9b4047537b27641f3cb8c67184e7a3a48f4b1fff47db64ea4e793"},{"path":"tools/p09/runtime_successor_manifest_v1.py","bytes":5867,"sha256":"ca0cd27ba5a7d94e91160038117311228dadacfce5410dd5eb239b1fa55b6dac"},{"path":"tools/p09/runtime_successor_worker_capsule_v1.py","bytes":3108,"sha256":"1755225e895ec4aadf8a2b86f912f936328f49060fc06a487eb4c45231bbc5f9"},{"path":"tools/p09/successor_runtime_graph_v1.py","bytes":2564,"sha256":"d02dc0f8d169a50520380eed83852c7da03c0a96ea8776dc4fcc6bc82ebfa3ea"},{"path":"tools/p09/current_envelope_acceptance_prepare_v1.py","bytes":2471,"sha256":"9f744ef75ad6953e84ee62b6398c285c3a421ebb20266e90062ff00a555cc98a"},{"path":"tools/p09/isolated_predecessor158_prepare_v1.py","bytes":5750,"sha256":"80806d22031114f79f844a2838daad7e06ee1e192bf403574316fe05473c6ea3"},{"path":"tools/p09/successor_current_binding_v1.py","bytes":4854,"sha256":"63978923382628a15959758a7d61fa101ea4d8d4ee66dbc38fbc727f54a7b3bc"},{"path":"tools/p09/successor_strict_window_v1.py","bytes":1567,"sha256":"06fe3c081cef9d4a688719dfaf9b5daad5d1af78aacc5dcb3946de088a13e198"},{"path":"tools/p09/successor_bounded_graph_bootstrap_v1.py","bytes":2972,"sha256":"1d8c61aba33d2eb5a722da6c473e64a775202685233813a176f797391604767c"},{"path":"tools/p09/flat_current_queue_envelope_runtime_v26.py","bytes":13574,"sha256":"9702e7a97bcfe5e459489d180e56d5ac533f72bf46996d3505301125544038ef"}]
RAW_TEST_PIN={"path":"tools/p09/tests/test_flat_current_queue_envelope_runtime_v26.py","bytes":5642,"sha256":"07b12a79263cc1d20d21f5cc19a88924cf47e0a6cadd61f42dcb479bdbae0858"}
SOURCE_NAMESPACES,SOURCE_PROOFS=old.namespace_bundle.load(old.c.ROOT,RAW_PINS,
    {"flat_current_queue_envelope_runtime_v25":old})
_original=SOURCE_NAMESPACES.flat_current_queue_envelope_runtime_v26
_env=_original.only159.__globals__
_env.update(SELF=SELF,TEST=TEST,SCHEMA="hwpx-agent.p09-envelope-current-controller/v27",
    DATA="implementation/p09/evidence/p09-361-case159-envelope-controller-data035.v1.json",
    QUAL="implementation/p09/evidence/p09-361-case159-namespace-controller-code14-r748.v1.json",
    QUAL_STATE="PASS_CURRENT159_NAMESPACE_CONTROLLER_CODE14_ORIGINAL_BOUND64_NOT_NATIVE_OR_GO",
    PREFLIGHT="implementation/p09/evidence/p09-361-case159-envelope-controller-preflight035.v1.json")
_original.API.run_owned.__globals__.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),
    QUAL_PATH=_env["QUAL"])
# Exact metadata-only new destination; inverse must restore original code.
_fn=_env["preflight_projection"];_code=_fn.__code__
_old="-envelope-controller-preflight034.v1.json";_new="-envelope-controller-preflight035.v1.json"
old.a.require(sum(type(x) is str and x==_old for x in _code.co_consts)==1,"ONE_NEW159_PREFLIGHT_METADATA")
_changed=_code.replace(co_consts=tuple(_new if type(x) is str and x==_old else x for x in _code.co_consts))
old.a.require(_changed.replace(co_consts=_code.co_consts)==_code,"ORIGINAL_FULL159_PREFLIGHT_CODE_RESTORED")
_projected=FunctionType(_changed,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_projected.__kwdefaults__=_fn.__kwdefaults__;_env["preflight_projection"]=_projected
M=NS(**_env)
# Every raw file must be included before whole preflight/Native/GO.
_raw_own=M._original_own_inputs
def own_inputs(q):
    for pin in RAW_PINS+[RAW_TEST_PIN]:old.a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT159_RAW_CONTROLLER_HELPERS_AND_TEST_INPUTS")
    q.pin(SELF);q.pin(TEST)
    return _raw_own(q)
_env["own_inputs"],ADMISSION_COUNTS=old.admission_once.connect(own_inputs)
M.own_inputs=_env["own_inputs"];M.API.own_inputs=M.own_inputs
M._original_own_inputs=own_inputs
M.API.run_owned.__globals__["own_inputs"]=M.own_inputs

def test_code_projection(code,reverse=False):
    before,after=(_new,_old) if reverse else (_old,_new)
    constants=tuple(test_code_projection(x,reverse) if type(x) is CodeType else after
        if type(x) is str and x==before else x for x in code.co_consts)
    return code.replace(co_consts=constants)

def test_namespace():
    ns,proof=old.namespace_bundle.load(old.c.ROOT,[RAW_TEST_PIN],
        {"flat_current_queue_envelope_runtime_v26":M})
    module=ns.test_flat_current_queue_envelope_runtime_v26
    cls=module.Tests;fn=cls.test_original_whole_preflight_code_retained_except_destination
    revised=test_code_projection(fn.__code__)
    old.a.require(test_code_projection(revised,True)==fn.__code__,"ORIGINAL_ALL_CONTROLLER_TEST_CODE_RESTORED")
    new=FunctionType(revised,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
    new.__kwdefaults__=fn.__kwdefaults__
    cls.test_original_whole_preflight_code_retained_except_destination=new
    return module,proof

if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]));raise SystemExit(M.worker(sys.argv[3]))
        p=argparse.ArgumentParser();p.add_argument("--case",type=int,required=True)
        p.add_argument("--run",type=int);p.add_argument("--preflight",action="store_true")
        args=p.parse_args();M.base.configure(args.case);M.only159()
        M.require((args.run is not None)!=args.preflight,"EXACTLY_ONE_MODE")
        raise SystemExit(M.preflight() if args.preflight else M.run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        label=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V27_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=label)));raise SystemExit(2) from None
