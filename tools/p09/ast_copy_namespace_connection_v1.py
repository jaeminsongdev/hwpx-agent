"""One private copy dependency for fresh namespace trees and helper bodies.

The complete original loader code/defaults/closure and all fresh source/hash/
AST predicates remain. No source/hash/AST cache, default-module mutation or
sys.modules hiding. Only import of stdlib copy inside this loader is routed.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/ast_copy_namespace_connection_v1.py"
TEST="tools/p09/tests/test_ast_copy_namespace_connection_v1.py"


def require(ok,label):
    if not ok:raise ValueError("AST_COPY_CONNECTION_"+label)


def connect(original,candidate):
    root=candidate.connect(original);fn=root.load;original_import=fn.__globals__["importlib"].import_module
    private_copy=fn.__globals__["copy"]
    require(private_copy.deepcopy is candidate.deepcopy,"SAME_QUALIFIED_AST_CLONER")
    def import_module(name,*args,**kwargs):
        if name=="copy" and not args and not kwargs:return private_copy
        return original_import(name,*args,**kwargs)
    library=NS(**{**vars(fn.__globals__["importlib"]),"import_module":import_module})
    env=dict(fn.__globals__,importlib=library)
    revised=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    revised.__kwdefaults__=fn.__kwdefaults__
    require(revised.__code__ is original.load.__code__ and revised.__defaults__ is original.load.__defaults__
        and revised.__closure__ is original.load.__closure__,"ENTIRE_ORIGINAL_LOADER_BODY_DEFAULTS_CLOSURE")
    return NS(**{**vars(original),"load":revised}),dict(root_and_private_helper_copy_dependency_connected=True,
        complete_original_loader_code_retained=True,default_copy_or_importlib_changed=False,
        byte_hash_AST_or_JSON_cache=False,Native_or_GO_authorized=False)


def envelope(original,loader):
    require(getattr(loader,"SELF",None)=="tools/p09/runtime_envelope_namespace_bundle_v1.py","ORIGINAL_LOADER_IDENTITY")
    return NS(**{**vars(original),"namespace_bundle":loader})


def invoke(original,proxy):
    """Whole worker/graph main, one explicit late envelope import dependency."""
    require(type(original) is FunctionType and original.__name__=="main"
        and original.__code__.co_filename.replace("\\","/").endswith("tools/p09/xz_unified_runtime_v1.py"),"EXACT_WHOLE_UNIFIED_MAIN")
    builtins=dict(original.__builtins__);prior=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:return proxy
        return prior(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    revised=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),
        argdefs=original.__defaults__,closure=original.__closure__)
    revised.__kwdefaults__=original.__kwdefaults__
    require(revised.__code__ is original.__code__ and revised.__defaults__ is original.__defaults__
        and revised.__closure__ is original.__closure__,"ENTIRE_UNIFIED_MAIN_CODE_DEFAULTS_CLOSURE")
    return revised()
