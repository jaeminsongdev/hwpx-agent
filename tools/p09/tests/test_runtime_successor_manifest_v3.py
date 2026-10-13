"""Manifest025 closed cursor tests; actual positive path is qualified separately."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_manifest_v3 as m
import accept_case112_current_epoch as a
import runtime_successor_binding_v2 as successor

root=Path(__file__).resolve().parents[3]
document=json.loads((root/m.PATH).read_text(encoding="utf-8"))
class Reader:
    def __init__(self,row):self.row=row;self.snapshots={}
    def json(self,name):self.snapshots[name]=dict(path=name,bytes=1,sha256="0"*64);return self.row

class Tests(unittest.TestCase):
    def reject(self,row,path=None):
        q=Reader(row);pin=dict(path=path or m.PATH,bytes=1,sha256="0"*64)
        with self.assertRaises(ValueError):m.load(q,pin,a,controller=None,new_module=None,successor=successor)
    def test_extra_manifest_key_denied(self):self.reject(dict(document,extra=True))
    def test_wrong_or_boolean_cursor_denied(self):
        for row in (dict(document,index=True),dict(document,index=159),dict(document,before=152)):
            with self.subTest(row=row):self.reject(row)
    def test_wrong_or_boolean_physical_run_denied(self):
        for run in (1,True,3):
            with self.subTest(run=run):self.reject(dict(document,physical_product_run=run))
    def test_other_base_manifest_denied(self):
        row=copy.deepcopy(document);row["base_manifest_pin"]["path"]="wrong.json";self.reject(row)
    def test_other_current_manifest_path_denied(self):self.reject(document,"wrong.json")
