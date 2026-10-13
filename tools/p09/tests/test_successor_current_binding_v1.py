from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case112_current_epoch as a
import successor_current_binding_v1 as m


class Tests(unittest.TestCase):
    def test_wrong_or_bool_current_config_rejected_before_read(self):
        for config in (None,NS(index=158,before=151),NS(index=True,before=152),NS(index=159,before=True)):
            fake=NS(a=a,base=NS(CONFIG=config))
            q=NS(json=lambda name:(_ for _ in ()).throw(AssertionError("UNEXPECTED_READ")))
            with self.subTest(config=config),self.assertRaises(ValueError):m.qualify(q,fake)
    def test_wrong_prior_context_rejected_before_full_oracle(self):
        fn=m.previous_callback(NS(a=a))
        listing=dict(source_test_names=[""]*157+["exact_case"])
        with patch.object(m.predecessor,"prepare") as prepare:
            for index,before,flat in ((157,150,True),(158,True,True),(True,151,True),(158,151,False)):
                with self.subTest(index=index,before=before,flat=flat),self.assertRaises(ValueError):
                    fn(None,{},listing,None,None,NS(INDEX=index,BEFORE=before,CASE="exact_case"),flat)
        prepare.assert_not_called()
    def _fixture(self):
        oldbody=dict(original=True);fresh=dict(original="fresh")
        row=dict(selected_test_index=158);listing=dict(source_test_names=[""]*157+["exact_case"])
        api=NS(a=NS(require=a.require,exact=a.exact,BODY_PIN=dict(path="body"),FRESH_PIN=dict(path="fresh"),
            packed=NS(unpack=lambda raw,check:raw),read_exact=lambda q,p:oldbody if p["path"]=="body" else fresh))
        return api,row,listing,oldbody,fresh,NS(INDEX=158,BEFORE=151,CASE="exact_case"),NS(checkpoint=lambda:None)
    def test_full_oracle_return_and_original_row_retained(self):
        api,row,listing,body,fresh,ctx,q=self._fixture();token=object()
        with patch.object(m.predecessor,"prepare",return_value=(row,listing,token,{})) as prepare:
            evidence,proof=m.previous_callback(api)(q,row,listing,body,fresh,ctx)
        self.assertIs(evidence,token);prepare.assert_called_once_with(q,api,m.prepare_adapter,m.successor)
        self.assertFalse(proof["hash_only_predecessor_substitution"])
    def test_fresh_body_substitution_rejected_before_oracle(self):
        api,row,listing,body,fresh,ctx,q=self._fixture()
        with patch.object(m.predecessor,"prepare") as prepare,self.assertRaises(ValueError):
            m.previous_callback(api)(q,row,listing,dict(changed=True),fresh,ctx)
        prepare.assert_not_called()
    def test_fresh_fixture_substitution_rejected_before_oracle(self):
        api,row,listing,body,fresh,ctx,q=self._fixture()
        with patch.object(m.predecessor,"prepare") as prepare,self.assertRaises(ValueError):
            m.previous_callback(api)(q,row,listing,body,dict(changed=True),ctx)
        prepare.assert_not_called()
    def test_prior_candidate_substitution_rejected_after_whole_check(self):
        api,row,listing,body,fresh,ctx,q=self._fixture()
        with patch.object(m.predecessor,"prepare",return_value=(dict(changed=True),listing,None,{})),self.assertRaises(ValueError):
            m.previous_callback(api)(q,row,listing,body,fresh,ctx)
    def test_compiled_roster_substitution_rejected_after_whole_check(self):
        api,row,listing,body,fresh,ctx,q=self._fixture()
        with patch.object(m.predecessor,"prepare",return_value=(row,dict(changed=True),None,{})),self.assertRaises(ValueError):
            m.previous_callback(api)(q,row,listing,body,fresh,ctx)
    def test_original_resource_stop_exception_identity_retained(self):
        api,row,listing,body,fresh,ctx,q=self._fixture();error=ValueError("ORIGINAL_RESOURCE_STOP")
        with patch.object(m.predecessor,"prepare",side_effect=error),self.assertRaises(ValueError) as caught:
            m.previous_callback(api)(q,row,listing,body,fresh,ctx)
        self.assertIs(caught.exception,error)


if __name__=="__main__":unittest.main()
