from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import native011_engine_owned_metadata_validation as m
import native011_ready_native_construction as common
import native011_engine_owned_metadata_connection as owned
import native011_engine_owned_metadata_adoption as adoption
import native011_metadata_tail_connection as connection
import native011_metadata_tail_candidate as candidate
import native011_exact_read_budget as exact
import native011_chunk_join_connection as codes
import reusable_audit_chunk_v1 as chunk
import owned_source_read_pressure as pressure
import test_native011_metadata_tail_connection as fixtures


class Tests(unittest.TestCase):
    def raw(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def test_entire_validator_inverse_one_factory_site_and_no_allocation(self):
        original=common.validate;namespace=dict(vars(common))
        with patch.object(owned,'connect',side_effect=AssertionError('NO_ALLOCATION_DURING_PROJECTION')):
            selected,proof=m.project(self.raw(m.SOURCE),original)
        self.assertIs(common.validate,original);self.assertEqual(set(vars(common)),set(namespace))
        self.assertTrue(all(vars(common)[n] is value for n,value in namespace.items()))
        self.assertTrue(proof['entire_original_validator_AST_inverse']);self.assertEqual(proof['metadata_selector_sites'],1)
        self.assertFalse(proof['Native_or_product_or_GO_authorized'])
        self.assertIsNot(selected.__globals__,original.__globals__)
    def test_entry_changes_one_private_dependency_without_rewriting_original_main(self):
        raw=self.raw(m.SOURCE);selected,proof=m.project(raw,common.validate)
        entry,evidence=m.bind_entry(raw,common.main,selected)
        self.assertIs(entry.__code__,common.main.__code__);self.assertIs(entry.__closure__,common.main.__closure__)
        self.assertEqual(entry.__kwdefaults__,common.main.__kwdefaults__)
        self.assertIs(entry.__globals__['validate'],selected);self.assertIs(common.main.__globals__['validate'],common.validate)
        self.assertFalse(evidence['actual_common_entry_or_Native_or_product_executed'])
    def test_nonoriginal_source_or_function_refused_before_any_connection(self):
        raw=self.raw(m.SOURCE)
        with self.assertRaises(ValueError):m.project(raw+b'\n',common.validate)
        with self.assertRaises(ValueError):m.project(raw,lambda:None)
        with self.assertRaises(ValueError):m.bind_entry(raw,lambda:None,common.validate)
    def test_all_original_factory_arguments_reach_owned_adapter_in_exact_order(self):
        args=[object() for _ in range(12)];called=[]
        api=NS(connect=lambda *values:(called.append(values) or 'result'))
        result=m.select(api,adoption,connection,*args[:11])
        self.assertEqual(result,'result');self.assertEqual(called,[tuple(args[:3])+tuple([connection,args[3],adoption])+tuple(args[4:11])])
    def test_actual_private_factory_uses_original_owned_assignment_after_common_selector(self):
        linked,owner,pins=fixtures.Tests().fixture()
        selected,proof=m.select(owned,adoption,connection,linked,owner,pins,candidate,exact,pressure,chunk,
            self.raw(exact.ORIGINAL),self.raw(connection.METADATA),self.raw(connection.BUILD),codes)
        self.assertEqual(owner.metadata_connection.readers,[]);self.assertIsNone(owner.shared.metadata)
        reader,prefix=owned.allocate_original_prefix(self.raw(owned.ENGINE),linked.engine.run_owned.__globals__['build'],'.',lambda:None,pressure)
        self.assertIsInstance(reader,selected.selected_reader)
        self.assertTrue(adoption.summary(reader)['original_engine_owned_assignment_adopted'])
        self.assertEqual(proof['original_engine_metadata_IO_rates'],dict(binary=1048576,other=2097152))
        self.assertEqual(reader.read_passes,0);self.assertFalse(proof['GO_authorized'])
    def test_selector_does_not_remove_original_engine_checker_or_protection_calls(self):
        selected,proof=m.project(self.raw(m.SOURCE),common.validate)
        names=set(selected.__code__.co_names)
        self.assertTrue({'complete_budget','inspect_current','connect_shared','connect_private_factory','project'}<=names)
        self.assertIs(selected.__globals__['require'],common.validate.__globals__['require'])
        self.assertTrue(proof['original_engine_checker_complete_budget_source201_shared5_and_guards_retained'])
    def test_compile_fallback_is_lazy_but_still_required_on_first_form_mismatch(self):
        raw=self.raw(m.SOURCE)
        with patch.object(m,'compile',wraps=compile,create=True) as compiled:
            m.checked(raw,common.validate,'validate')
            self.assertEqual(compiled.call_count,1)
        with patch.object(m,'compile',wraps=compile,create=True) as compiled:
            with self.assertRaises(ValueError):m.checked(raw,lambda:None,'validate')
            self.assertEqual(compiled.call_count,2)
