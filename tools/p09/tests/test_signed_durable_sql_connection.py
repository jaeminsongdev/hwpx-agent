"""Closed admission/root/DI tests; no SQL, native or child process starts."""
import base64
import copy
import hashlib
import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import signed_durable_sql_contract as s
import signed_durable_sql_root as root
import signed_durable_sql_driver as driver
import run_signed_durable_sql_probe as runner

NONCE='12345678-1234-4234-8234-123456789abc'
RUN='87654321-4321-4321-8321-cba987654321'


def pin(name):return dict(path=name,bytes=0,sha256='0'*64)


class DurableSQLConnectionTests(unittest.TestCase):
    def build_row(self):
        return dict(state=s.build.PASS,current_build_binding_accepted=True,source_freeze_exact_after=True,
            protected_executables_exact_after=True,cleanup_confirmed=True,owned_tree_empty=True,exit_code=0,
            stop_reason=None,policy=copy.deepcopy(s.c.POLICY),worker_created=True,job_assigned=True,
            writer_authorized=True,post_hash_stable_admission_revalidated=True,compile_admission_RAM_percent=15,
            build_result=dict(catalog_profile=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,
                overflow_checks=True,test=False),validated_stream=dict(all_records_validated=True,
                raw_output_truncated=False,raw_logs_included=False,stdout_record_buffer_limit=32768,
                stderr_total_limit=32768,stdout_total_JSON_IO_budget=16*1024*1024)),
            current_dev_package_profile_config=list(s.build.DEV_CONFIG),
            original_test_package_profile_config=list(s.build.original.base.CONFIG),
            actual_SQL_or_native_executed=False,current_SQL_admission_qualified=False,
            old_SQL_admission_modified=False,product_complete=False,P09_gate='OPEN',
            owned_limits_readback=dict(verified=True,cpu_hard_cap_machine_percent=6.25,affinity_mask=1,
                priority_class=16384,kill_on_close=True,breakaway_disabled=True,active_process_limit=16),
            job_final=dict(active_processes=0,owned_processes=[]),
            capture_diagnostics=dict(error_code=None,per_stream_limit_bytes=32768,raw_log_content_included=False),
            source_freeze=[pin('tools/p09/fixture.py')],whole_workspace_Rust_input_count=784,
            protected_executables=[pin(f'target/protected-{n}.exe') for n in range(51)],
            executable_pin=pin(s.build.executable_name(5)))

    def test_current_runtime_profile_and_limits_accept(self):
        source,protected,exe=s.accepted(self.build_row())
        self.assertEqual(len(protected),51);self.assertEqual(exe['path'],s.build.executable_name(5))
        self.assertEqual(len(source),1)

    def test_phase_success_cleanup_or_current_count_change_denied(self):
        for key,value in (('state','PASS'),('current_SQL_admission_qualified',True),('product_complete',True),
                ('P09_gate','CLOSED'),('owned_tree_empty',False),('whole_workspace_Rust_input_count',783),
                ('source_freeze_exact_after',False),('exit_code',2)):
            with self.subTest(key=key),self.assertRaises(ValueError):s.accepted(dict(self.build_row(),**{key:value}))

    def test_caps_profile_and_raw_stream_weakening_denied(self):
        changes=[('owned_limits_readback','affinity_mask',3),('owned_limits_readback','breakaway_disabled',False),
            ('owned_limits_readback','cpu_hard_cap_machine_percent',100),('job_final','active_processes',1),
            ('capture_diagnostics','per_stream_limit_bytes',65536)]
        for section,key,value in changes:
            row=self.build_row();row[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):s.accepted(row)
        for section,key,value in (('catalog_profile','test',True),('catalog_profile','overflow_checks',False),
                ('validated_stream','raw_output_truncated',True),('validated_stream','all_records_validated',False)):
            row=self.build_row();row['build_result'][section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):s.accepted(row)

    def test_old_test_or_canonical_binary_denied(self):
        for name in (s.build.original.BINARY,s.build.executable_name(4),
                     'target/p09-150-signed-durable/build/debug/examples/formula_issuer_product_postgres_probe.exe'):
            with self.assertRaises(ValueError):s.accepted(dict(self.build_row(),executable_pin=pin(name)))

    def test_only_fixed_receipt_before_any_IO(self):
        reader=Mock()
        with self.assertRaises(ValueError):s.bind_probe_build(reader,s.legacy.CURRENT_BUILD_PIN['path'])
        reader.pin.assert_not_called()

    def test_duplicate_or_invalid_input_pin_denied(self):
        for rows in ([],[pin('a'),pin('a')],[dict(pin('a'),sha256='bad')]):
            with self.assertRaises((ValueError,KeyError)):s.inventory(rows)

    def test_closed_consumer_binding_and_required_helpers(self):
        binding=dict(scheme='p150_current_runtime_r05',actual_SQL_qualified=False,receipt_pin=s.BUILD_PIN,
            compiled_source_count=845,helper_paths=['tools/p09/compiled-helper.py'])
        names=s.consumer_sources(binding)
        self.assertEqual(len(names),len(set(names)));self.assertTrue(set(s.SOURCES)<=set(names))
        self.assertIn(s.CLOSING_PIN['path'],names)
        for key,value in (('scheme','old'),('actual_SQL_qualified',True),('compiled_source_count',842),
                           ('receipt_pin',s.legacy.CURRENT_BUILD_PIN)):
            with self.assertRaises(ValueError):s.consumer_sources(dict(binding,**{key:value}))

    def test_all27_original_checks_retained_and_four_added_in_exact_positions(self):
        checks=driver.required_checks();extra=driver.ROOT_EXTRA+driver.CONSUMER_EXTRA
        self.assertEqual(len(checks),31)
        self.assertEqual([n for n in checks if n not in extra],driver.original.ROOT_CHECKS)
        self.assertEqual(checks[7:9],list(driver.ROOT_EXTRA));self.assertEqual(checks[20:22],list(driver.CONSUMER_EXTRA))

    def test_only_count_delta_whole_inverse(self):
        source='before\nlen(build["source_freeze"]) == 842\nafter\n'
        changed=driver.transformed_source(source)
        self.assertEqual(changed.replace('== 845','== 842'),source)
        for wrong in ('missing',source+source,source+'len(build["source_freeze"]) == 845'):
            with self.assertRaises(ValueError):driver.transformed_source(wrong)

    def test_changed_original_check_order_denied(self):
        with patch.object(driver.original,'ROOT_CHECKS',list(reversed(driver.original.ROOT_CHECKS))):
            with self.assertRaises(ValueError):driver.required_checks()

    def test_whole_current_original_driver_clone_no_original_mutation(self):
        raw=(s.c.ROOT/s.DRIVER).read_bytes()
        original=dict(path=s.DRIVER,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
            base64=base64.b64encode(raw).decode())
        reader=SimpleNamespace(json=lambda name:dict(files=[original]),
            pin=lambda name:{k:original[k] for k in ('path','bytes','sha256')})
        before=driver.original.OwnedSQLJobFactory;checks=list(driver.original.ROOT_CHECKS)
        made,holder=driver.make_driver(reader,NONCE)
        self.assertIsNot(made,driver.original);self.assertIs(driver.original.OwnedSQLJobFactory,before)
        self.assertEqual(driver.original.ROOT_CHECKS,checks)
        self.assertEqual(made.CHECKS,driver.original.CHECKS)
        self.assertEqual(made.resource_policy(),driver.original.resource_policy())
        self.assertIs(made.bind_probe_build,s.bind_probe_build)
        self.assertIs(made.consumer_sources,s.consumer_sources)
        self.assertEqual(made.ROOT_CHECKS,driver.required_checks());self.assertIsNone(holder.root)

    def test_current_original_digest_drift_denied(self):
        raw=b'x';item=dict(pin(s.DRIVER),base64=base64.b64encode(raw).decode())
        reader=SimpleNamespace(json=lambda name:dict(files=[item]),pin=Mock())
        with self.assertRaises(ValueError):driver.make_driver(reader,NONCE)
        reader.pin.assert_not_called()

    def test_root_exact_UUID_and_marker(self):
        self.assertEqual(root.root_name(RUN),f'{root.BASE}/p150-{RUN}')
        self.assertEqual(root.marker(RUN),f'{root.SCHEMA}\n{RUN}\n'.encode())
        for wrong in ('..',RUN.upper(),'87654321-4321-1321-8321-cba987654321','',None):
            with self.assertRaises(ValueError):root.root_name(wrong)

    def factory(self):
        delegated=Mock(return_value='unchanged-delegate');holder=root.OwnedRootHolder(NONCE,'fixture-crypto')
        class Original:
            def __init__(self):self.docker='fixture-docker'
            def __call__(self,args,**kw):return delegated(args,**kw)
        return holder,holder.factory_type(Original)(),delegated,Original

    def run_args(self):return root.ownership.run_arguments('fixture-docker',root.ownership.make_intent(NONCE,'approval',RUN))

    def test_exact_run_UUID_creates_root_before_delegate_and_scrubs_env(self):
        holder,factory,delegated,original=self.factory();trace=[]
        env=dict(POSTGRES_PASSWORD='PRIVATE_FIXTURE',**{k:'forged' for k in root.ENV})
        delegated.side_effect=lambda *a,**kw:trace.append('delegate') or 'same'
        with patch.object(root,'create',side_effect=lambda run:trace.append('create') or Path('derived')) as create:
            self.assertEqual(factory(self.run_args(),env=env,cwd='same'),'same')
            create.assert_called_once_with(RUN)
        self.assertEqual(trace,['create','delegate']);self.assertEqual(holder.run,RUN)
        self.assertIsInstance(factory,original);actual=delegated.call_args
        self.assertEqual(actual.args[0],self.run_args());self.assertEqual(actual.kwargs['cwd'],'same')
        self.assertEqual(actual.kwargs['env'],dict(POSTGRES_PASSWORD='PRIVATE_FIXTURE'))
        self.assertEqual(env['P150_BLOB_ROOT'],'forged')

    def test_root_creation_failure_never_launches_original(self):
        _,factory,delegated,_=self.factory()
        with patch.object(root,'create',side_effect=OSError('PRIVATE_FIXTURE')):
            with self.assertRaises(OSError):factory(self.run_args(),env={})
        delegated.assert_not_called()

    def test_forged_run_is_rejected_before_creation_and_delegate(self):
        _,factory,delegated,_=self.factory();args=self.run_args();args[12]='0.0.0.0::5432'
        with patch.object(root,'create') as create:
            with self.assertRaises(ValueError):factory(args,env={})
        create.assert_not_called();delegated.assert_not_called()

    def test_duplicate_run_cannot_create_or_launch_second_container(self):
        holder,factory,delegated,_=self.factory();holder.root=Path('already-created')
        with patch.object(root,'create') as create:
            with self.assertRaises(ValueError):factory(self.run_args(),env={})
        create.assert_not_called();delegated.assert_not_called()

    def test_only_exact_crypto_command_gets_verified_environment(self):
        holder,factory,delegated,_=self.factory();holder.root=Path('derived');holder.run=RUN
        with patch.object(root,'verify',return_value=holder.root) as verify:
            factory(['fixture-crypto'],env=dict(KEEP='same',P150_BLOB_MODE='forged'))
            verify.assert_called_once_with(holder.root,RUN)
        env=delegated.call_args.kwargs['env'];self.assertEqual(env['KEEP'],'same')
        self.assertEqual(env['P150_BLOB_MODE'],'owned_local_v1');self.assertEqual(env['P150_BLOB_RUN_ID'],RUN)

    def test_crypto_without_root_or_with_arguments_never_delegates(self):
        for args in (['fixture-crypto'],['fixture-crypto','extra']):
            _,factory,delegated,_=self.factory()
            with self.assertRaises(ValueError):factory(args,env={})
            delegated.assert_not_called()

    def test_invalid_command_shape_denied(self):
        for args in ([],None,'fixture-crypto',[None]):
            _,factory,delegated,_=self.factory()
            with self.assertRaises(ValueError):factory(args,env={})
            delegated.assert_not_called()

    def test_other_commands_unchanged_except_durable_env_scrub(self):
        holder,factory,delegated,_=self.factory();args=['fixture-docker','image','inspect','fixed']
        with patch.object(root,'create') as create:
            factory(args,env=dict(KEEP='same',**{k:'forged' for k in root.ENV}))
        delegated.assert_called_once_with(args,env=dict(KEEP='same'));create.assert_not_called()
        self.assertIsNone(holder.root)

    def test_journal_fsync_then_root_create_then_delegate(self):
        holder,factory,delegated,original=self.factory();trace=[]
        def writer(intent):
            trace.append('journal');return dict(intent=intent,journal_fsync_before_delegate_completed=True)
        factory=root.ownership.journalled_factory_type(type(factory),NONCE,'approval',writer=writer)()
        delegated.side_effect=lambda *a,**kw:trace.append('delegate')
        with patch.object(root,'create',side_effect=lambda run:trace.append('root') or Path('derived')):
            factory(self.run_args(),env={})
        self.assertEqual(trace,['journal','root','delegate'])

    def test_failed_journal_blocks_root_creation(self):
        _,factory,delegated,_=self.factory()
        factory=root.ownership.journalled_factory_type(type(factory),NONCE,'approval',
            writer=Mock(side_effect=ValueError('SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED')))()
        with patch.object(root,'create') as create:
            with self.assertRaises(ValueError):factory(self.run_args(),env={})
        create.assert_not_called();delegated.assert_not_called()

    def test_absent_root_manifest_not_disk_or_SQL_success(self):
        holder,_,_,_=self.factory();reader=Mock()
        self.assertEqual(holder.manifest(reader),dict(created=False,retained=True,files=[]))
        reader.pin.assert_not_called()

    def test_exact_owner_marker_read_is_bounded(self):
        path=s.c.ROOT/root.root_name(RUN);owner=Mock()
        owner.is_file.return_value=True;owner.stat.return_value=SimpleNamespace(st_size=len(root.marker(RUN)))
        owner.open.return_value=io.BytesIO(root.marker(RUN))
        with patch.object(root,'scoped_path',side_effect=[path,owner]),patch.object(Path,'is_dir',return_value=True):
            self.assertEqual(root.verify(path,RUN),path)
        owner.open.assert_called_once_with('rb')

    def test_owner_missing_oversize_or_wrong_identity_denied(self):
        path=s.c.ROOT/root.root_name(RUN)
        for exists,size,raw in ((False,0,b''),(True,130,b''),(True,4,b'bad!')):
            owner=Mock();owner.is_file.return_value=exists;owner.stat.return_value=SimpleNamespace(st_size=size)
            owner.open.return_value=io.BytesIO(raw)
            with patch.object(root,'scoped_path',side_effect=[path,owner]), \
                    patch.object(Path,'is_dir',return_value=True),self.assertRaises(ValueError):root.verify(path,RUN)

    def test_owner_root_other_path_denied_before_marker_read(self):
        path=s.c.ROOT/root.root_name(RUN)
        with patch.object(root,'scoped_path',return_value=path),self.assertRaises(ValueError):
            root.verify(s.c.ROOT/'target/other-root',RUN)

    def test_inventory_limit_before_any_unbounded_sort_or_file_read(self):
        holder,_,_,_=self.factory();holder.root=s.c.ROOT/root.root_name(RUN);holder.run=RUN
        reader=SimpleNamespace(resources=SimpleNamespace(checkpoint_io=Mock()),pin=Mock())
        consumed=[]
        def children():
            for n in range(10000):consumed.append(n);yield holder.root/str(n)
        with patch.object(root,'verify',return_value=holder.root),patch.object(Path,'iterdir',side_effect=lambda:children()):
            with self.assertRaisesRegex(ValueError,'ROOT_INVENTORY_BUDGET'):holder.manifest(reader)
        self.assertEqual(len(consumed),257);reader.pin.assert_not_called()

    def test_inventory_addition_cannot_pass_as_whole_root(self):
        holder,_,_,_=self.factory();holder.root=s.c.ROOT/root.root_name(RUN);holder.run=RUN
        reader=SimpleNamespace(resources=SimpleNamespace(checkpoint_io=Mock()),pin=Mock())
        with patch.object(root,'verify',return_value=holder.root), \
                patch.object(Path,'iterdir',side_effect=[iter([]),iter([holder.root/'new-file'])]):
            with self.assertRaisesRegex(ValueError,'ROOT_INVENTORY_DRIFT'):holder.manifest(reader)

    def test_runner_requires_explicit_current_selection_not_legacy(self):
        with patch.object(runner.subject,'scoped_path') as scoped:
            args=runner.arguments(7,0,'original','unchanged')
        self.assertEqual(args[0],s.BUILD_PIN['path']);self.assertEqual(args[-1],'approval')
        scoped.assert_called_once_with(args[1],fresh=True)
        for selection in ((True,0,'original','unchanged'),(91,0,'original','unchanged'),
                (7,36,'original','unchanged'),(7,0,'original','changed'),(7,0,'numeric_derivative','unchanged')):
            with self.assertRaises(ValueError):runner.arguments(*selection)

    def test_runner_redacts_unknown_or_private_error_values(self):
        for error in (ValueError('PRIVATE_FIXTURE'),OSError('PRIVATE_FIXTURE'),ValueError('X'*200)):
            self.assertNotIn('PRIVATE_FIXTURE',runner.closed_error(error))
        self.assertEqual(runner.closed_error(ValueError('SQL_BUILD_DURABLE_CURRENT_INPUT_DRIFT')),
                         'SQL_BUILD_DURABLE_CURRENT_INPUT_DRIFT')

    def test_no_caps_or_original_SQL_policy_changes(self):
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'],8)
        self.assertEqual(s.c.POLICY['job_memory_stop_percent'],7)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'],32768)
        self.assertEqual(driver.original.resource_policy()['container_memory_bytes'],512*1024*1024)


if __name__=='__main__':unittest.main()
