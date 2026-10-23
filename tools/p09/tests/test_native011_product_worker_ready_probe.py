import ast
from pathlib import Path
import unittest
import native011_product_worker_ready_probe as m


class Tests(unittest.TestCase):
    def fixture(self):
        required={str(i):{} for i in range(202)}
        value=dict(state='COMPLETED_ORIGINAL_INHERITED_WORKER_NOT_PRODUCT_ACCEPTANCE',original_worker_exit_code=1,error_code=None,
            cleanup_confirmed=True,cleanup=dict(import_finder_restored=True,inherited_source_cleanup_confirmed=True),
            source_count=202,final_fresh_hashes=202,inherited_sources_closed=202,source_pin_sha256='model',
            source_closing_before_original_READY=True,every_declared_source_read_at_least_twice=True,
            original_GO_observed=False,original_input_reads=1,product_creation_attempts=0,GO_written_by_child=False,
            Native_or_product_acceptance_qualified=False)
        return value,required
    def test_closed_preparation_outputs_do_not_allow_native_go_or_overwrite_ids(self):
        self.assertIn('ready001',m.output_for(1))
        for value in (0,4,True,'1'):
            with self.assertRaises(ValueError):m.output_for(value)
    def test_actual_child202_requires_full_closing_and_real_eof_not_product_acceptance(self):
        child,required=self.fixture();m.validate_child(child,required,lambda value:'model')
        for field,value in (('original_GO_observed',True),('product_creation_attempts',1),('final_fresh_hashes',201),
            ('inherited_sources_closed',201),('original_worker_exit_code',0),('Native_or_product_acceptance_qualified',True)):
            child,required=self.fixture();child[field]=value
            with self.assertRaises(ValueError):m.validate_child(child,required,lambda value:'model')
    def test_source_digest_and_every_input_are_required_not_count_alone(self):
        child,required=self.fixture()
        with self.assertRaises(ValueError):m.validate_child(child,required,lambda value:'changed')
        child['every_declared_source_read_at_least_twice']=False
        with self.assertRaises(ValueError):m.validate_child(child,required,lambda value:'model')
    def test_original_no_go_sink_gate_and_owned_cleanup_are_explicit(self):
        text=(Path(__file__).resolve().parents[3]/m.SELF).read_text(encoding='utf-8');tree=ast.parse(text)
        names={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
        self.assertIn('NoGoReadySink',names);self.assertIn('Gate',names);self.assertIn('AssignProcessToJobObject',names)
        self.assertIn('source_declaration',names);self.assertIn('bind_gate',names);self.assertIn('cleanup_handles',names)
        self.assertIn('gate.write(protocol.GO)',text);self.assertIn('not gate.written',text)
        self.assertNotIn('process.stdin.write(',text);self.assertNotIn('run_owned(',text)
