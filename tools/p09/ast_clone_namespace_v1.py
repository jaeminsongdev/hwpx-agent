"""Fresh-source namespace loader with a specialized independent AST copy.

No source/byte/hash/JSON/AST cache. The entire existing loader bytecode and
fresh file/hash/import/AST predicates remain; only its copy dependency changes.
Not installed into a default module or qualified worker by this library.
"""
import ast
import copy
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/ast_clone_namespace_v1.py"
TEST="tools/p09/tests/test_ast_clone_namespace_v1.py"
SOURCE=dict(path="tools/p09/runtime_envelope_namespace_bundle_v1.py",bytes=3320,
    sha256="385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62")
ATOMIC=frozenset((str,int,float,complex,bytes,bool,type(None),type(Ellipsis)))


def require(ok,label):
    if not ok:raise ValueError("AST_CLONE_NAMESPACE_"+label)


def deepcopy(value,memo=None):
    """Preserve fresh AST dictionaries, locations, attributes and graph aliases."""
    if memo is None:memo={}
    identity=id(value)
    if identity in memo:return memo[identity]
    kind=type(value)
    if kind in ATOMIC:return value
    if isinstance(value,ast.AST):
        result=kind.__new__(kind);memo[identity]=result
        result.__dict__.update({name:deepcopy(item,memo) for name,item in vars(value).items()})
        return result
    if kind is list:
        result=[];memo[identity]=result;result.extend(deepcopy(item,memo) for item in value);return result
    if kind is dict:
        result={};memo[identity]=result
        for key,item in value.items():result[deepcopy(key,memo)]=deepcopy(item,memo)
        return result
    # Non-AST custom values and tuple cycles keep the standard semantics.
    return copy.deepcopy(value,memo)


def connect(original):
    fn=original.load
    require(original.SELF==SOURCE["path"] and type(fn) is FunctionType
        and fn.__code__.co_filename.replace("\\","/").endswith(SOURCE["path"]),"EXACT_ORIGINAL_NAMESPACE_LOADER")
    env=dict(fn.__globals__,copy=NS(**{**vars(fn.__globals__["copy"]),"deepcopy":deepcopy}))
    revised=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    revised.__kwdefaults__=fn.__kwdefaults__
    require(revised.__code__ is fn.__code__ and revised.__defaults__ is fn.__defaults__ and revised.__closure__ is fn.__closure__,"WHOLE_ORIGINAL_LOADER_BODY")
    return NS(**{**vars(original),"load":revised})
