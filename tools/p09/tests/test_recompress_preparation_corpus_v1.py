import copy
import unittest
import recompress_preparation_corpus_v1 as module


class Tests(unittest.TestCase):
    def rows(self):
        return [dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1", next_case=165,
            semantic_original_pin=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{i:03}.v1.json", bytes=100, sha256="a"*64),
            physical_envelope_pin=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{i:03}.envelope.v1.json", bytes=50, sha256="b"*64))
            for i in range(1, 69)]

    def test_exact_ordered_batch_and_last_batch(self):
        rows = self.rows()
        self.assertEqual(module.select(rows, 1, 8), rows[:8])
        self.assertEqual(module.select(rows, 65, 4), rows[64:])

    def test_batch_bounds_and_bool(self):
        for first, count in ((0, 8), (1, 9), (68, 2), (True, 1), (1, True)):
            with self.assertRaises(ValueError): module.select(self.rows(), first, count)

    def test_complete_inventory_and_bijection_required(self):
        rows = self.rows()
        with self.assertRaises(ValueError): module.select(rows[:-1], 1, 8)
        rows[-1] = copy.deepcopy(rows[0])
        with self.assertRaises(ValueError): module.select(rows, 1, 8)

    def test_source_and_unknown_current_case_rejected(self):
        for path in ("tools/p09/source.py", "implementation/p09/evidence/p09-361-case165-current-runtime-run004.v1.json"):
            rows = self.rows(); rows[0]["semantic_original_pin"]["path"] = path
            with self.assertRaises(ValueError): module.select(rows, 1, 8)

    def test_schema_extra_fields_and_context_rejected(self):
        for key, value in (("extra", True), ("schema_version", "other"), ("next_case", True)):
            rows = self.rows(); rows[0][key] = value
            with self.assertRaises(ValueError): module.select(rows, 1, 8)

    def test_destination_never_original_or_existing_path(self):
        old = self.rows()[0]["physical_envelope_pin"]["path"]
        self.assertNotEqual(module.destination(old), old)
        self.assertTrue(module.destination(old).endswith(".level6.envelope.v1.json"))
        failed = old.replace(".envelope.v1.json", ".failed.envelope.v1.json")
        self.assertTrue(module.destination(failed).endswith(".failed.level6.envelope.v1.json"))
        rows = self.rows(); rows[0]["physical_envelope_pin"]["path"] = failed
        self.assertEqual(module.select(rows, 1, 1), rows[:1])
        for bad in ("../case112-runtime-run001.envelope.v1.json", old.replace("inputs/", "inputs/../"), module.destination(old)):
            with self.assertRaises(ValueError): module.destination(bad)

    def test_new_descriptor_keeps_all_original_fields(self):
        old = self.rows()[0]; before = copy.deepcopy(old)
        pin = dict(path=module.destination(old["physical_envelope_pin"]["path"]), bytes=40, sha256="c"*64)
        row = module.new_descriptor(old, pin)
        self.assertEqual(old, before)
        self.assertEqual({k:v for k,v in row.items() if k != "physical_envelope_pin"},
            {k:v for k,v in old.items() if k != "physical_envelope_pin"})
        with self.assertRaises(ValueError): module.new_descriptor(old, old["physical_envelope_pin"])
