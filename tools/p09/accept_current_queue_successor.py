"""Successor facade for the unchanged qualified whole acceptance engine.

No product replay or retrospective Native witnesses. Full candidate preparation
precedes independent-review and facade witnesses. Canonical output is exclusive.
"""
from pathlib import Path
from types import FunctionType,ModuleType,SimpleNamespace as NS
import sys

SELF="tools/p09/accept_current_queue_successor.py"
TEST="tools/p09/tests/test_accept_current_queue_successor.py"


def isolate_review_config(old):
    """Fresh immutable review context without resetting the configured runtime."""
    original=old.old.base
    family=original.configure.__globals__
    module=ModuleType("p09_private_acceptance_review_config")
    module.__dict__.update(family);module.__dict__.update(vars(original));module.__dict__.update(CONFIG=None)
    for name,fn in tuple(module.__dict__.items()):
        if type(fn) is FunctionType and fn.__globals__ is family:
            projected=FunctionType(fn.__code__,module.__dict__,argdefs=fn.__defaults__,closure=fn.__closure__)
            projected.__kwdefaults__=fn.__kwdefaults__
            if projected.__code__ is not fn.__code__:raise ValueError("ACCEPT_REVIEW_CONFIG_ORIGINAL_CODE")
            module.__dict__[name]=projected
    return NS(**{**vars(old),"old":NS(**{**vars(old.old),"base":module})})


def facade(m,identity,index):
    m.require(type(index) is int and 161<=index<=249 and m.base.CONFIG is not None
        and m.base.CONFIG.index==index and m.base.CONFIG.before==index-7,"EXACT_SUCCESSOR_ACCEPTANCE_CONTEXT")
    source=m.old.API.accept.__globals__["source"]
    return NS(**{**vars(m),"source":NS(**{**vars(source),"root_path":identity.root_path}),
        "RETRY":identity,"SELF":SELF,"TEST":TEST})


def validated_prepare(q,root_pin,prepare,review_path,a):
    # Review/facade witnesses never seed the expected Native scope.
    result=prepare(q,root_pin)
    proof=q.json(review_path)
    a.fields(proof,dict(state="PASS_SUCCESSOR_INDEPENDENT_WHOLE_REVIEW_NOT_QUEUE_OR_GATE",
        runtime_pin=root_pin,accepted_count_delta=0,product_or_Native_reexecuted=False,
        queue_acceptance_called=False,cleanup_confirmed=True,reviewer_not_retroactive_Native_input=True),
        "ACCEPT_QUALIFIED_SUCCESSOR_WHOLE_REVIEW")
    a.require(proof["fresh_inputs"]==proof["final_fresh_hashes"] and proof["fresh_inputs"]>0,
        "ACCEPT_ALL_REVIEW_HASHES_CLOSED")
    for pin in proof["reviewer_source_pins"]:a.exact(q.pin(pin["path"]),pin,"ACCEPT_UNCHANGED_REVIEW_CODE_AND_ROOT")
    q.pin(SELF);q.pin(TEST)
    return result


def main(ctx,root_pin,review_attempt,attempt):
    import hashlib,io,json,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import current_queue_successor_dispatch as dispatch
    import current_queue_successor_oracle as oracle
    import review_current_queue_successor as review
    import optimized_current_queue_acceptance_v3 as acceptance
    import flat_current_queue_envelope_runtime_v25 as envelope
    names,proof=envelope.namespace_bundle.load(c.ROOT,[dispatch.ORIGINAL_CONTROLLER_PIN],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    old=names.case160_run007_controller
    a.require(type(review_attempt) is int and 1<=review_attempt<=8 and type(attempt) is int and 1<=attempt<=8,
        "ACCEPT_CLOSED_ATTEMPTS")
    a.exact(root_pin["path"],ctx.root,"ACCEPT_EXACT_CURRENT_ROOT")
    scope.pins([root_pin])
    canonical=f"implementation/p09/evidence/p09-361-case{ctx.index}-current-epoch-accept001.v1.json"
    diagnostic=f"implementation/p09/evidence/p09-361-case{ctx.index}-optimized-acceptance-attempt{attempt:03}.v2.json"
    a.require(not (c.ROOT/canonical).exists() and not (c.ROOT/diagnostic).exists(),"ACCEPT_NO_CANONICAL_OR_DIAGNOSTIC_REPLAY")
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_accept_current_queue_successor"))
    a.exact(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
        dict(run=3,errors=0,failures=0,skipped=0),"ACCEPT_ALL_FACADE_CONTRACTS")
    # Assemble only; the original acceptance engine owns the sole live guard.
    class Sources:
        root=c.ROOT
        def json(self,name):
            path=self.root/name;old.old.base.stable.stable.prior.build.direct_path(path,file_required=True)
            with path.open("rb") as stream:raw=stream.read(262145)
            a.require(0<len(raw)<=262144,"ACCEPT_BOUNDED_ASSEMBLY_JSON")
            return json.loads(raw.decode("utf-8"),object_pairs_hook=old.old.base.unique)
        def pin(self,name):
            path=self.root/name
            old.old.base.stable.stable.prior.build.direct_path(path,file_required=True)
            with path.open("rb") as stream:raw=stream.read(65537)
            a.require(0<len(raw)<=65536,"ACCEPT_BOUNDED_ASSEMBLY_SOURCE")
            return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    sources=Sources();qualification=sources.json(ctx.qualification)
    runtime,controller,proof=dispatch.current_namespaces(sources,ctx,a,old,scope,bytes_policy,qualification)
    old.old.base.configure(ctx.index)
    template,identity,proof=runtime.connect_factory(c.ROOT,old.old.namespace_bundle,old.old.prior,ctx.index,ctx.run,lambda:None)
    current=old.CURRENT.M
    prepared_runtime=facade(current,identity,ctx.index)
    review_path=f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-whole-review-run{ctx.run:03}-attempt{review_attempt:03}.v1.json"
    def complete(q,pin):
        private=isolate_review_config(old)
        declaration=q.json(ctx.qualification)
        return review.prepare(q,ctx,declaration,private,a,runtime,scope,bytes_policy,dispatch,oracle,pin)
    prepared_runtime.API=NS(**{**vars(current.API),"prepare":lambda q,pin:validated_prepare(q,pin,complete,review_path,a),
        "accept":current.old.API.accept})
    def pin(name):
        path=c.ROOT/name
        old.old.base.stable.stable.prior.build.direct_path(path,file_required=True)
        with path.open("rb") as stream:raw=stream.read(262145)
        a.require(0<len(raw)<=262144,"ACCEPT_BOUNDED_QUALIFICATION_BOOTSTRAP")
        return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    row,receipt=acceptance.run(prepared_runtime,root_pin,pin(acceptance.prior.prior.QUAL_PATH),
        pin(acceptance.prior.QUAL_PATH),pin(acceptance.QUAL_PATH),diagnostic)
    print(json.dumps(dict(state=row["state"],error_code=row.get("error_code"),diagnostic_pin=receipt,
        accepted_count_delta=row.get("accepted_count_delta"),cleanup_confirmed=row.get("cleanup_confirmed"))))
    return 0 if row["state"].startswith("PASS_") and row.get("cleanup_confirmed") is True else 1


if __name__=="__main__":
    import argparse
    import current_queue_successor_dispatch as dispatch
    parser=argparse.ArgumentParser()
    for name in ("case","run","code-attempt","preflight-attempt","qualification-attempt","review-attempt","acceptance-attempt","root-bytes"):
        parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--root-sha256",required=True);args=parser.parse_args()
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    raise SystemExit(main(ctx,dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256),args.review_attempt,args.acceptance_attempt))
