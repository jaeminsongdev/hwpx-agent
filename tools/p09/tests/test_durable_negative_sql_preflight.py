"""Eight exact non-mutating prerequisite contracts; output values are never logged."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import durable_negative_sql_preflight as s


class CurrentSQLPreflightTests(unittest.TestCase):
    def result(self,stdout='',stderr='',code=0):return SimpleNamespace(stdout=stdout,stderr=stderr,returncode=code)

    def test_only_two_exact_read_only_commands(self):
        docker=str(s.DOCKER);commands=s.commands(docker)
        self.assertEqual(commands,(('server_version',[docker,'version','--format','{{.Server.Version}}']),
            ('fixed_image_identity',[docker,'image','inspect','--format','{{.Id}}',s.IMAGE])))
        self.assertNotIn('pull',json.dumps(commands));self.assertNotIn('run',json.dumps(commands))

    def test_alternate_binary_scope_denied(self):
        # Windows path identity is case-insensitive; PATH returns docker.EXE here.
        self.assertEqual(s.commands(str(s.DOCKER).replace('.exe','.EXE'))[0][0],'server_version')
        for name in ('docker','C:/other/docker.exe','C:/Program Files/Docker/docker.exe'):
            with self.assertRaises(ValueError):s.commands(name)

    def test_exact_server_and_image_only_readiness(self):
        server=s.classify(self.result(stdout='28.5.1\n'),'server_version')
        image=s.classify(self.result(stdout=s.IMAGE_ID+'\n'),'fixed_image_identity')
        self.assertEqual(s.diagnosis([server,image]),'READY_FIXED_LOCAL_IMAGE_ONLY_NOT_SQL_OR_GATE')
        self.assertFalse(server['raw_stdout_or_stderr_included'])

    def test_no_such_image_is_not_connection_or_SQL_success(self):
        server=s.classify(self.result(stdout='28.5.1'),'server_version')
        image=s.classify(self.result(stderr='Error: No such image: PRIVATE_FIXTURE',code=1),'fixed_image_identity')
        self.assertEqual(s.diagnosis([server,image]),'FIXED_LOCAL_IMAGE_ABSENT')
        self.assertNotIn('PRIVATE_FIXTURE',json.dumps(image));self.assertFalse(image['exact_identity_accepted'])

    def test_connection_unavailable_keeps_readiness_false(self):
        rows=[s.classify(self.result(stderr='Cannot connect to pipe/dockerDesktopLinuxEngine',code=1),kind)
            for kind in ('server_version','fixed_image_identity')]
        self.assertEqual(s.diagnosis(rows),'LOCAL_BACKEND_ENDPOINT_UNAVAILABLE')

    def test_wrong_identity_malformed_version_or_warning_denied(self):
        server=s.classify(self.result(stdout='28.5.1'),'server_version')
        for raw,errors in (('sha256:'+'0'*64,''),(s.IMAGE_ID,'PRIVATE_WARNING'),('', '')):
            image=s.classify(self.result(stdout=raw,stderr=errors),'fixed_image_identity')
            self.assertNotEqual(s.diagnosis([server,image]),'READY_FIXED_LOCAL_IMAGE_ONLY_NOT_SQL_OR_GATE')
        for raw in ('','private-value','28.5.1\nOTHER'):
            self.assertFalse(s.classify(self.result(stdout=raw),'server_version')['exact_identity_accepted'])

    def test_missing_duplicate_or_reordered_observation_denied(self):
        rows=[s.classify(self.result(),'server_version'),s.classify(self.result(),'fixed_image_identity')]
        for invalid in ([],rows[:1],rows[::-1],rows+rows):
            with self.assertRaises(ValueError):s.diagnosis(invalid)

    def test_probe_three_second_owned_cleanup_no_backend_changes(self):
        metadata=dict(path='target/fixture-metadata.exe',bytes=0,sha256='0'*64)
        runtime=dict(path=s.c.build.executable_name(1),bytes=0,sha256='0'*64)
        reader=SimpleNamespace(pin=lambda n:runtime if n==runtime['path'] else metadata,
            json=lambda n:dict(executable_pin=runtime) if n==s.c.BUILD_PIN['path'] else dict(executable_pin=metadata))
        profile=dict(cleanup_confirmed=True,owned_tree_empty=True,job_handle_closed=True,last_job_accounting=dict(active_processes=0))
        class Factory:
            def __init__(self,**kw):self.record=kw['record']
            def close(self):self.record([profile])
        results=[self.result(stdout='28.5.1'),self.result(stdout=s.IMAGE_ID)]
        with patch.object(s.shutil,'which',return_value=str(s.DOCKER)), \
                patch.object(s,'LocalDockerJobFactory',Factory), \
                patch.object(s,'bounded_observation_run',side_effect=results) as run:
            row=s.check(SimpleNamespace(windows=Mock(),checkpoint_io=Mock()),reader)
        self.assertEqual(run.call_count,2);self.assertTrue(row['ready'])
        for call in run.call_args_list:self.assertEqual(call.kwargs['timeout'],3)
        for key in ('backend_started_or_stopped','image_pulled_or_removed','container_created','SQL_or_native_executed',
                'Docker_daemon_or_WSL_contained_in_host_Job','backend_container_cleanup_qualified'):self.assertFalse(row[key])


if __name__=='__main__':unittest.main()
