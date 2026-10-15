import copy
import unittest


class Tests(unittest.TestCase):
    def data(self):
        old=dict(path="implementation/p09/evidence/p09-361-case112-current-runtime-run001.v1.json",bytes=100,sha256="a"*64)
        physical=dict(path="implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run001.envelope.v1.json",bytes=50,sha256="b"*64)
        row=dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1",next_case=164,semantic_original_pin=old,physical_envelope_pin=physical)
        extra=dict(path="tools/p09/untouched.py",bytes=10,sha256="c"*64)
        return old,physical,row,extra

    def test_alias_and_all_unmapped_pins_preserved(self):
        old,physical,row,extra=self.data();rows={physical["path"]:physical,extra["path"]:extra};before=copy.deepcopy(rows)
        normalized,proof=MODULE.normalize(SCOPE,[row],rows,165,CHECKPOINT)
        self.assertEqual(normalized,{old["path"]:old,extra["path"]:extra});self.assertEqual(rows,before)
        self.assertEqual(proof["approved_prior_aliases_reconciled"],1)

    def test_wrong_physical_hash_and_logical_conflict_rejected(self):
        old,physical,row,extra=self.data()
        with self.assertRaises(ValueError):MODULE.normalize(SCOPE,[row],{physical["path"]:dict(physical,sha256="d"*64)},165,CHECKPOINT)
        with self.assertRaises(ValueError):MODULE.normalize(SCOPE,[row],{physical["path"]:physical,old["path"]:dict(old,bytes=99)},165,CHECKPOINT)

    def test_source_alias_or_unapproved_context_or_duplicate_rejected(self):
        old,physical,row,extra=self.data()
        for changed in (dict(row,next_case=165),dict(row,semantic_original_pin=extra),dict(row,next_case=True)):
            with self.assertRaises(ValueError):MODULE.normalize(SCOPE,[changed],{physical["path"]:physical},165,CHECKPOINT)
        with self.assertRaises(ValueError):MODULE.normalize(SCOPE,[row,row],{physical["path"]:physical},165,CHECKPOINT)

    def test_new_current_encoding_not_an_arbitrary_prior_alias(self):
        old,physical,row,extra=self.data();new=dict(physical,path=physical["path"].replace(".envelope.",".level6.envelope."),sha256="e"*64)
        rows={new["path"]:new,extra["path"]:extra};normalized,proof=MODULE.normalize(SCOPE,[row],rows,165,CHECKPOINT)
        self.assertEqual(rows,normalized);self.assertEqual(proof["approved_prior_aliases_reconciled"],0)

    def test_empty_history_idempotence_and_mapping_key_identity(self):
        old,physical,row,extra=self.data();rows={physical["path"]:physical,old["path"]:old}
        first,_=MODULE.normalize(SCOPE,[row],rows,165,CHECKPOINT);second,_=MODULE.normalize(SCOPE,[row],first,165,CHECKPOINT)
        self.assertEqual(first,second);self.assertEqual(MODULE.normalize(SCOPE,[],rows,165,CHECKPOINT)[0],rows)
        with self.assertRaises(ValueError):MODULE.normalize(SCOPE,[row],{"wrong":physical},165,CHECKPOINT)

    def test_private_adapter_runs_original_union_and_retains_other_methods(self):
        old,physical,row,extra=self.data();m,_=BINDINGS_API.connect(ROOT,LOADER,SCOPE,165,{},[row])
        other={n:f for n,f in vars(m.Binding).items() if n!="semantic_union"}
        MODULE.install(m,[row],165)
        pin=dict(path="implementation/p09/evidence/manifest.v1.json",bytes=1,sha256="f"*64)
        bound=m.Binding([dict(row,next_case=165)],pin,next_case=165)
        semantic,proof=bound.semantic_union({physical["path"]:physical,extra["path"]:extra},CHECKPOINT)
        self.assertEqual(semantic,{old["path"]:old,extra["path"]:extra})
        self.assertTrue(proof["explicit_exact_pair_reconciliation_only"])
        self.assertTrue(all(vars(m.Binding)[n] is f for n,f in other.items()))
        with self.assertRaises(ValueError):MODULE.install(m,[row],165)
