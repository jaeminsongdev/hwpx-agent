"""Read-only review and qualified acceptance adapters for explicit v2 wire.

Frozen v1 review/acceptance bodies and full validators remain. New adapter
witnesses are post-Native sources, never retrospectively part of its Frame.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_successor_wire_review_v2.py"
TEST="tools/p09/tests/test_current_queue_successor_wire_review_v2.py"
PINS=[dict(path="tools/p09/review_current_queue_successor.py",bytes=9381,
    sha256="c7ecfcae2e708d9d1de501b55fc55adb21844b7aa7648d2b876e119f51b8ad92"),
    dict(path="tools/p09/accept_current_queue_successor.py",bytes=7728,
    sha256="c199a3f47a7e7ec1426d6fd764628d773ab8b880b011e3c13f4ebe9d40c86990")]


def assembly_reader(reader):
    """Only frozen acceptance's bounded Sources lacks a live guard callback."""
    if callable(getattr(reader,"checkpoint",None)):return reader
    if (type(reader).__name__!="Sources" or
        set(vars(type(reader)))-{"__module__","__dict__","__weakref__","__doc__","__firstlineno__","__static_attributes__"} != {"root","json","pin"}
        or set(vars(reader)) or not callable(reader.json) or not callable(reader.pin)):
        raise ValueError("V2_ACCEPTANCE_EXACT_ASSEMBLY_READER_REQUIRED")
    return NS(root=reader.root,json=reader.json,pin=reader.pin,checkpoint=lambda:None)


def load(root,a,scope,bytes_policy,envelope,bridge):
    modules,proof=bridge.load(root,a,scope,bytes_policy,envelope)
    dispatch=modules.current_queue_successor_dispatch
    original=dispatch.current_namespaces
    def current_namespaces(q,*args,**kwargs):
        return original(assembly_reader(q),*args,**kwargs)
    original.__globals__["current_namespaces"]=current_namespaces
    dispatch.current_namespaces=current_namespaces
    names,sourceproof=envelope.namespace_bundle.load(root,PINS,{})
    reuse={**vars(modules),**vars(names)}
    for namespace in vars(names).values():bridge.bind_imports(namespace,reuse)
    review=names.review_current_queue_successor
    accept=names.accept_current_queue_successor
    bridge.graph_v2_paths(review,PINS[0])
    # Only the adapter/test witness filenames change. Native source expectations
    # are still built first from predecessor and sealed v2 declarations.
    for namespace in (review,accept):
        for fn in vars(namespace).values():
            if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
                fn.__globals__.update(SELF=SELF,TEST=TEST)
        namespace.SELF,namespace.TEST=SELF,TEST
    return review,accept,dict(v2_dependency_proof=proof,frozen_review_acceptance_source_proofs=sourceproof,
        original_whole_preparation_and_acceptance_bodies_retained=True,default_namespace_not_mutated=True,
        actual_review_or_acceptance_qualified=False)


def main():
    import argparse
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_queue_successor_wire_runtime_v2 as bridge
    review,accept,proof=load(c.ROOT,a,scope,bytes_policy,envelope,bridge)
    parser=argparse.ArgumentParser()
    for name in ("case","run","code-attempt","preflight-attempt","qualification-attempt","review-attempt","root-bytes"):
        parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--root-sha256",required=True)
    parser.add_argument("--acceptance-attempt",type=int)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument("--review",action="store_true");mode.add_argument("--accept",action="store_true")
    args=parser.parse_args()
    ctx=review.main.__globals__["current_queue_successor_dispatch"].context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt) if "current_queue_successor_dispatch" in review.main.__globals__ else None
    # Function-local imports do not create an exported context factory.
    if ctx is None:
        import current_queue_successor_dispatch as original_dispatch
        ctx=original_dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    root_pin=dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256)
    if args.review:return review.main(ctx,root_pin,args.review_attempt)
    if args.acceptance_attempt is None:parser.error("--accept requires --acceptance-attempt")
    return accept.main(ctx,root_pin,args.review_attempt,args.acceptance_attempt)


if __name__=="__main__":raise SystemExit(main())
