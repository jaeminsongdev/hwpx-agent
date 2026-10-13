"""Full connection contracts with independent old133 inputs; not runtime134."""
import copy
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import flat_current_queue_direct_view_runtime_v3 as m

CHECKPOINT = lambda:None
DATA = RAW_SOURCES = METADATA_RAW = CHUNK_RAW = ROOT = LISTING = BODY = FRESH = CTX = INHERITED = None
ACTUAL = WORKER_NAMES = ORACLE_RAW = ACCEPTOR_RAW = None


class DirectConnectionTests(unittest.TestCase):
    def setUp(self):CHECKPOINT()

    def test_all_exact_function_class_and_constant_AST(self):
        for row in m.PROOF['exact_namespace_proofs']:
            self.assertTrue(row['all_function_class_constant_AST_unchanged'])
            self.assertFalse(row['full_module_or_CLI_import_executed'])
            self.assertFalse(row['imported_modules_hidden_or_removed'])
        self.assertFalse(m.PROOF['source_scope_exclusions_added'])
        self.assertFalse(m.PROOF['helper_ceiling_raised'])

    def test_no_full_v2_view_or_oracle_module_import(self):
        for name in ['flat_current_queue_inherited_scope_runtime_v2',
                     'held_native_read_views_v1','held_native_view_oracle_v1']:
            self.assertNotIn(name,sys.modules)

    def test_namespace_drift_cannot_be_loaded(self):
        for i in range(3):
            bad=list(RAW_SOURCES);bad[i]=bad[i]+b'\n'
            with self.assertRaises(ValueError):m.namespaces(bad)

    def test_fresh_namespace_code_equality(self):
        old,view,oracle,native,proof=m.namespaces(RAW_SOURCES)
        self.assertEqual(view.load.__code__,m.VIEW.load.__code__)
        self.assertEqual(view.NativeRead.readinto.__code__,m.VIEW.NativeRead.readinto.__code__)
        self.assertEqual(view.ReadView.readinto.__code__,m.VIEW.ReadView.readinto.__code__)
        self.assertEqual(oracle.mechanics_projection.__code__,m.ORACLE.mechanics_projection.__code__)
        self.assertIs(native.frames,m.base.native.frames)
        self.assertEqual(old.API.prepare.__code__,m.OLD.API.prepare.__code__)

    def test_complete_engine_code_unchanged_with_explicit_dependencies(self):
        old,_=m.OLD.API.template();new,_=m.template()
        self.assertEqual(old.run_owned.__code__,new.run_owned.__code__)
        self.assertEqual(old.worker.__code__,new.worker.__code__)
        self.assertIs(new.run_owned.__globals__['native'],m.NATIVE)
        self.assertIs(new.run_owned.__globals__['runtime_budget'],m.ORACLE.runtime_budget)
        self.assertEqual(new.worker.__globals__['SELF'],m.SELF)
        self.assertIs(m.API.worker.__globals__['template'],m.template)

    def test_default_modules_and_historical_backend_unchanged(self):
        before=m.base.native
        m.template()
        self.assertIs(m.base.native,before)
        self.assertEqual(before.SELF,'tools/p09/retained_read_streams.py')
        self.assertEqual(m.OLD.API.template.__globals__['SELF'],m.NAMESPACE_PINS[0]['path'])
        self.assertEqual(m.API.prepare.__code__,m.OLD.API.prepare.__code__)
        self.assertIsNot(m.API.prepare.__globals__,m.OLD.API.prepare.__globals__)

    def test_every_full_candidate_wrapper_code_retained(self):
        old=m.source.validate_candidate;new=m.CONNECTED_SOURCE.validate_candidate;count=0
        while True:
            self.assertIs(new.__code__,old.__code__);count+=1
            children=[n for n in ('prior','accepted','metadata','original')
                      if n in old.__code__.co_names and hasattr(old.__globals__.get(n),'validate_candidate')]
            if not children:break
            self.assertEqual(len(children),1)
            name=children[0];old=getattr(old.__globals__[name],'validate_candidate')
            new=getattr(new.__globals__[name],'validate_candidate')
        self.assertEqual(count,6)
        self.assertIn('retained_evidence',new.__globals__['candidate'].__dict__)
        self.assertIsNot(new.__globals__['candidate'],old.__globals__['candidate'])

    def test_real_old133_complete_oracle_unchanged(self):
        self.assertTrue(ACTUAL[1]['previous_actual_full_oracle_retained'])
        self.assertEqual(ACTUAL[0]['whole_runtime_input_count'],1976)
        self.assertEqual(ACTUAL[0]['actual_full_byte_passes'],2)
        self.assertTrue(ACTUAL[0]['actual_owned_Native_cleanup_validated'])

    def test_new_scoped_checker_rejects_old_retained_physical_observations(self):
        def direct_mechanics(raw,ctx,flat=True):
            project,proof=m.OLD.API.validator(raw,ctx,flat)
            return m.ORACLE.project_checker(project,project.__globals__['ORACLE_SCOPE']),proof
        wrapped=m.OLD.API.previous_validation.__globals__['previous'].scoped_validator(direct_mechanics,INHERITED)
        project,_=wrapped(ACCEPTOR_RAW,CTX,True)
        check,_=project(ORACLE_RAW,ROOT,LISTING,BODY)
        with self.assertRaisesRegex(ValueError,'^CURRENT_EPOCH_ACCEPT_BORROWED_STREAMS$'):
            check(ROOT,LISTING,BODY,FRESH,CHECKPOINT)

    def test_preflight003_cost_matches_actual_engine_not_old_retained(self):
        fn=m.preflight_projection(METADATA_RAW,CHUNK_RAW)
        self.assertIn('-direct-view-preflight003.v1.json',fn.__code__.co_consts)
        self.assertNotIn('-inherited-namespace-preflight002.v1.json',fn.__code__.co_consts)
        self.assertIs(fn.__globals__['base'].stable.runtime_budget,m.ORACLE.runtime_budget)
        self.assertIs(fn.__globals__['base'].native,m.NATIVE)
        self.assertIs(fn.__globals__['template'],m.template)
        self.assertEqual(m.ORACLE.runtime_budget(INHERITED,167)['final_postcleanup_distinct_sample_wait_allowance_seconds'],.5)

    def test_closed_DATA_preserves_old_sources_and_all_six_code(self):
        self.assertEqual(m.validate_data(copy.deepcopy(DATA),m.base.CONFIG),DATA)
        with self.assertRaises(ValueError):m.validate_data(dict(DATA,skip_previous=True),m.base.CONFIG)
        wrong=copy.deepcopy(DATA);wrong['connection_code_pins']=wrong['connection_code_pins'][:-1]
        with self.assertRaises(ValueError):m.validate_data(wrong,m.base.CONFIG)
        wrong=copy.deepcopy(DATA);wrong['failed134_preflight_pin']=None
        with self.assertRaises(ValueError):m.validate_data(wrong,m.base.CONFIG)

    def test_whole_real_imported_helper_closure_below_original64(self):
        self.assertTrue(28<=len(WORKER_NAMES)<=64)
        self.assertEqual(WORKER_NAMES,sorted(set(WORKER_NAMES)))
        self.assertIn(m.SELF,WORKER_NAMES)
        self.assertIn(m.NATIVE.SELF,WORKER_NAMES)
        self.assertFalse(m.PROOF['original_default_modules_mutated'])


if __name__=='__main__':unittest.main()
