"""Closed readonly Frame diagnostic entry, no product/GO mode."""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_readonly_frame_entry.py'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def main():
    args=sys.argv[1:];construct=bool(args and args[0]=='--construct-only');args=args[1:] if construct else args
    if len(args)!=2 or args[0]!='--attempt' or args[1] not in ('1','2','3','4','5','6','7','8'):
        raise ValueError('READONLY_FRAME_CLOSED_ENTRY')
    root=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
    def fresh(name,limit):
        path=root/name
        for parent in (path,*path.parents):
            if parent.is_symlink() or parent.is_junction():raise ValueError('READONLY_ENTRY_DIRECT_SOURCE')
            if parent==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        if not 0<len(raw)<=limit:raise ValueError('READONLY_ENTRY_SOURCE_BOUND')
        return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    if len(raw)!=LOADER['bytes'] or hashlib.sha256(raw).hexdigest()!=LOADER['sha256']:
        raise ValueError('READONLY_FRAME_EXACT_LOADER')
    env=dict(__name__='p09_readonly_frame_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    loader=NS(**env);pins=[]
    for name in ('tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py'):
        raw=fresh(name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=loader.load(root,pins,{})
    driver=libs.native011_readonly_frame_driver.Driver(int(args[1]),construct_only=construct)
    before=sys.argv;sys.argv=[before[0]]
    try:return libs.native011_ready_native_construction.main(driver=driver)
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
