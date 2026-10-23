"""Actual parent receipt-namespace construction only; never Native or GO.

Use the qualified parent probe's unchanged complete main body. Explicit
dependencies add this diagnostic and the receipt projector to its plan and
connect the namespace before the original Frame captures its actual engine.
"""
import hashlib
import json
from pathlib import Path
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_pre_go_namespace_probe.py'
HELPER='tools/p09/batch_pre_go_receipt.py'
PARENT=dict(path='tools/p09/batch_zlib_frame_probe.py',bytes=8012,
    sha256='f94c1b6f5a7f149faa3e925a653a1e89ee62088f61953584fdb88c3ec09cf768')


def require(ok,code):
    if not ok:raise ValueError('PRE_GO_NAMESPACE_PROBE_'+code)


def bootstrap(root):
    path=root/PARENT['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_QUALIFIED_PARENT_PROBE')
    for directory in (path.parent,*path.parent.parents):
        require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(),'DIRECT_ANCESTORS')
        if directory==root:break
    with path.open('rb') as stream:raw=stream.read(PARENT['bytes']+1)
    require(len(raw)==PARENT['bytes'] and hashlib.sha256(raw).hexdigest()==PARENT['sha256'],'EXACT_QUALIFIED_PARENT_PROBE')
    env=dict(__name__='p09_exact_namespace_parent_probe',__file__=str(path))
    exec(compile(raw,PARENT['path'],'exec'),env)
    return NS(**env)


def connect(probe):
    states=[];constructions=[];original_bootstrap=probe.bootstrap
    def bootstrap(root):
        metadata=original_bootstrap(root);original=metadata.construct
        def construct(root,q,epochs,a,parent,entry,profile,loader,prep,policy,witness,byte_policy):
            require(not constructions,'ONE_ORIGINAL_CONSTRUCTION_NOT_RETRY')
            constructions.append(True)
            a.exact(q.pin(PARENT['path']),PARENT,'ORIGINAL_PARENT_PROBE_PRESERVED')
            extra={name:dict(q.pin(name)) for name in (HELPER,PARENT['path'])}
            libraries,_=loader.load(root,[extra[HELPER]],{})
            selected=probe.extended_parent(parent,extra)
            selected,state=libraries.batch_pre_go_receipt.parent_api(selected);states.append(state)
            return original(root,q,epochs,a,selected,entry,profile,loader,prep,policy,witness,byte_policy)
        return NS(**{**vars(metadata),'construct':construct})
    def serialize(row,**kwargs):
        if row['state']=='PASS_ACTUAL_PRE_GO_PARENT_CONNECTION_NOT_NATIVE':
            require(len(states)==len(constructions)==1,'ONE_ACTUAL_DIAGNOSTIC_NAMESPACE_STATE')
            state=states[0]
            require(state.loads==state.windows==state.links==1 and state.projection['complete_code_inverse'] is True,
                'ACTUAL_ORIGINAL_ENGINE_NAMESPACE_CONNECTION')
            row=dict(row,state='PASS_ACTUAL_PRE_GO_DIAGNOSTIC_NAMESPACE_CONNECTION_NOT_NATIVE',
                diagnostic_receipt_namespace=state.projection,
                original_parent_probe_main_body_code_defaults_and_closure_unchanged=True,
                canonical_Native_receipt_or_intent_written=False)
        return json.dumps(row,**kwargs)
    original=probe.main
    env=dict(original.__globals__,SELF=SELF,bootstrap=bootstrap,json=NS(**{**vars(json),'dumps':serialize}))
    selected=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    selected.__kwdefaults__=original.__kwdefaults__
    require(selected.__code__ is original.__code__ and selected.__defaults__ is original.__defaults__
        and selected.__closure__ is original.__closure__,'ENTIRE_QUALIFIED_PARENT_PROBE_MAIN')
    return selected


def main():
    require(sys.argv[1:]==['--connect-only'],'ONLY_DIAGNOSTIC_CONSTRUCTION_NO_NATIVE_OR_GO')
    root=Path(__file__).resolve().parents[2]
    return connect(bootstrap(root))()


if __name__=='__main__':raise SystemExit(main())
