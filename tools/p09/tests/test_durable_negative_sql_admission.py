"""Sixteen pure current-generation admission/DI contracts; no actual children."""
import base64
import copy
import hashlib
import json
import re
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import durable_negative_sql_contract as s
import durable_negative_sql_driver as driver
import test_signed_durable_sql_connection as fixture

pin=fixture.pin
NONCE=fixture.NONCE


class CurrentNegativeSQLAdmissionTests(unittest.TestCase):
    def row(self):
        row=fixture.DurableSQLConnectionTests().build_row()
        row.update(state=s.build.PASS,runtime_only_build_accepted=True,
            provided_driver_generation='P151_R31_CURRENT_DS06_NON_TEST',whole_workspace_Rust_input_count=785,
            protected_executables_expected=53,parent_example_audit_pin=s.build.AUDIT_PIN,
            actual_SQL_metadata_or_signed_consumer_qualified=False,
            executable_pin=pin(s.build.executable_name(1)),
            protected_executables=[pin(f'target/protected-{n}.exe') for n in range(53)])
        return row

    def binding(self):
        return dict(scheme=s.SCHEME,actual_SQL_qualified=False,receipt_pin=s.BUILD_PIN,closing_audit_pin=s.CLOSING_PIN,
            compiled_source_count=846,current_Rust_input_count=785,required_check_count=39,
            helper_paths=['tools/p09/fixture.py'])

    def test_current53_and_non_test_accept(self):
        _,protected,exe=s.accepted(self.row());self.assertEqual(len(protected),53)
        self.assertEqual(exe['path'],s.build.executable_name(1))

    def test_wrong_generation_count_or_parent_denied(self):
        for key,value in (('provided_driver_generation','P150'),('whole_workspace_Rust_input_count',784),
                ('protected_executables_expected',52),('parent_example_audit_pin',s.prior.CLOSING_PIN)):
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(dict(self.row(),**{key:value}))

    def test_acceptance_cleanup_or_phase_change_denied(self):
        for key,value in (('state','PASS'),('runtime_only_build_accepted',False),('owned_tree_empty',False),
                ('source_freeze_exact_after',False),('exit_code',2),('product_complete',True),('P09_gate','CLOSED'),
                ('actual_SQL_metadata_or_signed_consumer_qualified',True),('current_SQL_admission_qualified',True)):
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(dict(self.row(),**{key:value}))

    def test_limits_and_assertion_weakening_denied(self):
        for section,key,value in (('owned_limits_readback','affinity_mask',3),('owned_limits_readback','cpu_hard_cap_machine_percent',100),
                ('owned_limits_readback','breakaway_disabled',False),('job_final','active_processes',1),
                ('capture_diagnostics','per_stream_limit_bytes',65536)):
            row=self.row();row[section][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(row)
        for key,value in (('test',True),('debug_assertions',False),('overflow_checks',False)):
            row=self.row();row['build_result']['catalog_profile'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(row)

    def test_complete_stream_required(self):
        for key,value in (('all_records_validated',False),('raw_output_truncated',True),('raw_logs_included',True)):
            row=self.row();row['build_result']['validated_stream'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(row)

    def test_old_unit_or_other_runtime_denied(self):
        for name in (s.prior.build.executable_name(5),s.build.executable_name(2),
                'target/p09-151-durable-negative/build/debug/examples/formula_issuer_product_postgres_probe-05e8ead2b3796168.exe'):
            with self.assertRaises(ValueError):s.accepted(dict(self.row(),executable_pin=pin(name)))

    def test_all53_history_no_duplicates(self):
        for rows in (self.row()['protected_executables'][:-1],self.row()['protected_executables']+[pin('target/protected-0.exe')]):
            with self.assertRaises(ValueError):s.accepted(dict(self.row(),protected_executables=rows))

    def test_fixed_receipt_before_IO(self):
        reader=Mock()
        with self.assertRaises(ValueError):s.bind_probe_build(reader,s.prior.BUILD_PIN['path'])
        reader.pin.assert_not_called()

    def test_consumer846_785_39_binding_closed(self):
        names=s.consumer_sources(self.binding());self.assertEqual(len(names),len(set(names)))
        self.assertTrue(set(s.SOURCES)<=set(names));self.assertIn(s.CLOSING_PIN['path'],names)
        for key,value in (('scheme','old'),('compiled_source_count',845),('current_Rust_input_count',784),
                ('required_check_count',31),('receipt_pin',s.prior.BUILD_PIN),('actual_SQL_qualified',True)):
            with self.subTest(key=key),self.assertRaises(ValueError):s.consumer_sources(dict(self.binding(),**{key:value}))

    def test_original31_preserved_then_eight_exact(self):
        checks=driver.required_checks();self.assertEqual(len(checks),39)
        self.assertEqual(checks[:31],driver.prior.required_checks())
        self.assertEqual(checks[31:],list(s.build.parent.CONTROL_CHECKS))

    def test_duplicate_or_original_check_drift_denied(self):
        with patch.object(s.build.parent,'CONTROL_CHECKS',s.build.parent.CONTROL_CHECKS[:-1]+(s.build.parent.CONTROL_CHECKS[0],)):
            with self.assertRaises(ValueError):driver.required_checks()
        with patch.object(driver.prior.original,'ROOT_CHECKS',list(reversed(driver.prior.original.ROOT_CHECKS))):
            with self.assertRaises(ValueError):driver.required_checks()

    def test_whole_guard_inverse_only842_to846(self):
        source='before\nlen(build["source_freeze"]) == 842\nafter\n'
        self.assertEqual(driver.transformed_source(source).replace('== 846','== 842'),source)
        for wrong in ('missing',source+source,source+'len(build["source_freeze"]) == 846'):
            with self.assertRaises(ValueError):driver.transformed_source(wrong)

    def test_original_driver_clone_DI_policy_and_no_root_creation(self):
        raw=(s.c.ROOT/s.DRIVER).read_bytes();item=dict(path=s.DRIVER,bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
        reader=SimpleNamespace(json=lambda name:dict(files=[item]),pin=lambda name:{k:item[k] for k in ('path','bytes','sha256')})
        original=driver.prior.original;before=original.OwnedSQLJobFactory;checks=list(original.ROOT_CHECKS)
        made,holder=driver.make_driver(reader,NONCE)
        self.assertIsNot(made,original);self.assertIs(original.OwnedSQLJobFactory,before)
        self.assertEqual(original.ROOT_CHECKS,checks);self.assertEqual(made.CHECKS,original.CHECKS)
        self.assertEqual(made.resource_policy(),original.resource_policy());self.assertIsNone(holder.root)
        self.assertIs(made.bind_probe_build,s.bind_probe_build);self.assertIs(made.consumer_sources,s.consumer_sources)
        self.assertEqual(holder.crypto,str(s.c.ROOT/s.build.executable_name(1)))

    def test_declared_rust_four_and_control_order_exact(self):
        self.assertEqual(len(s.ADDED_RUST),4);self.assertEqual(s.SOURCE_COUNT,846)
        raw=(s.c.ROOT/s.build.parent.SOURCE).read_text(encoding='utf-8')
        block=re.search(r'pub\(super\) const CHECKS: \[&str; 8\] = \[(.*?)\];',raw,re.DOTALL)
        self.assertIsNotNone(block)
        self.assertEqual(tuple(re.findall(r'"([a-zA-Z0-9_]+)"',block.group(1))),s.build.parent.CONTROL_CHECKS)

    def test_original_whole_sql_helpers_unchanged(self):
        for item in json.loads((s.c.ROOT/s.ARCHIVE).read_text(encoding='utf-8'))['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            self.assertEqual((s.c.ROOT/item['path']).read_bytes(),raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'])

    def test_admission_has_no_product_or_SQL_execution_mode(self):
        source=(s.c.ROOT/'tools/p09/verify_durable_negative_sql_admission.py').read_text(encoding='utf-8')
        self.assertIn("choices=('light','admission')",source)
        self.assertNotIn('supervise_owned_call(',source);self.assertNotIn('journalled_driver_call(',source)
        self.assertIsInstance(s.CLOSING_PIN,dict)
        self.assertNotEqual(s.BUILD_PIN,s.prior.BUILD_PIN)


if __name__=='__main__':unittest.main()
