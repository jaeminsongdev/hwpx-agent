"""Whole qualified current oracle with independent successor declarations.

Do not derive required pins from the candidate's observations. Preserve all
checker bodies, physical byte/Frame evidence, source scope and resource limits.
"""
from types import FunctionType,SimpleNamespace as NS
import current_queue_successor_connections as metadata

SELF="tools/p09/current_queue_successor_oracle.py"
TEST="tools/p09/tests/test_current_queue_successor_oracle.py"


def clone_family(family):
    env=dict(family)
    for name,fn in family.items():
        if type(fn) is FunctionType and fn.__globals__ is family:
            env[name]=metadata.clone(fn,env)
    return env


def connect(legacy,graph,step,identity,inherited,checkpoint):
    """Connect only; no candidate, runtime dispatch or queue writer invoked."""
    checkpoint();index=step.index
    metadata.require(type(index) is int and 161<=index<=249 and type(step.before) is int and step.before==index-7,
        "CLOSED_WHOLE_ORACLE_CONTEXT")
    metadata.require(type(inherited) is dict and graph.binding.next_case==index,"EXACT_WHOLE_ORACLE_BINDING")
    scoped_validator=legacy.API.previous.scoped_validator
    required=scoped_validator.__globals__["base"].scope.pins(list(inherited.values()))
    original_validator=legacy.M.validator;original_full=legacy.M.validate_candidate
    family=original_validator.__globals__
    metadata.require(original_full.__globals__ is family,"ONE_ORIGINAL_WHOLE_VALIDATOR_FAMILY")
    env=clone_family(family);projectors=[]
    original_oracle=graph.full_oracle
    def projector(generator,*args,**kwargs):
        checkpoint()
        private=metadata.clone(generator,dict(generator.__globals__))
        factory=lambda raw,ctx,flat=True:(private,{})
        scoped,proof=scoped_validator(factory,required)(None,None)
        metadata.require(scoped.__code__ is generator.__code__ and scoped.__globals__ is not generator.__globals__,
            "ENTIRE_GENERATOR_PRIVATE_INDEPENDENT_SCOPE")
        execute,state=original_oracle.projector(scoped,*args,**kwargs)
        projectors.append(state)
        return execute,state
    oracle=NS(**{**vars(original_oracle),"projector":projector})
    current_graph=NS(**{**vars(graph),"full_oracle":oracle})
    original_window=family["window"]
    def window_connect(check):
        frozen,proof=original_window.connect(check)
        current=metadata.project(frozen,dict(frozen.__globals__),{160:index})
        return current,dict(proof,current_case=index,whole_strict_window_predicates_retained=True)
    env.update(SELF=SELF,TEST=TEST,base=NS(**{**vars(family["base"]),"CONFIG":step}),
        RETRY=identity,_checkpoint=checkpoint,graph_value=lambda:current_graph,
        window=NS(**{**vars(original_window),"connect":window_connect}))
    for name in ("only159","only160"):
        if name in family:env[name]=metadata.project(family[name],env,{160:index,153:step.before})
    env["validator"]=metadata.project(original_validator,env,{160:index})
    env["validate_candidate"]=metadata.project(original_full,env,{160:index})
    return NS(validator=env["validator"],validate_candidate=env["validate_candidate"],
        graph=current_graph,projectors=projectors,environment=env),dict(
        independent_declared_scope_not_current_observations=True,inherited_input_count=len(required),
        whole_original_validator_family_retained=True,current_metadata_entire_code_inverse=True,
        original_default_namespaces_and_observed_records_not_mutated=True,
        original_scope_cost_resource_and_strict_window_predicates_retained=True,
        actual_current_candidate_or_Native_or_product_qualified=False,queue_acceptance_called=False)


