import os
import stat
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rust_inventory_single_snapshot_v1 as m
import current_stored_native_bridge as native

RAW = (Path(__file__).resolve().parents[3] / m.ORIGINAL_PIN["path"]).read_bytes()
def original():
    return native.definitions(RAW.decode(), ("rust_inputs",), dict(os=os, Path=Path, require=m.require)).rust_inputs
def snapshot(mode, attrs=0, tag=0):
    return NS(st_mode=mode, st_file_attributes=attrs, st_reparse_tag=tag)
class PathProbe:
    def __init__(self, file=True, link=False, junction=False):
        self.file, self.link, self.junction = file, link, junction
        self.calls = []
    def is_file(self): self.calls.append("file"); return self.file
    def is_symlink(self): self.calls.append("link"); return self.link
    def is_junction(self): self.calls.append("junction"); return self.junction

class Tests(unittest.TestCase):
    def test_ordinary_file_one_fresh_query_no_original_path_calls(self):
        p = PathProbe();c = m.Counters();calls=[]
        def query(path, **kw): calls.append((path,kw));return snapshot(stat.S_IFREG)
        self.assertTrue(m.predicate(p,"file",c,query=query))
        self.assertEqual(calls,[(p,dict(follow_symlinks=False))]);self.assertEqual(p.calls,[])
    def test_ordinary_directory_and_nonregular_file_decisions(self):
        c=m.Counters();p=PathProbe()
        self.assertTrue(m.predicate(p,"directory",c,query=lambda *a,**k:snapshot(stat.S_IFDIR,0x10)))
        self.assertFalse(m.predicate(p,"file",c,query=lambda *a,**k:snapshot(stat.S_IFDIR,0x10)))
        self.assertTrue(m.predicate(p,"directory",c,query=lambda *a,**k:snapshot(stat.S_IFREG)))
    def test_reparse_fallback_keeps_exact_short_circuit_order(self):
        for file,link,junction,expected,calls in ((False,False,False,False,["file"]),(True,True,False,False,["file","link"]),(True,False,True,False,["file","link","junction"]),(True,False,False,True,["file","link","junction"])):
            p=PathProbe(file,link,junction);c=m.Counters()
            self.assertEqual(m.predicate(p,"file",c,query=lambda *a,**k:snapshot(stat.S_IFREG,0x400,42)),expected)
            self.assertEqual(p.calls,calls);self.assertEqual(c.fallbacks,1)
    def test_error_and_invalid_fields_fallback_without_promoting_paths(self):
        def failure(*a,**k):raise PermissionError("test")
        for query in (failure,lambda *a,**k:NS(),lambda *a,**k:snapshot(stat.S_IFREG,0x10),lambda *a,**k:snapshot(stat.S_IFREG,True)):
            p=PathProbe(link=True);c=m.Counters()
            self.assertFalse(m.predicate(p,"directory",c,query=query));self.assertEqual(p.calls,["link"])
    def test_repeated_path_fresh_stat_detects_changes_no_cache(self):
        values=iter((snapshot(stat.S_IFREG),snapshot(stat.S_IFDIR,0x10)));c=m.Counters();p=PathProbe()
        query=lambda *a,**k:next(values)
        self.assertTrue(m.predicate(p,"file",c,query=query));self.assertFalse(m.predicate(p,"file",c,query=query))
        self.assertEqual(c.attempts,2)
    def test_original_code_and_all_ast_bodies_except_three_predicates_verified(self):
        fn=original();new,c=m.projection(fn,RAW)
        self.assertIsNot(fn.__code__,new.__code__);self.assertIsNone(new.__defaults__);self.assertIsNone(new.__closure__)
        self.assertEqual(c.requests,0);self.assertIs(new.__globals__["require"],fn.__globals__["require"])
    def test_changed_pin_and_changed_original_code_rejected(self):
        with self.assertRaises(ValueError):m.projection(original(),RAW+b"\n")
        fn=original();fn.__code__=fn.__code__.replace(co_name="changed")
        with self.assertRaises(ValueError):m.projection(fn,RAW)
    def test_inventory_result_checkpoints_filters_and_budget_unchanged(self):
        old=original();records=[("/test/crates",["src"],["Cargo.toml","skip.txt"]),("/test/crates/src",[],["a.rs"])]
        def walk(path,**kw):return records if path.as_posix()=="/test/crates" else []
        def query(path,**kw):return snapshot(stat.S_IFREG if str(path).endswith(("Cargo.toml",".rs")) else stat.S_IFDIR,0 if str(path).endswith(("Cargo.toml",".rs")) else 0x10)
        new,c=m.projection(old,RAW,query=query);a=[];b=[]
        with patch.object(os,"walk",walk),patch.object(Path,"is_dir",return_value=True),patch.object(Path,"is_file",return_value=True),patch.object(Path,"is_symlink",return_value=False),patch.object(Path,"is_junction",return_value=False):
            self.assertEqual(old(Path("/test"),lambda:a.append(1)),new(Path("/test"),lambda:b.append(1)))
        self.assertEqual(a,b);self.assertEqual(c.file_requests,2);self.assertEqual(c.directory_requests,3)
    def test_private_factory_only_and_other_definitions_delegate_unchanged(self):
        a=NS(native=native,Guard=object(),AcceptanceReader=object());old=NS(a=a,API=object())
        new,c=m.runtime(old,RAW);self.assertIs(old.a.native,native);self.assertIs(new.API,old.API)
        self.assertIs(new.a.Guard,a.Guard);self.assertIs(new.a.AcceptanceReader,a.AcceptanceReader)
        text=RAW.decode().replace("\r\n","\n")
        self.assertIsNot(new.a.native.definitions(text,("rust_inputs",),dict(os=os,Path=Path,require=m.require)).rust_inputs.__code__,original().__code__)
        self.assertEqual(len(c),1)
    def test_checkpoint_errors_propagate_before_any_predicate_without_retry(self):
        new,c=m.projection(original(),RAW)
        def fail():raise ValueError("ORIGINAL_STOP")
        with patch.object(os,"walk",return_value=[("/test/crates",[],["x.rs"])]),patch.object(Path,"is_dir",return_value=True):
            with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):new(Path("/test"),fail)
        self.assertEqual(c.requests,0)

if __name__ == "__main__":unittest.main()
