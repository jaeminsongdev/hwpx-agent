import ast
import io
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_product_worker_entry as m
import current_stored_runtime_scope as scope


class Tests(unittest.TestCase):
    def argv(self):return ['--ready-handle','11','--task',m.TASK,'--source-mapping','22','123','a'*64]
    def preparation(self,*,closing=True):
        events=[];rows={'one.py':dict(path='one.py',bytes=1,sha256='0'*64)}
        q=NS(snapshots=rows,final_fresh_hashes=0)
        def finish():events.append('finish');q.final_fresh_hashes=1 if closing else 0
        q.finish=finish
        def original_worker():pass
        from types import FunctionType
        original_worker=FunctionType(original_worker.__code__,dict(arguments=lambda:['exact-case']))
        result=NS(linked=NS(state=NS(attempts=0,calls=0),window=NS(WINDOW=NS(SECONDS=10)),original_worker=original_worker))
        worker=NS(prepare=lambda *args:(events.append('prepare') or result))
        return worker,q,NS(rows=rows),result,events
    def product(self):
        root=Path('model-root');scope=NS(EXE_PIN={'path':'target/model-test.exe'})
        def worker():pass
        from types import FunctionType
        worker=FunctionType(worker.__code__,dict(arguments=lambda:['exact-case','--exact','--test-threads=1']))
        prepared=[NS(linked=NS(original_worker=worker))]
        command=[str(root/scope.EXE_PIN['path']),'exact-case','--exact','--test-threads=1']
        return root,scope,prepared,command
    def test_exact_parent_handoff_arguments_and_distinct_bounded_handles(self):
        event,args=m.arguments(self.argv());self.assertEqual(event,11)
        self.assertEqual(args,['--source-mapped-probe','22','123','a'*64])
        for index,value in ((1,'0'),(1,'9'*21),(3,'case165-current-r010-tests'),(5,'11'),(5,'-1'),(6,'262145'),(7,'bad')):
            argv=self.argv();argv[index]=value
            with self.assertRaises(ValueError):m.arguments(argv)
        with self.assertRaises(ValueError):m.arguments(self.argv()+['--GO'])
    def test_original_go_eof_and_invalid_text_are_never_replaced_or_synthesized(self):
        for raw,expected in (('P149_GO\n',True),('',False),('not-go\n',False)):
            stdin=m.OriginalInput(io.StringIO(raw));self.assertEqual(stdin.readline(),raw)
            self.assertEqual(stdin.go,expected);self.assertEqual(stdin.reads,1)
            with self.assertRaises(ValueError):stdin.readline()
    def test_complete_declared_first_and_closing_reads_precede_original_ready(self):
        worker,q,cap,result,events=self.preparation();prepared=[]
        actual=m.prepare_actual(worker,'root',q,None,None,None,None,cap,prepared,lambda:events.append('checkpoint'))
        self.assertIs(actual,result);self.assertEqual(events,['prepare','finish','checkpoint']);self.assertEqual(prepared,[result])
        with self.assertRaises(ValueError):m.prepare_actual(worker,'root',q,None,None,None,None,cap,prepared,lambda:None)
    def test_missing_closing_or_source_or_original_window_denied(self):
        for fault in ('closing','source','window'):
            worker,q,cap,result,_=self.preparation(closing=fault!='closing')
            if fault=='source':cap.rows={**cap.rows,'missing.py':{}}
            if fault=='window':result.linked.window.WINDOW.SECONDS=15
            prepared=[]
            with self.assertRaises(ValueError):m.prepare_actual(worker,'root',q,None,None,None,None,cap,prepared,lambda:None)
            self.assertEqual(prepared,[None])
    def test_no_product_process_creation_before_original_go_or_second_attempt(self):
        root,scope,prepared,command=self.product();stdin=m.OriginalInput(io.StringIO(''))
        with self.assertRaisesRegex(ValueError,'NO_PRODUCT_CREATION'):m.product_attempt((command[0],command,root,{}),root,scope,prepared,stdin,[])
        stdin=m.OriginalInput(io.StringIO('P149_GO\n'));stdin.readline();attempts=[]
        m.product_attempt((command[0],command,str(root),{}),root,scope,prepared,stdin,attempts)
        self.assertEqual(attempts,[1])
        with self.assertRaisesRegex(ValueError,'NO_PRODUCT_CREATION'):m.product_attempt((command[0],command,root,{}),root,scope,prepared,stdin,attempts)
    def test_only_original_worker_exact_executable_arguments_and_root_are_allowed(self):
        root,scope,prepared,command=self.product();stdin=m.OriginalInput(io.StringIO('P149_GO\n'));stdin.readline()
        for values in (('other.exe',command,root,{}),(command[0],command+['extra'],root,{}),
            (command[0],command,root/'other',{})):
            attempts=[]
            with self.assertRaisesRegex(ValueError,'ONE_EXACT_ORIGINAL_WORKER_PRODUCT_COMMAND'):
                m.product_attempt(values,root,scope,prepared,stdin,attempts)
            self.assertEqual(attempts,[])
    def test_source_pin_digest_covers_every_declared_pin_not_just_count(self):
        first={'a':{'bytes':1,'sha256':'a'}};second={'a':{'bytes':1,'sha256':'b'}}
        self.assertNotEqual(m.pin_digest(first),m.pin_digest(second));self.assertEqual(m.pin_digest(first),m.pin_digest(dict(first)))
    def test_child_calls_original_worker_and_inherited_reader_without_native_or_go_writer(self):
        text=(Path(__file__).resolve().parents[3]/m.SELF).read_text(encoding='utf-8');tree=ast.parse(text)
        calls={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
        self.assertFalse(calls&{'Popen','run_owned','CreateJobObjectW','AssignProcessToJobObject'})
        self.assertIn('api.main()',text);self.assertIn('capabilities[\'reader_type\']',text)
        self.assertIn('set(q.snapshots)==set(cap.rows)',text);self.assertNotIn('EOFOnly(',text)
        self.assertIn('Native_or_product_acceptance_qualified=False',text)
    def test_import_finder_restore_failure_still_closes_sources_without_removing_other_hooks(self):
        actual=object();other=object();meta=[other,actual];closed=[]
        result=m.cleanup_sources(actual,NS(close=lambda:(closed.append(1) or True)),meta)
        self.assertFalse(result['cleanup_confirmed']);self.assertTrue(result['inherited_source_cleanup_confirmed'])
        self.assertEqual(meta,[other,actual]);self.assertEqual(closed,[1])
        meta=[actual,other];result=m.cleanup_sources(actual,NS(close=lambda:True),meta)
        self.assertTrue(result['cleanup_confirmed']);self.assertEqual(meta,[other])
    def test_missing_real_product_argument_dependency_cannot_pass_preparation(self):
        worker,q,cap,result,_=self.preparation();result.linked.original_worker.__globals__.clear();prepared=[]
        with self.assertRaises(ValueError):m.prepare_actual(worker,'root',q,None,None,None,None,cap,prepared,lambda:None)
        self.assertEqual(prepared,[None])
    def test_new_source202_declares_child_without_relabelling_original_eof201(self):
        prior={f'tools/p09/model{i}.py':dict(path=f'tools/p09/model{i}.py',bytes=1,sha256='0'*64) for i in range(201)}
        pin=dict(path=m.SELF,bytes=2,sha256='1'*64);rows={**prior,m.SELF:pin};reads=[];record=object()
        q=NS(pin=lambda name:(reads.append(name) or dict(rows[name])))
        a=NS(read_exact=lambda q,pin:record,exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        control=NS(READY={'model':'prior-provenance'},declarations=lambda value,actual_scope:(self.assertIs(value,record) or dict(prior)))
        value=m.source_declaration(q,a,scope,control)
        self.assertEqual(len(value.required),202);self.assertEqual(len(prior),201);self.assertNotIn(m.SELF,prior)
        self.assertEqual(set(reads),set(rows));self.assertFalse(value.proof['previous_EOF201_reclassified'])
        self.assertFalse(value.proof['actual_child_READY15_or_Native_or_product_qualified'])
    def test_wrong_prior_scope_cannot_silently_replace_existing_source201(self):
        control=NS(READY={},declarations=lambda *args:{m.SELF:{}})
        a=NS(read_exact=lambda *args:None)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_EOF201_DECLARATION_UNCHANGED'):
            m.source_declaration(None,a,scope,control)
    def test_phase_observer_does_not_replace_original_preparation_closing_or_input(self):
        worker,q,cap,result,events=self.preparation();phases=[];prepared=[]
        m.prepare_actual(worker,'root',q,None,None,None,None,cap,prepared,lambda:events.append('checkpoint'),observe=phases.append)
        self.assertEqual(phases,['constructor_started','constructor_returned','closing_complete'])
        self.assertEqual(events,['prepare','finish','checkpoint'])
        reader=m.OriginalInput(io.StringIO(''),phases.append);self.assertEqual(reader.readline(),'')
        self.assertEqual(phases[-1],'original_readline_entered');self.assertFalse(reader.go)
