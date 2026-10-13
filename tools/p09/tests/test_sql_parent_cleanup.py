"""Pure fallback identity guards and bounded command mocks, never live deletion."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import sql_parent_cleanup as subject
import sql_container_ownership as ownership
from tests.test_sql_container_ownership import NONCE, RUN

IDENTIFIER = "1"*64


def item_for(intent):
    return {"Id": IDENTIFIER, "Name": "/"+intent["container_name"], "Image": intent["image_id"],
        "Config": {"Labels": {intent["label_key"]: RUN}, "Image": intent["image_pin"], "Env": ["PRIVATE_FIXTURE"]},
        "Mounts": [], "HostConfig": {"NetworkMode": "bridge", "PortBindings": {"5432/tcp": [{"HostIp": "127.0.0.1"}]},
            "ReadonlyRootfs": True, "NanoCpus": 1000000000, "Memory": 536870912, "MemorySwap": 536870912,
            "PidsLimit": 64, "Tmpfs": {"/var/lib/postgresql": {}, "/tmp": {}, "/var/run/postgresql": {}}}}


class SQLParentCleanupTests(unittest.TestCase):
    def result(self, code=0, output="", error=""):
        return SimpleNamespace(returncode=code, stdout=output, stderr=error)

    def fixture(self, *, mutate=None, absent=False, unavailable=False, rm_failed=False, remains=False, case="approval"):
        intent = ownership.make_intent(NONCE, case, RUN)
        item = item_for(intent)
        if mutate:
            mutate(item)
        command = Mock(side_effect=[self.result(1, error="daemon unavailable" if unavailable else "No such container")
            if absent or unavailable else self.result(output=json.dumps([item])),
            self.result(1 if rm_failed else 0), self.result(0 if remains else 1, error="" if remains else "No such object")])
        row = subject.cleanup_from_intent(intent, command)
        self.assertIsNone(row["backend_container_cleanup_confirmed"])
        self.assertFalse(row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"])
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))
        return row, command, intent

    def test_owned_target_is_removed_by_fresh_ID_not_mutable_name(self):
        for case in ownership.CASES:
            row, command, intent = self.fixture(case=case)
            self.assertTrue(row["command_response_removal_verified"])
            self.assertEqual(row["container_id"], IDENTIFIER)
            self.assertEqual([call.args[0] for call in command.call_args_list],
                [["inspect", intent["container_name"]], ["rm", "--force", IDENTIFIER], ["inspect", IDENTIFIER]])

    def test_absent_lookup_does_not_remove_any_target(self):
        row, command, _ = self.fixture(absent=True)
        self.assertTrue(row["command_response_removal_verified"])
        self.assertIsNone(row["container_id"])
        self.assertEqual(command.call_count, 1)

    def test_unavailable_lookup_is_not_absence_or_removal_success(self):
        row, command, _ = self.fixture(unavailable=True)
        self.assertFalse(row["command_response_removal_verified"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(command.call_count, 1)

    def test_wrong_name_run_label_image_pin_or_ID_shape_cannot_be_removed(self):
        mutations = (lambda x: x.update(Name="/other"), lambda x: x.update(Id="other"),
            lambda x: x.update(Image="sha256:"+"2"*64), lambda x: x["Config"].update(Image="other"),
            lambda x: x["Config"]["Labels"].update({ownership.CASES["approval"][1]: NONCE}))
        for mutate in mutations:
            row, command, _ = self.fixture(mutate=mutate)
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertEqual(command.call_count, 1)

    def test_all_original_isolation_guards_reject_drift_before_rm(self):
        mutations = (lambda x: x.update(Mounts=[{}]), lambda x: x["HostConfig"].update(NetworkMode="host"),
            lambda x: x["HostConfig"].update(ReadonlyRootfs=False), lambda x: x["HostConfig"].update(NanoCpus=2000000000),
            lambda x: x["HostConfig"].update(Memory=1073741824), lambda x: x["HostConfig"].update(MemorySwap=1073741824),
            lambda x: x["HostConfig"].update(PidsLimit=128), lambda x: x["HostConfig"].update(Tmpfs={}),
            lambda x: x["HostConfig"]["PortBindings"]["5432/tcp"][0].update(HostIp="0.0.0.0"))
        for mutate in mutations:
            row, command, _ = self.fixture(mutate=mutate)
            self.assertEqual(row["error_code"], "SQL_OWNED_CLEANUP_ISOLATION_MISMATCH")
            self.assertEqual(command.call_count, 1)

    def test_remove_error_and_post_remove_presence_stay_failed(self):
        for options in ({"rm_failed": True}, {"remains": True}):
            row, _, _ = self.fixture(**options)
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertFalse(row["command_response_removal_verified"])

    def test_wrong_nonce_or_extra_journal_fields_never_issue_command(self):
        intent = ownership.make_intent(NONCE, "approval", RUN)
        intent["extra"] = "PRIVATE_FIXTURE"
        command = Mock()
        row = subject.cleanup_from_intent(intent, command)
        command.assert_not_called()
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_ambiguous_duplicate_key_or_oversized_inspect_is_rejected(self):
        for output in ("[]", "[{},{}]", '[{"Id":"a","Id":"b"}]', "x"*16385):
            with self.assertRaises(ValueError):
                subject.inspect_item(self.result(output=output))

    def test_raw_command_exception_is_redacted_and_never_cleanup_success(self):
        row = subject.cleanup_from_intent(ownership.make_intent(NONCE, "approval", RUN), Mock(side_effect=OSError("PRIVATE_FIXTURE")))
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_parent_tree_must_be_closed_before_fallback_actor_construction(self):
        intent = ownership.make_intent(NONCE, "approval", RUN)
        for parent in ({}, {"owned_job_profile": {"cleanup_confirmed": True, "last_job_accounting": None}}):
            with self.assertRaisesRegex(ValueError, "SQL_OWNED_CLEANUP_PARENT_TREE_NOT_CLOSED"):
                subject.OwnedCleanupCommand(intent, parent, object(), "C:\\fixture-docker.exe")

    def actor(self):
        actor = object.__new__(subject.OwnedCleanupCommand)
        actor.intent = ownership.make_intent(NONCE, "approval", RUN)
        actor.docker, actor.resources, actor.admitted_id, actor.profiles = "fixture-docker", SimpleNamespace(windows=object()), None, []
        actor.started, actor.calls = 1, 0
        return actor

    def test_actor_cannot_remove_unadmitted_ID_or_use_foreign_target(self):
        actor = self.actor()
        for arguments in (["rm", "--force", IDENTIFIER], ["inspect", "other"], ["prune"], ["--host", "tcp://other", "inspect"]):
            with self.assertRaisesRegex(ValueError, "SQL_OWNED_CLEANUP_TARGET_NOT_ADMITTED"):
                actor(arguments)

    def test_actor_binds_local_endpoint_three_second_owned_query_and_preserves_cleanup_profiles(self):
        actor = self.actor()
        profile = {"limits_readback": {"verified": True}, "cleanup_confirmed": True, "owned_tree_empty": True,
            "job_handle_closed": True, "last_job_accounting": {"active_processes": 0}}
        owned = SimpleNamespace(profile=profile)
        seen = []
        def query(args, **kwargs):
            seen.append((args, kwargs["timeout"]))
            kwargs["process_factory"](args, cwd=subject.c.ROOT, stdin=subject.subprocess.PIPE,
                stdout=subject.subprocess.PIPE, stderr=subject.subprocess.PIPE,
                creationflags=subject.subprocess.CREATE_NO_WINDOW|subject.subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            return self.result(output=json.dumps([item_for(actor.intent)]))
        with patch.object(subject, "bounded_observation_run", side_effect=query), \
                patch.object(subject, "OwnedSQLJobProcess", return_value=owned) as launched, \
                patch.object(subject.time, "monotonic", return_value=1.1), \
                patch.object(subject, "grace_resource_checkpoint") as checkpoint:
            actor(["inspect", actor.intent["container_name"]])
        self.assertEqual(actor.admitted_id, IDENTIFIER)
        self.assertEqual(seen, [(["fixture-docker", "--host", subject.LOCAL_DOCKER_HOST, "inspect", actor.intent["container_name"]], 3)])
        self.assertEqual(actor.profiles, [profile])
        self.assertEqual(launched.call_args.kwargs["allowed_executables"], ["fixture-docker"])
        self.assertNotIn("DOCKER_HOST", launched.call_args.kwargs["env"])
        checkpoint.assert_called_once_with(actor.resources, 1.1)

    def test_missing_job_readback_cannot_make_backend_cleanup_confirmed(self):
        actor = self.actor()
        actor.profiles = [{"limits_readback": None, "last_job_accounting": None}]
        with patch.object(subject.OwnedCleanupCommand, "__call__", return_value=self.result(1, error="No such container")):
            row = subject.cleanup_from_intent(actor.intent, actor)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertIsNone(row["backend_container_cleanup_confirmed"])

    def post_query_fixture(self, *, elapsed=1.1, error=None):
        actor = self.actor()
        profile = {"cleanup_confirmed": True, "owned_tree_empty": True, "job_handle_closed": True}
        owned = SimpleNamespace(profile=profile)
        def query(args, **kwargs):
            kwargs["process_factory"](args, cwd=subject.c.ROOT, stdin=subject.subprocess.PIPE,
                stdout=subject.subprocess.PIPE, stderr=subject.subprocess.PIPE,
                creationflags=subject.subprocess.CREATE_NO_WINDOW|subject.subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            return self.result(output=json.dumps([item_for(actor.intent)]))
        with patch.object(subject, "bounded_observation_run", side_effect=query), \
                patch.object(subject, "OwnedSQLJobProcess", return_value=owned), \
                patch.object(subject.time, "monotonic", return_value=elapsed), \
                patch.object(subject, "grace_resource_checkpoint", side_effect=error):
            with self.assertRaises(ValueError) as caught:
                actor(["inspect", actor.intent["container_name"]])
        self.assertIsNone(actor.admitted_id)
        self.assertEqual(actor.profiles, [profile])
        return str(caught.exception)

    def test_post_query_teardown_wall_cannot_exceed_scope_and_admit_removal(self):
        self.assertEqual(self.post_query_fixture(elapsed=16.1), "STOP_SQL_OWNED_CLEANUP_WALL_TIME")

    def test_post_query_resource_pressure_cannot_admit_further_removal(self):
        self.assertEqual(self.post_query_fixture(error=ValueError("STOP_SQL_CALL_GRACE_RESOURCE_PRESSURE")),
            "STOP_SQL_CALL_GRACE_RESOURCE_PRESSURE")
