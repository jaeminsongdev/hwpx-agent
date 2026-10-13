import json
import unittest
from tools.p09 import qualify_current_native_form_diagnostic_admission as q

class CurrentDiagnosticAdmissionTests(unittest.TestCase):
    def test_exact_two_original_sources_preserved_and_current_old_failure_retained(self):
        old,prep,component=q.lineage()
        self.assertEqual(len(old["source_sha256"]),50)
        self.assertEqual(set(q.ARCHIVES),{"Cargo.lock",q.sdk.LIB})
        self.assertEqual(len(prep["cases"]),15)
        self.assertEqual(component["new_native_batch"]["state"],"not_run")
    def test_complete_lock_inverse_rejects_unrelated_bytes_or_missing_extra_dependencies(self):
        current=q.public.bounded_bytes(q.ROOT/"Cargo.lock",2097152)
        original=q.public.checked(q.ROOT/q.ARCHIVES["Cargo.lock"][0],q.ARCHIVES["Cargo.lock"][1])
        q.lock_inverse(current,original)
        for bad in (current+b"\n",current.replace(b' "artifact-service",\n',b"",1),
                    current.replace(b' "revision-service",\n',b' "revision-service",\n "revision-service",\n',1)):
            with self.assertRaises(ValueError):q.lock_inverse(bad,original)
    def test_whole_root_inverse_rejects_unrelated_additions(self):
        current=q.public.checked(q.ROOT/q.sdk.LIB,q.sdk.CURRENT_LIB)
        archived=q.public.checked(q.ROOT/q.sdk.ARCHIVE,q.sdk.history.OLD_LIB)
        q.sdk.project(current,archived)
        with self.assertRaises(ValueError):q.sdk.project(current+b"\n",archived)
    def test_fixed_append_only_paths_reject_old_private_traversal_and_aliases(self):
        self.assertEqual(q.path_guard(q.ROOT/q.CAPSULE,None),q.ROOT/q.CAPSULE)
        for bad in (q.ROOT/q.binding.PREPARATION,q.ROOT/q.COMPONENT,q.ROOT/"implementation/p09/evidence/private/x.json",
                    q.ROOT/"implementation/p09/evidence/../evidence/p09-36-native-form-diagnostic-current-admission.r02.json"):
            with self.assertRaises(ValueError):q.path_guard(bad,None)
    def test_original_harness_and_component_sources_remain_exact(self):
        component=json.loads(q.public.checked(q.ROOT/q.COMPONENT,q.COMPONENT_SHA,524288))
        for name,digest in component["source_sha256"].items():q.public.checked(q.ROOT/name,digest)
        q.public.checked(q.ROOT/q.q.HARNESS,q.q.HARNESS_SHA)
        self.assertEqual(len(q.binding.attempt_paths("p09-35-20261003-r02")),15)
    def test_strict_types_and_case_prefixes_not_coerced(self):
        for actual,expected in ((1,True),(True,1),(15.0,15)):
            with self.assertRaises(ValueError):q.exact(actual,expected,"invalid_type")
        for bad in ("../x","C:/x","a\\b",None,1,"a"*41):
            with self.assertRaises(ValueError):q.binding.attempt_paths(bad)
    def test_all_historical_artifact_keys_follow_original_windows_receipt_without_hash_changes(self):
        component=json.loads(q.public.checked(q.ROOT/q.COMPONENT,q.COMPONENT_SHA,524288))
        actual={}
        for row,path,trace,passed in q.binding.previous.verified_traces():
            actual[str((path/"target-trace.json").relative_to(q.ROOT))]=q.q.sha(q.public.bounded_bytes(path/"target-trace.json",131072))
            actual.update({str((path/name).relative_to(q.ROOT)):data["sha256"] for name,data in q.binding.artifact_snapshot(path,trace,passed).items()})
        self.assertEqual(actual,component["historical_trace_and_artifact_sha256"])
        self.assertEqual(len(actual),22)

if __name__=="__main__":unittest.main()
