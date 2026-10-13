"""Explicit exclusive preflight slots; no automatic retry or checker reduction.

Only one output suffix changes. Restore it to recover the entire original
function code. Source/byte/final-hash/resource/product predicates remain intact.
"""
from pathlib import Path
from types import FunctionType

SELF="tools/p09/preflight_output_slot_v1.py"
TEST="tools/p09/tests/test_preflight_output_slot_v1.py"
OLD="-envelope-controller-run003-preflight029.v1.json"


def require(ok,code):
    if not ok:raise ValueError("PREFLIGHT_SLOT_"+code)


def suffix(sequence):
    require(type(sequence) is int and 30<=sequence<=999,"EXPLICIT_FRESH_SEQUENCE30_TO999")
    return f"-envelope-controller-run003-preflight{sequence:03}.v1.json"


def path(root,sequence):
    root=Path(root).absolute()
    return root/"implementation/p09/evidence"/f"p09-361-case158{suffix(sequence)}"


def ensure_fresh(root,sequence):
    root=Path(root).absolute();target=path(root,sequence)
    require(target.parent.is_dir(),"EXISTING_EVIDENCE_DIRECTORY")
    for parent in (target.parent,*target.parent.parents):
        require(not parent.is_symlink() and not parent.is_junction(),"DIRECT_OUTPUT_ANCESTORS")
        if parent==root:break
    else:raise ValueError("PREFLIGHT_SLOT_OUTPUT_OUTSIDE_ROOT")
    require(not target.exists() and not target.is_symlink() and not target.is_junction(),
        "EXCLUSIVE_OUTPUT_NOT_REUSED")
    return target


def project(original,sequence):
    require(type(original) is FunctionType,"ORIGINAL_FULL_PREFLIGHT_FUNCTION")
    new=suffix(sequence);code=original.__code__
    require(sum(type(x) is str and x==OLD for x in code.co_consts)==1,"ONE_ORIGINAL_OUTPUT_SUFFIX")
    revised=code.replace(co_consts=tuple(new if type(x) is str and x==OLD else x for x in code.co_consts))
    restored=revised.replace(co_consts=tuple(OLD if type(x) is str and x==new else x for x in revised.co_consts))
    require(restored==code,"ALL_ORIGINAL_PREFLIGHT_CODE_RESTORED")
    fn=FunctionType(revised,dict(original.__globals__),argdefs=original.__defaults__,closure=original.__closure__)
    fn.__kwdefaults__=original.__kwdefaults__
    return fn,dict(sequence=sequence,physical_product_run=3,changed_output_suffix_only=True,
        complete_original_code_restored_by_inverse=True,original_defaults_and_closure_retained=True,
        default_controller_namespace_mutated=False,automatic_retry_loop=False,
        whole_preflight_or_actual_product_qualified=False,GO_authorized=False)
