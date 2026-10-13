from pathlib import Path
import sys
from types import FunctionType
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preflight_output_slot_v1 as m


def original_factory():
    token=object()
    def original(a=token,*,b=token):
        checkpoint()
        return "-envelope-controller-run003-preflight029.v1.json",a,b
    return original


class Tests(unittest.TestCase):
    def test_explicit_suffix30_and999_only_in_supported_range(self):
        self.assertTrue(m.suffix(30).endswith("preflight030.v1.json"))
        self.assertTrue(m.suffix(999).endswith("preflight999.v1.json"))
    def test_boolean_old_number_float_and_string_rejected(self):
        for value in (True,29,1000,30.0,"30",None):
            with self.assertRaises(ValueError):m.suffix(value)
    def test_only_output_changes_and_inverse_restores_original_code(self):
        old=original_factory();new,proof=m.project(old,30)
        restored=new.__code__.replace(co_consts=tuple(m.OLD if x==m.suffix(30) else x for x in new.__code__.co_consts))
        self.assertEqual(restored,old.__code__)
        self.assertFalse(proof["GO_authorized"])
    def test_defaults_keyword_defaults_closure_and_namespace_retained(self):
        old=original_factory();new,_=m.project(old,30)
        self.assertIs(new.__defaults__,old.__defaults__)
        self.assertIs(new.__kwdefaults__,old.__kwdefaults__)
        self.assertIs(new.__closure__,old.__closure__)
        self.assertEqual(new.__globals__,old.__globals__)
        self.assertIsNot(new.__globals__,old.__globals__)
    def test_original_guard_error_identity_propagates(self):
        old=original_factory();error=ValueError("ORIGINAL_STOP")
        def stop():raise error
        old=FunctionType(old.__code__,dict(old.__globals__,checkpoint=stop),argdefs=old.__defaults__,closure=old.__closure__)
        old.__kwdefaults__=original_factory().__kwdefaults__
        new,_=m.project(old,30)
        with self.assertRaises(ValueError) as caught:new()
        self.assertIs(caught.exception,error)
    def test_original_namespace_does_not_get_new_destination(self):
        old=original_factory();before=old.__code__;m.project(old,30)
        self.assertIs(old.__code__,before);self.assertIn(m.OLD,old.__code__.co_consts)
    def test_missing_original_suffix_rejected(self):
        with self.assertRaises(ValueError):m.project(lambda:None,30)
    def test_same_output_existing_file_or_link_cannot_be_reused(self):
        with patch.object(Path,"is_dir",return_value=True),patch.object(Path,"is_symlink",return_value=False),\
                patch.object(Path,"is_junction",return_value=False),patch.object(Path,"exists",return_value=True):
            with self.assertRaises(ValueError):m.ensure_fresh(Path("D:/repo"),30)
    def test_linked_output_ancestor_rejected(self):
        with patch.object(Path,"is_dir",return_value=True),patch.object(Path,"is_symlink",return_value=True):
            with self.assertRaises(ValueError):m.ensure_fresh(Path("D:/repo"),30)
    def test_destination_is_exact_case158_run003_not_arbitrary_user_path(self):
        self.assertEqual(m.path(Path("D:/repo"),30).name,"p09-361-case158-envelope-controller-run003-preflight030.v1.json")


if __name__=="__main__":unittest.main()
