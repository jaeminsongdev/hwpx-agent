from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_manifest_v1 as m
import runtime_successor_binding_v1 as successor
import accept_case112_current_epoch as a


def row():
    pin=lambda name:dict(path=name,bytes=1,sha256="a"*64)
    return dict(schema_version=m.SCHEMA,index=159,before=152,authority152_pin=successor.AUTHORITY,
        actual158_pin=successor.ROOT,prior_manifest_pin=pin("old.json"),binding_qualification_pin=pin(m.CODE),
        extra_producer_pin=pin(m.PRODUCER),prior_failure_lineage={})


class Tests(unittest.TestCase):
    def rejected(self,value,path=None):
        authority=NS(read_exact=lambda q,p:value,require=a.require,fields=a.fields,exact=a.exact)
        with self.assertRaises(ValueError):m.load(object(),dict(path=path or m.PATH,bytes=1,sha256="a"*64),authority,
            old_manifest=None,new_module=None,successor=successor,failed003=None,failed004=None)
    def test_extra_and_missing_closed_keys_rejected(self):
        self.rejected(dict(row(),extra=True));value=row();del value["prior_failure_lineage"];self.rejected(value)
    def test_wrong_or_boolean_case_cursor_rejected(self):
        for values in (dict(index=True),dict(index=158),dict(before=151)):self.rejected(dict(row(),**values))
    def test_wrong_actual_authority_root_or_manifest_path_rejected(self):
        for key in ("authority152_pin","actual158_pin"):
            value=row();value[key]=dict(value[key],path="wrong.json");self.rejected(value)
        self.rejected(row(),"wrong.json")
    def test_actual_private_binding_is_required_before_old_admission(self):self.rejected(row())


if __name__=="__main__":unittest.main()