def qualify(index,run,attempt):
    """Actual independent declaration connection; no current candidate exists."""
    import io
    import json
    import os
    from pathlib import Path
    import re
    import sys
    import time
    import unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_runtime as runtime
    import current_queue_successor_binding as bindings
    import runtime_envelope_namespace_bundle_v1 as loader
    import owned_source_read_pressure as bytes_policy
    import case160_run007_controller as old
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    metadata.require(type(index) is int and 161<=index<=249 and type(run) is int and 2<=run<=8
        and type(attempt) is int and 1<=attempt<=8,"ORACLE_QUALIFICATION_CONTEXT")
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{index}-successor-oracle-connection{attempt:03}.v1.json"
    metadata.require(not output.exists(),"EXCLUSIVE_ORACLE_CONNECTION_REPORT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_SUCCESSOR_WHOLE_ORACLE_CONNECTION_NOT_ADOPTED",index=index,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,runtime.SELF,runtime.TEST,bindings.SELF,metadata.SELF,loader.SELF):q.pin(name)
        hint=q.json(f"implementation/p09/evidence/p09-361-case{index}-successor-worker-bootstrap{run:03}.v1.json")
        runtime.validate_worker_hint(hint,f"case{index}-current-r{run:03}-tests")
        actual,buffer=q._read(hint["capsule_pin"]["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,hint["capsule_pin"],"EXACT_CURRENT_WHOLE_ORACLE_CAPSULE")
        graph,decoder=runtime.reconstruct_worker_graph(c.ROOT,loader,scope,bytes_policy,hint,bytes(buffer),guard.check)
        step=hint["step"]
        authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
        a.fields(authority,dict(accepted_count_after=index-7,next_runtime_index=index,
            runtime_candidate_pin=step["prior_candidate_pin"],resource_cleanup_confirmed=True),"ACTUAL_PREDECESSOR_AUTHORITY_FOR_EXPECTATIONS")
        representation=prior["source_input_representation"]
        for pin in bindings.PINS+metadata.PINS+runtime.PINS:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_DECLARED_ORACLE_GRAPH_SOURCES")
        inherited=bindings.inherited_scope(scope,representation,authority["fresh_input_pins"],q.snapshots,guard.check)
        # Require every inherited original and current manifest; never read a
        # case161 candidate or its observed source_freeze to construct this.
        inherited=scope.extend(inherited,{hint["manifest_pin"]["path"]:hint["manifest_pin"]})
        a.exact(q.pin(hint["manifest_pin"]["path"]),hint["manifest_pin"],"REAL_DECLARED_ORACLE_MANIFEST")
        inherited=scope.extend(inherited,q.snapshots)
        inherited,aliases=graph.binding.semantic_union(inherited,guard.check)
        old.old.base.configure(index)
        template,identity,factory_proof=runtime.connect_factory(c.ROOT,loader,old.old.prior,index,run,guard.check)
        current,proof=connect(old.CURRENT,graph,old.old.base.CONFIG,identity,inherited,guard.check)
        current.environment["only159"]()
        suite=unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_current_queue_successor_oracle")
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        out["contracts"]=contracts;a.exact(contracts,dict(run=5,errors=0,failures=0,skipped=0),"ALL_INDEPENDENT_ORACLE_CONNECTION_CONTRACTS")
        q.finish();guard.check(force=True)
        out.update(state="CONNECTED_WHOLE_SUCCESSOR_ORACLE_WITH_INDEPENDENT_DECLARATIONS_NOT_ACTUAL_CANDIDATE_OR_GO",
            connection_proof=proof,inherited_semantic_input_count=len(inherited),candidate_record_used_to_derive_scope=False,
            current_candidate_or_checker_executed=False,queue_acceptance_called=False,
            new_whole_CODE_closure_cost_and_preflight_still_required=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    metadata.require(guard.cleanup,"ORACLE_CONNECTION_CLEANUP")
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    metadata.require(0<len(raw)<=262144,"BOUNDED_ORACLE_CONNECTION_REPORT")
    for parent in (output.parent,*output.parent.parents):
        metadata.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_ORACLE_REPORT_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:metadata.require(stream.write(raw)==len(raw),"ALL_ORACLE_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","contracts","inherited_semantic_input_count","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("CONNECTED_") else 1


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();raise SystemExit(qualify(args.case,args.run,args.attempt))
