"""Guarded contracts; fixture results are not product/Native acceptance."""
import unittest

MODULE=API=CHUNK=RAW=None
CHECKPOINT=lambda:None


class Tests(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        if any(v is None for v in (MODULE,API,CHUNK,RAW)):raise ValueError("WORKSPACE_GUARDED_FIXTURE_REQUIRED")
    def tearDown(self):CHECKPOINT()
    def test_reader_is_private_and_keeps_all_original_wrappers(self):
        before=API.AcceptanceReader
        api,proof=MODULE.reader_api(API,CHUNK,RAW,"bounded-fixture-receipt")
        self.assertIs(API.AcceptanceReader,before)
        self.assertIsNot(api.AcceptanceReader,before)
        self.assertTrue(issubclass(api.AcceptanceReader,before))
        self.assertTrue(proof["original_MRO_preserved_with_one_leaf_insert"])
        self.assertEqual(proof["original_checkpoints_hash_parse_pacing_and_stream_statements_removed"],0)
    def test_only_preparation_modes_and_frozen_runtime_source(self):
        self.assertEqual(MODULE.MODES,("workspace-code","code","preflight","qualify"))
        self.assertEqual(MODULE.BRIDGE["path"],"tools/p09/current_queue_successor_wire_runtime_v2.py")
        self.assertEqual(MODULE.BRIDGE["bytes"],11932)
        self.assertEqual(len(MODULE.BRIDGE["sha256"]),64)


if __name__=="__main__":unittest.main()
