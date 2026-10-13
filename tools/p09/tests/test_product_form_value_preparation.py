"""New successor guards without modifying any predecessor source lock or test."""
from pathlib import Path
import unittest
from tools.p09 import qualify_product_form_value_preparation as q


class ProductFormValuePreparationGuards(unittest.TestCase):
    def test_complete_product_inverse_and_original_vs0_bytes_are_real(self):
        raw = q.public.bounded_bytes(q.ROOT / q.LIB, 2 * 1024 * 1024)
        archived = q.public.checked(q.ROOT / q.ARCHIVE, q.OLD_LIB)
        q.product_inverse(raw, archived)
        for changed in (raw + b"\n", raw.replace(q.DELTA, b"", 1), raw + q.DELTA):
            with self.assertRaises(ValueError): q.product_inverse(changed, archived)
        with self.assertRaises(ValueError): q.product_inverse(raw, archived + b"\n")

    def test_all_original_seven_sources_and_1443_authentic_graph_inputs_are_preserved(self):
        actual = q.authority()
        self.assertEqual(actual["original_physical_view_files"], 1443)
        self.assertEqual(actual["original_physical_view_bytes"], 48223297)
        self.assertTrue(actual["graph_raw_bytes_preserved"])
        self.assertFalse(actual["complete_original_capsule_reexecution_this_successor"])
        self.assertFalse(actual["current_old_verifier_pass_claimed"])

    def test_snapshot_is_exact_inventory_not_native_candidate(self):
        files = q.snapshot()
        self.assertEqual(len(files), 11)
        self.assertEqual(sum(map(len, files.values())), 167304)
        self.assertEqual(q.oracle.sha(files["fixture-manifest.json"]), q.MANIFEST_SHA)
        q.match_snapshot(files, dict(files))

    def test_changed_bytes_missing_files_and_extra_files_fail_closed(self):
        files = q.snapshot()
        for changed in ({**files, "actual.output.hwpx": b"wrong"},
                        {name: raw for name, raw in files.items() if name != "fixture-manifest.json"},
                        {**files, "extra.hwpx": b"wrong"}):
            with self.assertRaises(ValueError): q.match_snapshot(files, changed)

    def test_compiled_product_inventory_rejects_duplicates_skip_and_filter(self):
        names = sorted(q.INTEGRATION)
        good = "\n".join(f"test {name} ... ok" for name in names)
        good += "\ntest result: ok. 10 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n"
        self.assertEqual(q.prior.protocol(good, q.INTEGRATION, 10)["passed"], 10)
        for changed in (good.replace(names[0], names[1]), good.replace("... ok", "... ignored", 1),
                        good.replace("0 filtered out", "1 filtered out"), good + f"test {names[0]} ... ok\n"):
            with self.assertRaises(ValueError): q.prior.protocol(changed, q.INTEGRATION, 10)

    def test_private_inventory_declares_only_unrelated_vs0_unit_filtered(self):
        good = "\n".join(f"test {name} ... ok" for name in sorted(q.PRIVATE))
        good += "\ntest result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out; finished in 1s\n"
        self.assertEqual(q.prior.protocol(good, q.PRIVATE, 2, 1)["filtered_unrelated"], 1)
        with self.assertRaises(ValueError): q.prior.protocol(good.replace("1 filtered", "2 filtered"), q.PRIVATE, 2, 1)

    def test_evidence_cannot_target_private_originals_or_traverse(self):
        self.assertEqual(q.evidence_path(q.ROOT / q.CAPSULE), q.ROOT / q.CAPSULE)
        for path in (Path("relative.json"), q.ROOT / "implementation/p09/evidence/private/anything.json",
                     q.ROOT / "implementation/p09/evidence/../evidence" / Path(q.CAPSULE).name,
                     q.ROOT / q.PREDECESSOR):
            with self.assertRaises(ValueError): q.evidence_path(path)


if __name__ == "__main__": unittest.main()
