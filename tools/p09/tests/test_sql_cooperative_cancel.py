"""Event API mocks and additive resource semantics, not Docker/SQL acceptance."""
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

import sql_cooperative_cancel as subject

NAME = subject.PREFIX+"12345678-1234-4234-8234-123456789abc"


class SQLCooperativeCancelTests(unittest.TestCase):
    def native(self):
        return SimpleNamespace(CreateEventW=Mock(return_value=11), OpenEventW=Mock(return_value=12),
            SetEvent=Mock(return_value=True), WaitForSingleObject=Mock(return_value=258), CloseHandle=Mock(return_value=True))

    def test_create_manual_reset_unset_event_is_non_inheritable(self):
        native = self.native()
        with patch.object(subject.ctypes, "get_last_error", return_value=0):
            event = subject.CancelEvent(NAME, create=True, native=native)
        native.CreateEventW.assert_called_once_with(None, True, False, NAME)
        self.assertFalse(event.is_set())
        event.close()

    def test_child_open_requests_synchronization_only_not_signal_rights(self):
        native = self.native()
        event = subject.CancelEvent.open(NAME, native=native)
        native.OpenEventW.assert_called_once_with(subject.SYNCHRONIZE, False, NAME)
        with self.assertRaisesRegex(ValueError, "SQL_CANCEL_SIGNAL_NOT_OWNED"):
            event.request()
        native.SetEvent.assert_not_called()
        event.close()

    def test_existing_event_is_rejected_closed_and_never_signaled(self):
        native = self.native()
        with patch.object(subject.ctypes, "get_last_error", return_value=183):
            with self.assertRaisesRegex(ValueError, "SQL_CANCEL_ALREADY_EXISTS"):
                subject.CancelEvent(NAME, create=True, native=native)
        native.CloseHandle.assert_called_once_with(11)
        native.SetEvent.assert_not_called()

    def test_arbitrary_global_name_or_non_v4_uuid_is_rejected(self):
        for name in ("Global\\PRIVATE", NAME.replace("4234", "1234"), NAME.upper(), "", None):
            with self.assertRaises(ValueError):
                subject.CancelEvent.open(name, native=self.native())

    def test_null_create_or_open_handle_is_failure(self):
        for create in (True, False):
            native = self.native()
            native.CreateEventW.return_value = native.OpenEventW.return_value = None
            with self.assertRaises(ValueError):
                subject.CancelEvent(NAME, create=create, native=native)
            native.CloseHandle.assert_not_called()

    def test_owner_signal_and_nonblocking_wait_preserve_state(self):
        native = self.native()
        with patch.object(subject.ctypes, "get_last_error", return_value=0):
            event = subject.CancelEvent(NAME, create=True, native=native)
        event.request()
        native.SetEvent.assert_called_once_with(11)
        native.WaitForSingleObject.return_value = 0
        self.assertTrue(event.is_set())
        native.WaitForSingleObject.assert_called_with(11, 0)
        event.close()

    def test_signal_wait_and_close_fail_closed(self):
        native = self.native()
        with patch.object(subject.ctypes, "get_last_error", return_value=0):
            event = subject.CancelEvent(NAME, create=True, native=native)
        native.SetEvent.return_value = False
        with self.assertRaisesRegex(ValueError, "SQL_CANCEL_SIGNAL_FAILED"):
            event.request()
        native.WaitForSingleObject.return_value = 0xffffffff
        with self.assertRaisesRegex(ValueError, "SQL_CANCEL_WAIT_FAILED"):
            event.is_set()
        native.CloseHandle.return_value = False
        with self.assertRaisesRegex(ValueError, "SQL_CANCEL_CLOSE_FAILED"):
            event.close()
        self.assertFalse(event.closed)

    def test_double_close_does_not_use_stale_handle(self):
        native = self.native()
        event = subject.CancelEvent.open(NAME, native=native)
        event.close()
        event.close()
        native.CloseHandle.assert_called_once_with(12)
        with self.assertRaisesRegex(ValueError, "SQL_CANCEL_HANDLE_CLOSED"):
            event.is_set()

    def resource(self, requested=False, reason=None):
        sample, checkpoint = Mock(return_value={"sample": "original"}), Mock(return_value="original-checkpoint")
        class Original:
            def __init__(self):
                self.stop, self.reason = threading.Event(), reason
            def _failed(self, code):
                self.reason = self.reason or code
                self.stop.set()
            def sample(self, *args, **kwargs):
                return sample(*args, **kwargs)
            def checkpoint_io(self):
                if self.stop.is_set():
                    raise ValueError(self.reason)
                return checkpoint()
        cancel = SimpleNamespace(is_set=Mock(return_value=requested))
        resources = subject.cancellable_resource_type(Original, cancel)()
        return resources, cancel, sample, checkpoint, Original

    def test_normal_sample_and_checkpoint_call_original_methods_unchanged(self):
        resources, _, sample, checkpoint, original = self.resource()
        self.assertIsInstance(resources, original)
        self.assertEqual(resources.sample("same", mode="same"), {"sample": "original"})
        sample.assert_called_once_with("same", mode="same")
        self.assertEqual(resources.checkpoint_io(), "original-checkpoint")
        checkpoint.assert_called_once()

    def test_checkpoint_cancellation_sets_original_latch_before_more_IO(self):
        resources, _, _, checkpoint, _ = self.resource(True)
        with self.assertRaisesRegex(ValueError, subject.CANCEL_REASON):
            resources.checkpoint_io()
        self.assertTrue(resources.stop.is_set())
        checkpoint.assert_not_called()

    def test_runtime_sample_observes_cancel_after_original_sampling(self):
        resources, _, sample, _, _ = self.resource(True)
        resources.sample()
        sample.assert_called_once()
        self.assertEqual(resources.reason, subject.CANCEL_REASON)

    def test_existing_resource_stop_reason_is_not_overwritten(self):
        resources, _, _, _, _ = self.resource(True, "STOP_EXISTING_FIXTURE")
        resources.sample()
        self.assertEqual(resources.reason, "STOP_EXISTING_FIXTURE")

    def test_cancel_observation_error_is_latched_closed_not_ignored(self):
        resources, cancel, _, _, _ = self.resource()
        cancel.is_set.side_effect = OSError("PRIVATE_FIXTURE")
        with self.assertRaisesRegex(ValueError, subject.OBSERVATION_FAILURE):
            resources.checkpoint_io()
        self.assertTrue(resources.stop.is_set())

    def test_non_boolean_observation_cannot_authorize_more_IO(self):
        resources, cancel, _, _, _ = self.resource()
        cancel.is_set.return_value = 0
        with self.assertRaisesRegex(ValueError, subject.OBSERVATION_FAILURE):
            resources.checkpoint_io()

    def test_original_authority_admission_masks_new_reason_without_changing_actual_stop(self):
        from run_formula_issuer_authority_sql_probe import AdmissionRefusal
        from sql_call_accounting import closed_code
        resources = SimpleNamespace(samples=[], reason=subject.CANCEL_REASON)
        error = AdmissionRefusal(ValueError(subject.CANCEL_REASON), resources)
        self.assertEqual(str(error), "redacted")
        self.assertEqual(closed_code(error), "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE")
        self.assertEqual(resources.reason, subject.CANCEL_REASON)
        self.assertFalse(error.diagnostics["heavy_work_started"])
