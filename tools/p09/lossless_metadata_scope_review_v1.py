"""Post-Native review: sealed metadata scope is not the full Frame scope.

No Native/product entry. Frozen runtime bytes, full Frame validation, physical
accounting, decoder limits and final fresh hashes remain mandatory.
"""
import ast
import copy
import hashlib
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/lossless_metadata_scope_review_v1.py"
TEST="tools/p09/tests/test_lossless_metadata_scope_review_v1.py"
V4=dict(path="tools/p09/current_queue_successor_lossless_runtime_v4.py",bytes=18227,
    sha256="8ff8d105e753e2727b7fe4294f1e2b6fe6d670bd9d12e69afac5946888602db8")
SCRATCH_PINS=[dict(path="tools/p09/reusable_audit_chunk_v1.py",bytes=8088,
    sha256="1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75"),
    dict(path="tools/p09/tests/test_reusable_audit_chunk_v1.py",bytes=10148,
    sha256="60af53923c129d9f67774b8347a5e7df6aef85ea1c30cd9e65378e4a37a5a399")]


def require(ok,label):
    if not ok:raise ValueError("METADATA_SCOPE_REVIEW_"+label)


def declared_metadata(binding,preflight,qualification,a):
    """Two sealed pre-execution declarations; candidate never an input."""
    descriptors=binding.descriptors()
    mapping={d["semantic_original_pin"]["path"]:d["semantic_original_pin"] for d in descriptors}
    require(len(mapping)==len(descriptors),"UNIQUE_FULL_FRAME_MAPPINGS")
    def declared(pins):
        require(type(pins) is list,"SEALED_PIN_LIST")
        names={p["path"]:p for p in pins}
        require(len(names)==len(pins),"UNIQUE_SEALED_PINS")
        result={n:p for n,p in names.items() if n in mapping}
        for n,p in result.items():a.exact(p,mapping[n],"SEALED_METADATA_EXACT_SEMANTIC_PIN")
        return result
    pref=declared(preflight["current_source_pins"])
    qual=declared(qualification["source_pins"])
    a.exact(pref,qual,"SAME_PREFLIGHT_AND_ENTRY_METADATA_DECLARATIONS")
    require(0<len(pref)<=len(mapping),"NONEMPTY_SEALED_METADATA_SCOPE")
    return frozenset(pref)


def project_accounting(raw,environment,expected_metadata):
    """Exactly one predicate correction; all other v4 checks retained."""
    require(type(raw) is bytes and len(raw)==V4["bytes"] and
        hashlib.sha256(raw).hexdigest()==V4["sha256"],"EXACT_FROZEN_V4")
    nodes=[n for n in ast.parse(raw.decode("utf-8")).body
        if isinstance(n,ast.FunctionDef) and n.name=="validate_accounting"]
    require(len(nodes)==1,"ONE_FULL_ACCOUNTING_BODY")
    original=nodes[0];changed=copy.deepcopy(original);matches=[]
    for node in ast.walk(changed):
        if isinstance(node,ast.Compare) and ast.dump(node,include_attributes=False)==ast.dump(
            ast.parse("set(counts)==set(expected)",mode="eval").body,include_attributes=False):
            matches.append(node)
    require(len(matches)==1,"ONE_METADATA_NAME_PREDICATE")
    matches[0].comparators=[ast.Name(id="expected_metadata",ctx=ast.Load())]
    inverse=copy.deepcopy(changed)
    replacements=[n for n in ast.walk(inverse) if isinstance(n,ast.Compare) and
        len(n.comparators)==1 and isinstance(n.comparators[0],ast.Name) and n.comparators[0].id=="expected_metadata"]
    require(len(replacements)==1,"ONE_INVERSE_PREDICATE")
    replacements[0].comparators=[ast.parse("set(expected)",mode="eval").body]
    require(ast.dump(inverse,include_attributes=False)==ast.dump(original,include_attributes=False),"WHOLE_ACCOUNTING_INVERSE")
    env=dict(environment,expected_metadata=set(expected_metadata))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),SELF,"exec"),env)
    return env["validate_accounting"]


