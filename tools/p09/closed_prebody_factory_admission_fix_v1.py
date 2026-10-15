"""Bind the frozen V6 factory import before its reader is constructed.

Preserve sealed graph/source files. The facade cannot admit a descriptor until
the actual stage reader has completed V6's full original-source verification.
No Native, review, acceptance, GO, or protection setting is enabled here.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

SELF="tools/p09/closed_prebody_factory_admission_fix_v1.py"
V6=dict(path="tools/p09/current_queue_closed_metadata_runtime_v6.py",bytes=13606,
    sha256="f0bae39351d26983cb7090b4b1593c28eceabef0dd57c54d5db03d7238ab7b93")


def require(ok,label):
    if not ok:raise ValueError("CLOSED_FACTORY_ADMISSION_"+label)


def load(root,a,scope,bytes_policy,envelope,qualification_path,*,worker=False,ctx=None):
    sources,_=envelope.namespace_bundle.load(root,[V6],{})
    v6=sources.current_queue_closed_metadata_runtime_v6
    readers=[]
    class Reader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.pin(SELF);a.exact(self.pin(V6["path"]),V6,"FROZEN_PREPARED_ENTRY_SOURCE")
            readers.append(self)
    api=NS(**{**vars(a),"AcceptanceReader":Reader})
    linked=v6.load(root,api,scope,bytes_policy,envelope,qualification_path,worker=worker,ctx=ctx)
    if not worker:
        bindings=linked.modules.current_queue_successor_binding
        def connect(*args,**kwargs):
            require(bool(readers),"ACTUAL_PARENT_READER_REQUIRED")
            policy=getattr(readers[-1],"closed_source_policy",None)
            require(type(policy) is linked.alias.VerifiedPolicy,"FRESH_SOURCE_ADMISSION_REQUIRED_BEFORE_BINDING")
            return linked.connection.binding_api(bindings,linked.alias,policy).connect(*args,**kwargs)
        facade=NS(**{**vars(bindings),"connect":connect})
        linked.v4.override_import(linked.modules.current_queue_successor_runtime,"current_queue_successor_binding",facade)
    return linked


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    require(any(flag in sys.argv for flag in ("--bootstrap","--code","--preflight","--qualify","--owned-worker")),"PREPARATION_ONLY")
    sources,_=envelope.namespace_bundle.load(c.ROOT,[V6],{})
    v6=sources.current_queue_closed_metadata_runtime_v6
    v6.main.__globals__["load"]=load
    return v6.main()


if __name__=="__main__":raise SystemExit(main())
