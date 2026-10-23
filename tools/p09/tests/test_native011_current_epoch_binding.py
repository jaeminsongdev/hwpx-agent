"""Original-function projection and single-use scope composition models only."""
import ast
import copy
from types import SimpleNamespace as NS
import unittest
import accept_case112_current_epoch as a
import conservative_maintenance as c
import current_stored_runtime_scope as scope
import native011_current_epoch_scope as epoch
import native011_current_epoch_binding as binding


def pin(name):return dict(path=name,bytes=1,sha256='a'*64)


class BindingContracts(unittest.TestCase):
    def fixture(self):
        original=[pin(f'legacy/f{i}.rs') for i in range(1658)]
        translation=(original[0],dict(original[0],path='archive/legacy/f0.rs'))
        archived=epoch.archive_rows({p['path']:p for p in original},[translation],scope)
        current={'current/x.rs':pin('current/x.rs')};whole=scope.extend(archived,current)
        controls={'controls/binding.py':pin('controls/binding.py')};record={'names':['original']}
        declaration=NS(current=current,whole=whole,translations=[translation])
        owner=binding.BoundScope(scope,declaration,record,controls,pin('current/candidate.exe'),epoch.archive_rows)
        return owner,record,original

    def test_actual_original_whole_function_only_count_guard_projection(self):
        raw=(c.ROOT/binding.SOURCE['path']).read_text(encoding='utf-8')
        observed=[]
        def definitions(source,names,namespace):
            observed.append(source);return NS(binding=lambda q:None)
        _,proof=binding.project_binding(raw,definitions,{})
        self.assertTrue(proof['whole_function_AST_inverse'])
        self.assertFalse(proof['old_schema_PASS_fabricated'])
        self.assertEqual(proof['changed_guard'],dict(before=787,after=805))
        source=observed[0]
        self.assertIn('len(rust) == 805',source)
        self.assertIn('AUTHORITATIVE_FRESH131_EXACT112',source)
        self.assertIn('UNCHANGED105_CURSOR',source)
        self.assertIn('scope.compose',source)
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_RUST_COUNT_GUARD'):
            binding.project_binding(raw.replace('len(rust)==787','len(rust)==786'),definitions,{})

    def test_original_listing_then_independent_archive_union_without_mutating_global_scope(self):
        owner,record,original=self.fixture();before=copy.deepcopy(scope.EXE_PIN)
        current=owner.listing_inputs(record);result=owner.compose(original,list(current.values()))
        self.assertEqual(result,owner.whole)
        self.assertEqual(owner.calls,['listing_inputs','compose'])
        self.assertEqual(scope.EXE_PIN,before)
        self.assertNotEqual(owner.api.EXE_PIN,before)
        self.assertIn('archive/legacy/f0.rs',result);self.assertNotIn('legacy/f0.rs',result)

    def test_source_scope_replacement_and_second_call_rejected(self):
        owner,record,original=self.fixture();current=owner.listing_inputs(record)
        with self.assertRaisesRegex(ValueError,'EXACT_CURRENT_DECLARATION_NO_SCOPE_SUBSTITUTION'):
            owner.compose(original,[pin('different.rs')])
        owner.compose(original,list(current.values()))
        with self.assertRaisesRegex(ValueError,'ORIGINAL_BINDING_CALL_ORDER'):
            owner.compose(original,list(current.values()))
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_REAL_LIST_RECORD'):owner.listing_inputs(record)

    def test_wrong_order_wrong_record_and_later_record_mutation_rejected(self):
        owner,record,original=self.fixture()
        with self.assertRaisesRegex(ValueError,'ORIGINAL_BINDING_CALL_ORDER'):owner.compose(original,[])
        record['names'].append('altered')
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_REAL_LIST_RECORD'):owner.listing_inputs(record)


if __name__=='__main__':unittest.main()
