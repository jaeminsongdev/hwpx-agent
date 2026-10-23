"""New namespace/data models only; no actual full162 qualification or files."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_worker_transport as transport
import native011_zlib_binding as module


class Native011ZlibContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.raw = (cls.root/module.SOURCE['path']).read_bytes()
        cls.transport_raw = (cls.root/transport.SOURCE['path']).read_bytes()

    def api(self):
        return module.connect(self.raw)

    def test_exact_source_and_no_execution_or_publication_entry(self):
        api = self.api()
        self.assertFalse(api.proof['Native_or_GO_qualified'])
        self.assertEqual(len(api.HISTORY_KEYS),8)
        self.assertTrue({'connect','declared_rows','historical_context','worker_graph'} <=
            set(api.proof['unchanged_function_bodies']))
        self.assertFalse(any(hasattr(api,n) for n in ('main','publish','run_product','launch')))
        with self.assertRaises(ValueError):
            module.connect(self.raw+b'\n')

    def test_new_manifest_preserves_whole_model_table_history_and_qualification(self):
        api = self.api(); rows = [{'model_descriptor':i} for i in range(162)]
        roles = {n:{'original_failure_not_pass':True} for n in api.HISTORY_KEYS}
        history = {'model_prior':{'state':'FAILED'}}
        declaration = NS(NEW_TABLE_SHA256=api.digest(rows),REFERENCE_MANIFEST={'old':'reference009'},
            OLD_TABLE_SHA256='old-table',CODEC2={'codec':'unchanged'},QUALIFICATION={'qualification':'unchanged'})
        before = copy.deepcopy((rows,roles,history))
        result = api.manifest(rows,history,roles,declaration)
        self.assertEqual(result['physical_run'],11)
        self.assertEqual(result['schema_version'],'hwpx-agent.p09-run011-zlib-manifest/v1')
        self.assertEqual(result['accepted_count_before'],158)
        self.assertEqual(result['descriptors'],rows)
        self.assertEqual(result['original_historical_input_roles'],roles)
        self.assertEqual(result['historical_predecessor_provenance'],history)
        self.assertEqual(result['physical_qualification_pin'],declaration.QUALIFICATION)
        self.assertFalse(result['GO_authorized'])
        self.assertEqual((rows,roles,history),before)
        result['descriptors'].clear()
        self.assertEqual(len(rows),162)
        with self.assertRaises(ValueError):
            api.manifest(rows[:-1],history,roles,declaration)
        with self.assertRaises(ValueError):
            api.manifest(rows,history,{},declaration)

    def test_new_hint_does_not_relabel_reference_or_mutate_old_context(self):
        api = self.api()
        previous = dict(schema_version='original-schema',index=165,run=9,step=dict(index=165,before=158),
            capsule_pin={'old':'capsule'},manifest_pin={'old':'manifest'},first_descriptor={'old':'first'},
            historical_pairs=[{'failure':'retained'}],historical_provenance={'old':'unchanged'})
        before = copy.deepcopy(previous)
        reference = NS(manifest_pin={'new':'manifest'},binding=NS(descriptors=lambda:[{'new':'first'}]))
        result = api.preparation_hint(previous,reference,dict(bytes=8,sha256='0'*64))
        self.assertEqual(result['run'],11)
        self.assertEqual(result['capsule_pin']['path'],module.WIRE)
        self.assertEqual(result['historical_pairs'],before['historical_pairs'])
        self.assertEqual(previous,before)
        with self.assertRaises(ValueError):
            api.preparation_hint(dict(previous,run=10),reference,dict(bytes=8,sha256='0'*64))

    def test_entry_projects_only_run011_zlib_paths_with_original_byte_checks(self):
        import current_queue_successor_connections as metadata
        api = self.api(); worker = transport.connect(self.transport_raw)
        rebuilt = api.entry_reconstructor(worker,metadata)
        self.assertEqual(rebuilt.__defaults__,worker.reconstruct.__defaults__)
        self.assertEqual(rebuilt.__closure__,worker.reconstruct.__closure__)
        constants = rebuilt.__code__.co_consts
        self.assertIn(module.BOOTSTRAP,constants)
        self.assertIn(module.WIRE,constants)
        self.assertNotIn(transport.BOOTSTRAP,constants)
        self.assertNotIn(transport.WIRE,constants)
        calls = []
        with self.assertRaisesRegex(ValueError,'ENTRY_FRESH_BYTES_MATCH_PIN'):
            rebuilt(transport.TASK,dict(path=module.BOOTSTRAP,bytes=1,sha256='0'*64),
                lambda *args:calls.append('read') or b'x',lambda:None,lambda:None,lambda:None)
        self.assertEqual(calls,['read'])


if __name__ == '__main__':
    unittest.main()
