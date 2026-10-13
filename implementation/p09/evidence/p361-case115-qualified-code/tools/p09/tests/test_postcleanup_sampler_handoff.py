"""Guarded pure scheduling/AST contracts; no Native or product execution."""
import ast
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import postcleanup_sampler_handoff as h
import run_case114_current_queue as r


class HandoffContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine,_=r.template()
        q=r.stable.accepted112.AcceptanceReader(r.c.ROOT,CHECKPOINT)
        pin,raw=q._read(h.TEMPLATE_PIN['path'],parse=True);q._bind(pin['path'],pin)
        r.stable.accepted112.exact(pin,h.TEMPLATE_PIN,'ORIGINAL_TEMPLATE')
        cls.raw=bytes(raw);cls.fixed,cls.proof=h.project(cls.raw,cls.engine.run_owned,114,107);q.finish()
    def test_one_timestamp_assignment_and_every_original_guard_undo_exact(self):
        self.assertTrue(self.proof['engine_AST_restored_exactly'])
        self.assertTrue(self.proof['exact_original_engine_code_verified_before_change'])
        self.assertEqual(self.proof['added_timestamp_assignments'],1)
        self.assertFalse(self.proof['extra_sampler_query_thread_or_process'])
        self.assertFalse(self.proof['missing_interval_errors_suppressed'])
    def test_last_successful_timestamp_not_new_zero_or_rounded_clock(self):
        self.assertEqual(h.timestamp((49.999,3.),clock=lambda:50.),49.999)
        for value in (None,[],(None,0),(True,0),(51.,0),(-1.,0),(49.,float('nan'))):
            with self.subTest(),self.assertRaises(ValueError):h.timestamp(value,clock=lambda:50.)
    def test_immediate_post_cleanup_waits_for_original_cadence_no_fake_sample(self):
        post_time=h.timestamp((50.,0.),clock=lambda:50.)
        observations=[]
        for now in (50.,50.001,50.499,50.5):
            if now-post_time>=.5:observations.append(now);post_time=now
        self.assertEqual(observations,[50.5])
    def test_already_due_sample_is_not_postponed_or_hidden(self):
        post_time=h.timestamp((49.4,0.),clock=lambda:50.)
        self.assertGreaterEqual(50.-post_time,.5)
    def test_modified_template_or_different_baseline_cannot_project(self):
        with self.assertRaises(ValueError):h.project(self.raw[:-1],self.engine.run_owned,114,107)
        with self.assertRaises(ValueError):h.project(self.raw,lambda _:0,114,107)
        with self.assertRaises(ValueError):h.project(self.raw,self.engine.run_owned,115,108)
    def test_actual_original_post_guard_still_contains_all_deadlines_and_decisions(self):
        tree=ast.parse(self.raw.decode('utf-8'))
        guards=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='post_guard']
        self.assertEqual(len(guards),1)
        code=ast.unparse(guards[0])
        for text in ('global_deadline','<= 600','>= 0.5','c.decision','reason is None','sampled(windows_instance)'):
            self.assertIn(text,code)


CHECKPOINT=lambda:None
if __name__=='__main__':
    guard=r.stable.accepted112.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(HandoffContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_or_Native_frame_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
