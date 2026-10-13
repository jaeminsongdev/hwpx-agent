import math
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import owned_input_read_pressure as pressure
import stored_test_profile81 as profile


class InputContracts(unittest.TestCase):
    def owner(self,value=40):
        return SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=value)],checkpoint_io=lambda:None)
    def test_no_legacy_runner_dependency_is_loaded_by_lightweight_modules(self):
        import ast
        for module in (pressure,profile):
            tree=ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            names=[name.name for node in ast.walk(tree) if isinstance(node,ast.Import) for name in node.names]
            self.assertTrue(set(names)<={"math","time"})
            self.assertFalse(any(isinstance(node,ast.ImportFrom) for node in ast.walk(tree)))
    def test_cool_host_retains_original_hard_and_full_callbacks(self):
        events=[];owner=self.owner();owner.checkpoint_io=lambda:events.append("hard")
        reader=SimpleNamespace(checkpoint=lambda:events.append("full"))
        guard=pressure.PreSaturationReadCheckpoint(reader,owner,sleep=lambda _:self.fail("unexpected wait"))
        reader.checkpoint();guard.restore();self.assertEqual(events,["hard","full"])
    def test_sample_must_advance_not_reuse_same_row_twice(self):
        owner=self.owner(80);reader=SimpleNamespace(checkpoint=lambda:None)
        guard=pressure.PreSaturationReadCheckpoint(reader,owner,sleep=lambda _:None)
        with self.assertRaisesRegex(ValueError,"SAMPLE_NOT_ADVANCED"):reader.checkpoint()
        guard.restore()
    def test_invalid_original_sample_fails_closed(self):
        for value in (True,-1,101,math.nan,"40"):
            owner=self.owner(value);reader=SimpleNamespace(checkpoint=lambda:None)
            guard=pressure.PreSaturationReadCheckpoint(reader,owner)
            with self.subTest(value=value),self.assertRaises(ValueError):reader.checkpoint()
            guard.restore()
    def test_guard_does_not_restore_some_other_callback(self):
        owner=self.owner();reader=SimpleNamespace(checkpoint=lambda:None)
        guard=pressure.PreSaturationReadCheckpoint(reader,owner);reader.checkpoint=lambda:None
        with self.assertRaises(ValueError):guard.restore()
    def test_query_pacer_rejects_nonadvancing_clock_without_loop(self):
        waits=[];pacer=pressure.QueryPacer(lambda:None,clock=lambda:0.,sleep=lambda delay:waits.append(delay))
        pacer.reserve()
        with self.assertRaisesRegex(ValueError,"CLOCK_NOT_ADVANCING"):pacer.reserve()
        self.assertEqual(len(waits),64)
    def test_all81_keys_and_assertions_are_exact(self):
        profile.config_contract(profile.CONFIG)
        self.assertEqual(len(profile.CONFIG),81)
        self.assertEqual(len(profile.PACKAGES),16)
        self.assertEqual(sum("debug-assertions=true" in value for value in profile.CONFIG),16)
        self.assertEqual(sum("overflow-checks=true" in value for value in profile.CONFIG),16)
        self.assertEqual(sum("codegen-units=16" in value for value in profile.CONFIG),16)
        changed=tuple(value.replace("debug-assertions=true","debug-assertions=false") for value in profile.CONFIG)
        with self.assertRaises(ValueError):profile.config_contract(changed)


if __name__=="__main__":unittest.main()
