import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_product_worker_scope as m
import native011_ready_scope_connection as old
import current_stored_runtime_scope as scope


class Tests(unittest.TestCase):
    def pin(self,name):return dict(path=name,bytes=1,sha256='0'*64)
    def raw(self):return (Path(__file__).resolve().parents[3]/m.SOURCE['path']).read_bytes()
    def fixture(self):
        prior={f'tools/p09/model{i}.py':self.pin(f'tools/p09/model{i}.py') for i in range(201)}
        entry=self.pin(m.CHILD);required=scope.extend(prior,{m.CHILD:entry})
        pins=scope.extend(required,{f'qualifier/model{i}.py':self.pin(f'qualifier/model{i}.py') for i in range(11)})
        child=dict(source_count=202,final_fresh_hashes=202,inherited_sources_closed=202,source_pin_sha256=m.pin_digest(required),
            original_input_reads=1,original_GO_observed=False,product_creation_attempts=0,original_worker_exit_code=1,
            cleanup_confirmed=True,every_declared_source_read_at_least_twice=True)
        proof=dict(state='PASS_PRODUCT_CHILD202_SOURCE_AND_ORIGINAL_READY_REAL_EOF_NOT_NATIVE',cleanup_confirmed=True,
            fresh_inputs=213,final_fresh_hashes=213,actual_source_files=202,actual_child_launches=1,
            GO_authorized=False,actual_product_GO_writes=0,parent_frame_state='CLOSED',inner_job_final={'active_processes':0},
            child=child,readiness=dict(readiness_confirmed=True,readiness_limit_seconds=15,readiness_elapsed_seconds=7.5,
                actual_original_GO_written=False,stopped=True),original_worker_source_scope_pin_sha256=m.pin_digest(required),
            source_pins=list(pins.values()),worker_source_declaration={'new_child_entry_pin':entry},
            source_handoff=dict(failed=False,preparation_START_sent=True,source_flags_and_descriptor_cleanup_errors=[]))
        for key,count in (('first_source_boundary',1),('second_source_boundary',2)):
            proof[key]=dict(worker_required_count=202,parent_input_count=202,actual_parent_byte_boundaries=count,exact_whole_worker_pin_coverage=True)
        return prior,entry,required,pins,proof
    def test_exact_qualified202_from_original201_and_new_entry_not_native_acceptance(self):
        prior,entry,required,pins,proof=self.fixture()
        actual,dependencies=m.qualified(proof,prior,entry,scope)
        self.assertEqual(actual,required);self.assertEqual(dependencies,pins);self.assertEqual(len(prior),201)
    def test_partial_eof_product_or_commit_claim_cannot_be_admitted(self):
        for field,value in (('parent_frame_state','COMMITTED'),('actual_product_GO_writes',1),('final_fresh_hashes',212)):
            prior,entry,required,pins,proof=self.fixture();proof[field]=value
            with self.assertRaises(ValueError):m.qualified(proof,prior,entry,scope)
        prior,entry,required,pins,proof=self.fixture();proof['child']['source_pin_sha256']='bad'
        with self.assertRaises(ValueError):m.qualified(proof,prior,entry,scope)
    def test_qualified_source_values_must_match_every_pin_not_just_202_count(self):
        prior,entry,required,pins,proof=self.fixture();proof=copy.deepcopy(proof);proof['source_pins'][0]['bytes']=2
        with self.assertRaisesRegex(ValueError,'QUALIFIED_WORKER_PINS_EXACT'):m.qualified(proof,prior,entry,scope)
    def test_entire_original_scope_inspector_inverse_and_default_function_unchanged(self):
        before=old.inspect_current;selected,proof=m.inspector(self.raw(),before)
        self.assertIs(old.inspect_current,before);self.assertTrue(proof['entire_original_scope_inspector_AST_inverse'])
        self.assertEqual(proof['expected_worker_count'],202);self.assertFalse(proof['actual_Native_or_product_qualified'])
        prior,entry,required,pins,record=self.fixture()
        history={f'history/{i}.json':self.pin(f'history/{i}.json') for i in range(419)};whole=scope.extend(required,history)
        data=NS(planned=NS(current=required,whole=whole,history=history,logical=whole),declared=NS(to_physical=scope.pins))
        class Native:pass
        class A(Native):pass
        class B(A):pass
        class Frame(B):pass
        value=selected(data,required,scope,Frame,Native)
        self.assertEqual(value['required_worker_sources'],202);self.assertFalse(value['actual_live_Frame_coverage_qualified'])
        self.assertEqual(old.inspect_current(data,prior,scope,Frame,Native)['required_worker_sources'],201)
    def test_source_or_function_drift_refused_before_control_binding(self):
        with self.assertRaises(ValueError):m.inspector(self.raw()+b'\n',old.inspect_current)
        with self.assertRaises(ValueError):m.inspector(self.raw(),lambda:None)
        with self.assertRaises(ValueError):m.bind(old,self.raw())
    def test_private_admission_adds_ten_named_controls_and_does_not_reread201(self):
        prior,entry,required,pins,record=self.fixture();reads=[]
        base=NS(required=prior,control_names=tuple('base'+str(i) for i in range(47)),readiness_pin=old.READY)
        control=NS(**{**vars(old),'admit':lambda *args,**kwargs:base})
        state,proof=m.bind(control,self.raw());q=NS(pin=lambda name:(reads.append(name) or dict(pins[name])))
        a=NS(read_exact=lambda q,pin:record,exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        result=control.admit(q,a,scope,exact_read=True)
        self.assertEqual(result.required,required);self.assertEqual(len(result.control_names),57)
        self.assertEqual(result.control_names[-10:],m.CONTROLS);self.assertEqual(state.calls,1)
        self.assertEqual(reads.count(m.CHILD),1);self.assertEqual(len(reads),12)
        self.assertTrue(state.admission['source_declaration_only']);self.assertFalse(state.admission['GO_authorized'])
        with self.assertRaises(ValueError):control.admit(q,a,scope,exact_read=True)
    def test_stale_child_entry_pin_cannot_reuse_old_ready202_as_current_freshness(self):
        prior,entry,required,pins,record=self.fixture();new_pin=dict(entry,sha256='1'*64)
        base=NS(required=prior,control_names=tuple('base'+str(i) for i in range(47)))
        control=NS(**{**vars(old),'admit':lambda *args,**kwargs:base});m.bind(control,self.raw())
        q=NS(pin=lambda name:new_pin if name==m.CHILD else pins[name]);a=NS(read_exact=lambda *args:record)
        with self.assertRaises(ValueError):control.admit(q,a,scope)