def connect_review(v4,raw,ctx):
    """Private checker only; declaration populated before original prepare."""
    state={};original=v4.validate_accounting
    def checked(row,binding,a):
        require(set(state)=={"preflight","qualification"},"DECLARATIONS_BEFORE_CANDIDATE")
        names=declared_metadata(binding,state["preflight"],state["qualification"],a)
        project_accounting(raw,original.__globals__,names)(row,binding,a)
        actual={p["path"] for p in row["bootstrap_metadata"]["input_pins"] if p["path"] in
            {d["semantic_original_pin"]["path"] for d in binding.descriptors()}}
        require(actual==set(names),"ALL_SEALED_METADATA_READS_ACTUALLY_OBSERVED")
        return True
    original.__globals__["validate_accounting"]=checked;v4.validate_accounting=checked
    def wrap(reviewer,contracts,scratch,a):
        original_prepare=reviewer.prepare
        def prepare(q,*args,**kwargs):
            # Original dispatch.admit then revalidates these exact receipts and
            # every declared source before its whole candidate preparation.
            state.clear();state.update(preflight=q.json(ctx.preflight),qualification=q.json(ctx.qualification))
            row,listing,evidence,proof=original_prepare(q,*args,**kwargs)
            # Only AFTER the whole Native expectations/checker are closed.
            for pin in SCRATCH_PINS+[scratch.ORIGINAL_PIN]:
                a.exact(q.pin(pin["path"]),pin,"CURRENT_POST_NATIVE_REVIEW_SCRATCH_SOURCES")
            return row,listing,evidence,dict(proof,sealed_metadata_scope_review=dict(
                contracts=contracts,expected_metadata_names=len(row["bootstrap_metadata"]["early_pressure"]
                    ["explicit_fresh_lossless_metadata"]["semantic_read_counts"]),
                original_full_Frame_scope_and_both_boundaries_retained=True,
                expectations_from_two_sealed_preexecution_declarations=True,
                entire_other_v4_accounting_checks_retained=True,
                runtime_source_not_modified_or_reexecuted=True,
                post_Native_review_workspace=scratch.summary(q)))
        original_prepare.__globals__.update(prepare=prepare,SELF=SELF,TEST=TEST)
        reviewer.prepare=prepare
    return wrap


def main():
    import argparse,io,sys,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","code-attempt","preflight-attempt","qualification-attempt","adoption-attempt","review-attempt","root-bytes"):
        parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--root-sha256",required=True);parser.add_argument("--acceptance-attempt",type=int)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review",action="store_true");mode.add_argument("--accept",action="store_true")
    args=parser.parse_args()
    require(args.case==164 and args.run==6,"EXACT_REVIEWED_EPOCH")
    if args.accept:require(args.acceptance_attempt is not None,"EXPLICIT_ACCEPTANCE_ATTEMPT")
    # Unit contracts only; no fixture is ever a Native or queue success.
    import reusable_audit_chunk_v1 as scratch
    from tests import test_reusable_audit_chunk_v1 as scratch_tests
    scratch_raw=(c.ROOT/scratch.ORIGINAL_PIN["path"]).read_bytes()
    scratch_tests.SOURCE_BYTES=scratch_raw
    suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromName("tests.test_lossless_metadata_scope_review_v1"),
        unittest.defaultTestLoader.loadTestsFromModule(scratch_tests)))
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
    a.exact(contracts,dict(run=24,errors=0,failures=0,skipped=0),"ALL_METADATA_SCOPE_REVIEW_CONTRACTS")
    names,proof=envelope.namespace_bundle.load(c.ROOT,[V4],{})
    v4=names.current_queue_successor_lossless_runtime_v4
    components,proof=envelope.namespace_bundle.load(c.ROOT,v4.PINS,{})
    # The private source loader verifies V4. The exact AST projector rechecks it.
    raw=(c.ROOT/V4["path"]).read_bytes()
    qualification=f"implementation/p09/evidence/p09-361-case{args.case}-lossless-v4-adoption-code{args.adoption_attempt:03}.v1.json"
    ctx=NS(index=args.case,run=args.run,
        preflight=f"implementation/p09/evidence/p09-361-case{args.case}-successor-preflight-run{args.run:03}-attempt{args.preflight_attempt:03}.v1.json",
        qualification=f"implementation/p09/evidence/p09-361-case{args.case}-successor-dispatch-qualification-run{args.run:03}-attempt{args.qualification_attempt:03}.v1.json")
    wrap=connect_review(v4,raw,ctx)
    modules,bridge,oracle=v4.load(c.ROOT,a,scope,bytes_policy,envelope,components,qualification)
    ctx=modules.current_queue_successor_dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    retry=components.current_queue_successor_retry_runtime_v3
    adapters,proof=envelope.namespace_bundle.load(c.ROOT,[retry.REVIEW],{})
    facade=NS(**{**vars(bridge),"load":lambda root,aa,ss,bb,ee:(v4.load(root,aa,ss,bb,ee,components,qualification)[0],{})})
    reviewer,acceptor,proof=adapters.current_queue_successor_wire_review_v2.load(c.ROOT,a,scope,bytes_policy,envelope,facade)
    v4.override_import(reviewer,"current_queue_successor_oracle",oracle)
    v4.override_import(acceptor,"current_queue_successor_oracle",oracle)
    reader,reader_proof=scratch.reader_type(a.AcceptanceReader,scratch_raw)
    review_api=NS(**{**vars(a),"AcceptanceReader":reader})
    v4.override_import(reviewer,"accept_case112_current_epoch",review_api)
    # Default API/Native reader unchanged. Every original review wrapper and
    # closing byte pass remains; only its leaf allocates one reusable 64KiB.
    wrap(reviewer,contracts,scratch,a)
    # Post-Native witnesses; never injected into Native's declared Frame.
    for fn in vars(acceptor).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__.update(SELF=SELF,TEST=TEST)
    root_pin=dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256)
    if args.review:return reviewer.main(ctx,root_pin,args.review_attempt)
    return acceptor.main(ctx,root_pin,args.review_attempt,args.acceptance_attempt)


if __name__=="__main__":raise SystemExit(main())
