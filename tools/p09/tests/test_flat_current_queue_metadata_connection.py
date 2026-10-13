import ast
import copy
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_metadata_runtime as r
import flat_current_queue_metadata_acceptance as accept


class ConnectionContracts(unittest.TestCase):
    def step(self, index=120):
        return NS(index=index, before=index-7, pin=dict(path='step', bytes=1, sha256='0'*64))

    def data(self, index=120):
        step = self.step(index)
        return dict(schema_version='hwpx-agent.p09-flat-metadata-connection/v1', index=index,
                    before=step.before, run=2 if index == 120 else 1, base_step_pin=step.pin,
                    failed_runtime_pin=r.FAILED120 if index == 120 else None,
                    optimization_qualification_pin=r.QUALIFIED,
                    connection_code_pins=[dict(path=n, bytes=1, sha256='0'*64) for n in r.FILES])

    def test_exact120_has_only_reviewed_second_attempt(self):
        self.assertEqual(r.validate_data(self.data(), self.step())['run'], 2)

    def test_later_steps_are_first_attempt_not_automatic_retry(self):
        self.assertEqual(r.validate_data(self.data(121), self.step(121))['run'], 1)

    def test_extra_or_wrong_typed_cursor_or_run_rejected(self):
        for key, value in (('run', 3), ('run', True), ('index', 121), ('before', 114)):
            row = self.data(); row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                r.validate_data(row, self.step())
        row = self.data(); row['extra'] = True
        with self.assertRaises(ValueError):
            r.validate_data(row, self.step())

    def test_failed_pin_cannot_be_removed_or_substituted(self):
        for value in (None, dict(r.FAILED120, sha256='0'*64)):
            row = self.data(); row['failed_runtime_pin'] = value
            with self.assertRaises(ValueError):
                r.validate_data(row, self.step())

    def test_connection_code_inventory_must_be_complete(self):
        row = self.data(); row['connection_code_pins'].pop()
        with self.assertRaises(ValueError):
            r.validate_data(row, self.step())

    def test_qualification_or_step_pin_cannot_change(self):
        for key in ('optimization_qualification_pin', 'base_step_pin'):
            row = self.data(); row[key] = dict(row[key], sha256='0'*64)
            if key == 'base_step_pin': row[key]['bytes'] = 2
            with self.assertRaises(ValueError):
                r.validate_data(row, self.step())

    def test_compatible_summary_retains_policy_but_warning_never_cools(self):
        events = []
        owner = NS(lock=threading.Lock(), samples=[dict(system_cpu_percent=75)],
                   checkpoint_io=lambda: events.append('hard'))
        reader = NS(checkpoint=lambda: events.append('original'))
        guard = r.MetadataCheckpoint(reader, owner)
        with self.assertRaisesRegex(ValueError, 'STOP_METADATA_WARNING'):
            reader.checkpoint()
        guard.restore()
        self.assertEqual(events, ['hard'])
        self.assertEqual((guard.COOL_SAMPLES, guard.MAX_WINDOWS, guard.pause_windows), (2, 8, 0))
        self.assertEqual(guard.warning_entries, 1)
        self.assertTrue(guard.restored)

    def test_authorized_root_never_selects_failed001(self):
        self.assertTrue(accept.root_path(self.step()).endswith('run002.v1.json'))
        self.assertTrue(accept.root_path(self.step(121)).endswith('run001.v1.json'))

    def test_prepare_projection_retains_all_ast_and_rejects_drift(self):
        # Synthetic small AST contract only; real pinned source checked in guarded prepare.
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        fn = accept.prepare_projection(raw)
        self.assertTrue(callable(fn))
        with self.assertRaises(ValueError):
            accept.prepare_projection(raw.replace(b'run001', b'run003'))

    def test_runtime_factory_does_not_mutate_original_build_module(self):
        # No real runtime/worker. Exact engine projection is inspected only.
        if r.base.CONFIG is None:
            r.base.configure(120)
        old = r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint
        engine, proof = r.template()
        self.assertIs(r.base.stable.stable.prior.build.pressure.PreSaturationReadCheckpoint, old)
        self.assertTrue(proof['original_engine_bytecode_unchanged'])
        self.assertEqual(engine.run_owned.__globals__['SELF'], r.SELF)
        self.assertIs(engine.run_owned.__globals__['build'].pressure.PreSaturationReadCheckpoint,
                      r.MetadataCheckpoint)


if __name__ == '__main__':
    unittest.main()
