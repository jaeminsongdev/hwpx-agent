from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed_receipt_manifest_v2 as m
import accept_case112_current_epoch as a


def row():
    pin=lambda path:dict(path=path,bytes=1,sha256="a"*64)
    return dict(schema_version=m.SCHEMA,index=158,before=151,
        base_manifest_pin=pin(m.original.PATH),failed004_role_code_pin=pin(m.CODE),
        failed004_producer_pin=pin(m.PRODUCER),failed004_descriptor={},failure004_admission={},
        extra_three_producer_pin=pin(m.EXTRA),extra_three_descriptors=[])


class Tests(unittest.TestCase):
    def rejected(self,value,pin_path=None):
        pin=dict(path=pin_path or m.PATH,bytes=1,sha256="a"*64)
        authority=NS(read_exact=lambda q,p:value,require=a.require,fields=a.fields,exact=a.exact)
        with self.assertRaises(ValueError):m.load(object(),pin,authority)
    def test_extra_or_missing_manifest_keys_rejected(self):
        self.rejected(dict(row(),extra=True))
        value=row();del value["failure004_admission"];self.rejected(value)
    def test_wrong_case_before_or_boolean_case_rejected(self):
        for values in (dict(index=True),dict(index=157),dict(before=150)):
            self.rejected(dict(row(),**values))
    def test_wrong_manifest_or_base_path_rejected_before_large_reads(self):
        self.rejected(row(),"wrong.json")
        value=row();value["base_manifest_pin"]=dict(value["base_manifest_pin"],path="wrong.json")
        self.rejected(value)
    def test_both_private_failure_roles_required(self):
        self.rejected(row())


if __name__=="__main__":unittest.main()
