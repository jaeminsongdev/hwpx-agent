"""Exact source graph in private namespaces, not hidden imported modules.

Every non-import AST node remains, in its original order. Import aliases are
resolved explicitly; every source pin still belongs to the full input scope.
No sys.modules entry is removed or masked and no default module is mutated.
"""
import ast
import copy
import hashlib
import importlib
from types import SimpleNamespace as NS

SELF="tools/p09/runtime_envelope_namespace_bundle_v1.py"


def require(ok,label):
    if not ok:raise ValueError("ENVELOPE_NAMESPACE_"+label)


def load(root,pins,reuse):
    require(type(pins) is list and type(reuse) is dict,"EXPLICIT_DEPENDENCIES")
    names={p["path"].rsplit("/",1)[-1][:-3]:p for p in pins}
    require(len(names)==len(pins) and 0<len(names)<=16,"CLOSED_GRAPH_SIZE")
    built={};building=set();proof=[]
    def dependency(name):
        if name in reuse:return reuse[name]
        if name in names:return namespace(name)
        # The graph must not silently import another project helper.
        module=importlib.import_module(name)
        filename=getattr(module,"__file__",None)
        if filename:
            from pathlib import Path
            require(not Path(filename).absolute().is_relative_to(root/"tools/p09"),"UNDECLARED_PROJECT_IMPORT")
        return module
    def namespace(name):
        if name in built:return built[name]
        require(name not in building,"NO_CIRCULAR_RAW_NAMESPACE")
        building.add(name);pin=names[name];path=root/pin["path"]
        require(type(pin["bytes"]) is int and 0<pin["bytes"]<=65536,"BOUNDED_SOURCE")
        with path.open("rb") as stream:raw=stream.read(pin["bytes"]+1)
        require(len(raw)==pin["bytes"] and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_SOURCE_PIN")
        tree=ast.parse(raw.decode("utf-8"));env=dict(__name__="p09_exact_"+name,__file__=pin["path"])
        nodes=[]
        for node in tree.body:
            if isinstance(node,ast.Import):
                for alias in node.names:
                    require("." not in alias.name or alias.asname is not None,"EXPLICIT_DOTTED_ALIAS")
                    env[alias.asname or alias.name]=dependency(alias.name)
            elif isinstance(node,ast.ImportFrom):
                require(node.level==0 and node.module is not None,"ABSOLUTE_IMPORT_DECLARATION")
                module=dependency(node.module)
                for alias in node.names:
                    require(alias.name!="*","NO_WILDCARD_IMPORT")
                    env[alias.asname or alias.name]=getattr(module,alias.name)
            else:nodes.append(copy.deepcopy(node))
        original=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
        require([ast.dump(n,include_attributes=False) for n in nodes]==
            [ast.dump(n,include_attributes=False) for n in original],"ALL_NON_IMPORT_AST_RETAINED")
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),pin["path"],"exec"),env)
        result=NS(**env);built[name]=result;building.remove(name)
        proof.append(dict(source_pin=pin,original_function_class_constants_and_initialization_AST_retained=True,
            actual_module_imported_or_sys_modules_hidden=False))
        return result
    for name in names:namespace(name)
    return NS(**built),proof
