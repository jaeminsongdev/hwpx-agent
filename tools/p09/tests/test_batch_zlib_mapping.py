"""Closed-table and original-Projection contracts; not Native evidence."""
import copy
import hashlib
from pathlib import Path
import unittest
import batch_zlib_mapping as module
import batch_engine_connection as entry
import current_stored_runtime_scope as scope

SOURCE_PINS=None
CHECKPOINT=lambda:None


def exact(a,b,code):
    if type(a) is not type(b) or a!=b:raise ValueError(code)


class TableContracts(unittest.TestCase):
    def fixture(self):
        originals=[];records=[]
        for index in range(162):
            old=dict(path='implementation/p09/evidence/fixture'+str(index)+'.json',bytes=1,sha256='0'*64)
            physical=dict(path='old-corpus/input'+str(index)+'.json',bytes=1,sha256='1'*64)
            originals.append(dict(semantic_original_pin=old,physical_envelope_pin=physical))
            records.append(dict(semantic_pin=copy.deepcopy(old),old_physical_pin=copy.deepcopy(physical),
                candidate_encoded_bytes=3,candidate_sha256='2'*64))
        report=dict(state='FAILED_BASELINE_AND_UNADOPTED_ZLIB_MEMORY_CANDIDATE_NOT_NATIVE',
            GO_authorized=False,candidate_physical_files_published=False,
            candidate=dict(codec_pin=copy.deepcopy(module.CODEC1),
                state='PASS_FULL162_ZLIB_MEMORY_COMPARISON_NOT_ADOPTED_OR_NATIVE',completed_mappings=162,
                mapping_records=records))
        return report,originals

    def test_full162_exact_generation_and_originals(self):
        report,originals=self.fixture();rows=module.rows_from_comparison(report,originals,scope,exact)
        self.assertEqual(len(rows),162)
        self.assertEqual([r['semantic_original_pin'] for r in rows],[r['semantic_original_pin'] for r in originals])
        self.assertEqual(rows[0]['physical_envelope_pin']['path'],module.PREFIX+'case165-zlib-g001-001.envelope.v1.json')

    def test_subset_or_wrong_original_denied(self):
        report,originals=self.fixture()
        with self.assertRaises(ValueError):module.rows_from_comparison(report,originals[:-1],scope,exact)
        originals[0]['physical_envelope_pin']['bytes']=2
        with self.assertRaises(ValueError):module.rows_from_comparison(report,originals,scope,exact)

    def test_code_and_exe_cannot_become_mapped_original(self):
        for name in ('crates/product-cli/src/lib.rs','target/test.exe'):
            report,originals=self.fixture()
            report['candidate']['mapping_records'][0]['semantic_pin']['path']=name
            originals[0]['semantic_original_pin']['path']=name
            with self.assertRaisesRegex(ValueError,'RECEIPTS_ONLY'):
                module.rows_from_comparison(report,originals,scope,exact)

    def test_invalid_pin_and_unqualified_report_denied(self):
        report,originals=self.fixture();report['candidate']['mapping_records'][0]['candidate_encoded_bytes']=True
        with self.assertRaises(ValueError):module.rows_from_comparison(report,originals,scope,exact)
        report,originals=self.fixture();report['GO_authorized']=True
        with self.assertRaisesRegex(ValueError,'EXACT_UNADOPTED'):
            module.rows_from_comparison(report,originals,scope,exact)


class ProjectionContracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT();root=Path(module.__file__).resolve().parents[2]
        loader=entry.bootstrap_loader(root)
        libs,_=loader.load(root,[SOURCE_PINS['tools/p09/'+n+'.py'] for n in
            ('runtime_record_envelope_v1','runtime_record_envelope_v2','runtime_envelope_source_projection_v1')],
            {'current_stored_runtime_scope':scope})
        self.source=libs.runtime_envelope_source_projection_v1;self.codec=libs.runtime_record_envelope_v2
        self.raw=b'{}';self.encoded=self.codec.encode(self.raw,CHECKPOINT);self.rows=[]
        for index in range(162):
            self.rows.append(dict(schema_version=module.SCHEMA,next_case=165,
                semantic_original_pin=dict(path='implementation/p09/evidence/fixture'+str(index)+'.json',
                    bytes=2,sha256=hashlib.sha256(self.raw).hexdigest()),
                physical_envelope_pin=dict(path=module.PREFIX+f'case165-zlib-g001-{index+1:03}.envelope.v1.json',
                    bytes=len(self.encoded),sha256=hashlib.sha256(self.encoded).hexdigest())))
        self.required={r['semantic_original_pin']['path']:r['semantic_original_pin'] for r in self.rows}

    def test_all_original_methods_semantic_scope_and_ordinary_exe_retained(self):
        methods=dict(vars(self.source.Projection));extra=dict(path='target/ordinary.exe',bytes=1,sha256='3'*64)
        self.required[extra['path']]=extra
        factory=module.projection_factory(self.source,self.codec,self.rows,exact)
        projection=factory.project(self.required,CHECKPOINT)
        self.assertTrue(all(vars(self.source.Projection).get(n) is v for n,v in methods.items()))
        self.assertEqual(dict(projection.semantic_pins),self.required)
        self.assertEqual(dict(projection.physical_pins[extra['path']]),extra)
        self.assertEqual(len(projection.physical_pins),163)

    def test_actual_v2_decode_and_changed_carrier_denial(self):
        factory=module.projection_factory(self.source,self.codec,self.rows,exact)
        projection=factory.project(self.required,CHECKPOINT);row=self.rows[0]
        args=(row['semantic_original_pin']['path'],row['physical_envelope_pin'])
        self.assertEqual(projection.decode_fresh(*args,self.encoded,CHECKPOINT),self.raw)
        with self.assertRaises(ValueError):projection.decode_fresh(*args,self.encoded+b'x',CHECKPOINT)

    def test_public_table_copy_cannot_change_closed_factory(self):
        factory=module.projection_factory(self.source,self.codec,self.rows,exact)
        factory.rows[0]['physical_envelope_pin']['sha256']='4'*64
        projection=factory.project(self.required,CHECKPOINT)
        self.assertEqual(projection.decode_fresh(self.rows[0]['semantic_original_pin']['path'],
            self.rows[0]['physical_envelope_pin'],self.encoded,CHECKPOINT),self.raw)

    def test_unknown_semantic_and_wrong_generation_denied(self):
        factory=module.projection_factory(self.source,self.codec,self.rows,exact)
        other=dict(path='target/ordinary.exe',bytes=1,sha256='3'*64)
        with self.assertRaisesRegex(ValueError,'ONLY_CLOSED162'):
            factory.source.descriptor(other,self.rows[0]['physical_envelope_pin'],next_case=165)
        self.rows[0]['physical_envelope_pin']['path']=module.PREFIX+'case165-zlib-g002-001.envelope.v1.json'
        with self.assertRaises(ValueError):module.projection_factory(self.source,self.codec,self.rows,exact)


if __name__=='__main__':unittest.main()
