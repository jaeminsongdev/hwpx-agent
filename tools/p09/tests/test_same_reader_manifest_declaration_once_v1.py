"""Manifest declaration reuse does not replace first/final/Native reads."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import same_reader_manifest_declaration_once_v1 as m

PIN=dict(path="manifest159.json",bytes=3,sha256="a"*64)
INPUT=dict(path="original.json",bytes=4,sha256="b"*64)


class Binding:
    def __init__(self,descriptors,manifest_pin,*,next_case):
        self.rows=copy.deepcopy(descriptors);self.manifest_pin=dict(manifest_pin);self.next_case=next_case
    def descriptors(self):return copy.deepcopy(self.rows)


class Reader:
    def __init__(self):self.snapshots={};self.final_fresh_hashes=0;self.checks=0
    def checkpoint(self):self.checks+=1


class Tests(unittest.TestCase):
    def setUp(self):
        self.owner=[(1,2)];self.q=Reader();self.api=object()
        self.module=NS(Binding=Binding)
        self.deps={k:object() for k in m.KEYS};self.deps["new_module"]=self.module;self.calls=0
        def original(q,pin,a,**deps):
            self.calls+=1;q.snapshots.update({PIN["path"]:dict(PIN),INPUT["path"]:dict(INPUT)})
            return deps["new_module"].Binding([dict(original_pin=INPUT)],pin,next_case=159),\
                {INPUT["path"]:dict(INPUT)},dict(all_original_admission_checks_executed=True)
        self.original=original;self.load,self.counts=m.connect(original,identity=lambda:self.owner[0])
    def execute(self,q=None,**override):
        return self.load(q or self.q,dict(PIN),self.api,**{**self.deps,**override})
    def test_first_call_runs_whole_original_loader(self):
        self.execute();self.assertEqual(self.calls,1);self.assertEqual(self.counts["original_complete_admissions"],1)
    def test_same_reader_same_dependencies_reconstruct_typed_declaration(self):
        first=self.execute();second=self.execute()
        self.assertEqual(self.calls,1);self.assertIsNot(first[0],second[0])
        self.assertIs(type(second[0]),Binding);self.assertEqual(first[0].descriptors(),second[0].descriptors())
        self.assertEqual(first[1:],second[1:]);self.assertEqual(self.counts["duplicate_declarations_avoided"],1)
    def test_different_readers_never_share(self):
        self.execute();self.execute(Reader());self.assertEqual(self.calls,2)
    def test_different_module_never_shares_constructor(self):
        self.execute();self.execute(new_module=NS(Binding=Binding));self.assertEqual(self.calls,2)
    def test_different_original_dependency_never_shares(self):
        self.execute();self.execute(successor=object());self.assertEqual(self.calls,2)
    def test_changed_owner_rejected(self):
        self.execute();self.owner[0]=(1,3)
        with self.assertRaises(ValueError):self.execute()
    def test_changed_retained_pin_rejected(self):
        self.execute();self.q.snapshots[INPUT["path"]]["sha256"]="c"*64
        with self.assertRaises(ValueError):self.execute()
    def test_missing_retained_pin_rejected(self):
        self.execute();del self.q.snapshots[INPUT["path"]]
        with self.assertRaises(ValueError):self.execute()
    def test_final_fresh_is_not_bypassed_or_reset(self):
        self.execute();self.q.final_fresh_hashes=2
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.q.final_fresh_hashes,2)
    def test_caller_result_mutation_does_not_modify_retained_declaration(self):
        b,s,p=self.execute();s[INPUT["path"]]["bytes"]=9;p.clear();b.rows.clear()
        b2,s2,p2=self.execute();self.assertEqual(s2[INPUT["path"]],INPUT)
        self.assertTrue(p2["all_original_admission_checks_executed"]);self.assertEqual(len(b2.descriptors()),1)
    def test_native_and_final_read_methods_never_replaced(self):
        checkpoint=self.q.checkpoint.__func__;self.execute();self.execute()
        self.assertIs(self.q.checkpoint.__func__,checkpoint);self.assertEqual(self.q.final_fresh_hashes,0)
        self.assertGreaterEqual(self.q.checks,4)
    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):self.load(self.q,PIN,self.api,extra=True,**self.deps)
