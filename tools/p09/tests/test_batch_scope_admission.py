"""Small in-memory NO-GO declaration contracts, not Native qualification."""
import copy
from types import SimpleNamespace as NS
import unittest
import batch_scope_admission as module
import current_stored_runtime_scope as scope


class Contracts(unittest.TestCase):
    def report(self):
        return dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
            index=165, preparation_report_generation=2, cleanup_confirmed=True,
            product_or_Native_executed=False, GO_authorized=False, accepted_count_delta=0,
            fresh_inputs=64, final_fresh_hashes=64,
            manifest_pin=copy.deepcopy(module.PACKAGE[0]), capsule_pin=copy.deepcopy(module.PACKAGE[1]),
            bootstrap_pin=copy.deepcopy(module.PACKAGE[2]), source_pins=[
                dict(path=f'tools/p09/test_source{i}.py',bytes=1,sha256='0'*64) for i in range(64)])

    def test_closed_report(self):
        self.assertEqual(len(module.validate_report(self.report(),scope)),64)

    def test_boolean_index_not_integer(self):
        report=self.report();report['index']=True
        with self.assertRaisesRegex(ValueError,'EXACT_PUBLISHED_REPORT'):
            module.validate_report(report,scope)

    def test_no_go(self):
        report=self.report();report['GO_authorized']=True
        with self.assertRaisesRegex(ValueError,'EXACT_PUBLISHED_REPORT'):
            module.validate_report(report,scope)

    def test_source_count(self):
        report=self.report();report['source_pins'].pop()
        with self.assertRaisesRegex(ValueError,'CLOSED64'):
            module.validate_report(report,scope)

    def test_final_hash_required(self):
        report=self.report();report['final_fresh_hashes']=63
        with self.assertRaisesRegex(ValueError,'EXACT_PUBLISHED_REPORT'):
            module.validate_report(report,scope)

    def test_original_package_not_relabelled(self):
        report=self.report();report['manifest_pin']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'EXACT_PACKAGE'):
            module.validate_report(report,scope)

    def test_no_self_reference(self):
        report=self.report();report['source_pins'][0]=copy.deepcopy(module.PACKAGE[3])
        with self.assertRaisesRegex(ValueError,'CLOSED64'):
            module.validate_report(report,scope)

    def test_full_cost_terms(self):
        current={'a':1,'b':2}
        predicted=400-4/20+20+3+167/20+11+5+2.05
        fake_scope=NS(cost=lambda r,rate:dict(predicted_combined_seconds=400))
        fake_views=NS(model=lambda r,n:dict(predicted_runtime_combined_seconds=predicted))
        row=module.early_budget(current,fake_scope,fake_views)
        self.assertAlmostEqual(row['with_shared_decoder_final_sample_and_preparation_seconds'],predicted+20.5)
        self.assertEqual(row['shared_decoder_allowance_seconds'],5)
        self.assertTrue(row['conservative_fits'])
        self.assertFalse(row['product_credit_taken'])

    def test_oversized_model_does_not_call_expensive_next_stage(self):
        fake_scope=NS(cost=lambda r,rate:dict(predicted_combined_seconds=650))
        def denied(*args):raise AssertionError('must stop before next stage')
        row=module.early_budget({'a':1},fake_scope,NS(model=denied))
        self.assertFalse(row['conservative_fits'])
        self.assertFalse(row['actual_tightened_engine_budget_qualified'])

    def test_no_discounted_model(self):
        fake_scope=NS(cost=lambda r,rate:dict(predicted_combined_seconds=400))
        fake_views=NS(model=lambda *args:dict(predicted_runtime_combined_seconds=1))
        with self.assertRaisesRegex(ValueError,'ALL_TERMS_NOT_DISCOUNTED'):
            module.early_budget({'a':1},fake_scope,fake_views)

    def test_exact_program_names(self):
        with self.assertRaisesRegex(ValueError,'EXPLICIT_PROGRAMS'):
            module.extend_plan(None,(),{},scope.pins(list(module.PACKAGE)),NS(scope=scope),lambda:None)

    def test_package_table_immutable(self):
        programs={n:dict(path=n,bytes=1,sha256='0'*64) for n in module.PROGRAMS}
        with self.assertRaisesRegex(ValueError,'IMMUTABLE_FOUR'):
            module.extend_plan(None,(),programs,{},NS(scope=scope),lambda:None)

    def test_own_preparation_receipt_explicitly_current_not_missing_from_self_free_sources(self):
        def pin(name):return dict(path=name,bytes=1,sha256='0'*64)
        hot=pin('tools/p09/reference.py');cold=pin('implementation/p09/evidence/p09-361-case114-current-runtime-run001.v1.json')
        programs={n:pin(n) for n in module.PROGRAMS}
        legacy=pin('implementation/p09/evidence/config.json')
        fake=NS(scope=scope, LEGACY_CONFIG=legacy,
            partition=NS(candidate=lambda *args:dict(per_case_candidate=[hot],batch_preservation_candidate=[cold])),
            Batch=lambda whole,current,history,**kwargs:NS(whole=whole,current=current,history=history))
        declared=NS(physical={hot['path']:hot,cold['path']:cold},logical={hot['path']:hot,cold['path']:cold})
        planned=module.extend_plan(declared,(),programs,scope.pins(list(module.PACKAGE)),fake,lambda:None)
        self.assertEqual(planned.current[module.PREPARATION_PROOF['path']],module.PREPARATION_PROOF)
        self.assertEqual(planned.history,{cold['path']:cold})
        self.assertNotIn(cold['path'],planned.current)

    def test_preparation_receipt_must_not_be_reclassified_from_history(self):
        programs={n:dict(path=n,bytes=1,sha256='0'*64) for n in module.PROGRAMS}
        hot=dict(path='tools/p09/reference.py',bytes=1,sha256='0'*64)
        fake=NS(scope=scope,LEGACY_CONFIG=dict(path='config.json',bytes=1,sha256='0'*64),
            partition=NS(candidate=lambda *args:dict(per_case_candidate=[hot],
                batch_preservation_candidate=[module.PREPARATION_PROOF])))
        with self.assertRaisesRegex(ValueError,'NO_HISTORICAL_RECEIPT_RECLASSIFIED'):
            module.extend_plan(NS(physical={}),(),programs,scope.pins(list(module.PACKAGE)),fake,lambda:None)


class EpochContracts(unittest.TestCase):
    class Guard:
        def __init__(self):self.cleanup=False;self.samples=[];self.fail=False;self.calls=0;self.closed=0
        def acquire(self):pass
        def check(self,**kwargs):
            self.calls+=1
            if self.fail:raise ValueError('STOP_TEST_CPU')
        def close(self):self.closed+=1;self.cleanup=True

    def policy(self):
        return NS(phase='READY',active=None,cases=[],metadata_reader_active=False,parent_connection=None)

    def epochs(self):return module.ReadOnlyEpochs(self.Guard,clock=lambda:0,identity=lambda:1)

    def test_three_serial_epochs_close_original_guards_once(self):
        epochs=self.epochs();epochs.advance('construction');first=epochs.guard
        epochs.advance('opening_and_metadata',self.policy());second=epochs.guard
        epochs.advance('closing',self.policy());third=epochs.guard;epochs.close()
        self.assertEqual([r['stage'] for r in epochs.records],list(epochs.STAGES))
        self.assertEqual([g.closed for g in (first,second,third)],[1,1,1])
        self.assertTrue(all(r['cleanup_confirmed'] for r in epochs.records))

    def test_resource_stop_never_rotates_or_retries(self):
        epochs=self.epochs();epochs.advance('construction');first=epochs.guard;first.fail=True
        with self.assertRaisesRegex(ValueError,'STOP_TEST_CPU'):epochs.advance('opening_and_metadata',self.policy())
        with self.assertRaisesRegex(ValueError,'NO_FAILED_EPOCH_RETRY'):epochs.advance('opening_and_metadata',self.policy())
        self.assertIs(epochs.guard,first);epochs.close();self.assertEqual(len(epochs.records),1)

    def test_no_repeated_or_skipped_stage(self):
        epochs=self.epochs();epochs.advance('construction')
        for name in ('construction','closing'):
            with self.assertRaisesRegex(ValueError,'THREE_EXACT'):epochs.advance(name,self.policy())
        epochs.close()

    def test_case_or_frame_or_metadata_cannot_reset_deadline(self):
        for field,value in (('active',object()),('cases',[1]),('metadata_reader_active',True),
                ('parent_connection',object()),('phase','CASE_ACTIVE')):
            epochs=self.epochs();epochs.advance('construction');policy=self.policy();setattr(policy,field,value)
            with self.assertRaisesRegex(ValueError,'NO_NATIVE_FRAME'):epochs.advance('opening_and_metadata',policy)
            epochs.close()

    def test_owner_change_denied_before_guard(self):
        epochs=self.epochs();epochs.advance('construction');epochs.identity=lambda:2
        with self.assertRaisesRegex(ValueError,'LIVE_SERIAL'):epochs.check()
        with self.assertRaisesRegex(ValueError,'NO_FAILED'):epochs.advance('opening_and_metadata',self.policy())
        epochs.close()

    def test_close_idempotent_and_no_fourth_stage(self):
        epochs=self.epochs()
        for stage in epochs.STAGES:epochs.advance(stage,self.policy())
        epochs.close();epochs.close();self.assertEqual(len(epochs.records),3)
        with self.assertRaisesRegex(ValueError,'THREE_EXACT'):epochs.advance('construction',self.policy())

    def test_cleanup_failure_blocks_successor(self):
        class Bad(self.Guard):
            def close(self):self.cleanup=False
        epochs=module.ReadOnlyEpochs(Bad,clock=lambda:0,identity=lambda:1)
        epochs.advance('construction')
        with self.assertRaisesRegex(ValueError,'EXACT_EPOCH_CLEANUP'):epochs.advance('opening_and_metadata',self.policy())
        self.assertTrue(epochs.broken);self.assertIsNone(epochs.guard)


class RouterContracts(unittest.TestCase):
    def test_original_run_and_both_live_checkpoints_retained(self):
        calls=[]
        def check():calls.append('original')
        budget=NS(checkpoint=check)
        def run(action):
            budget.checkpoint();return action(budget.checkpoint)
        budget.run=run
        def decode(name,pin,raw,checkpoint):checkpoint();return raw
        projection=NS(semantic_pins={},physical_pins={},next_case=165,decode_fresh=decode)
        router=module.MetadataRouter(projection,budget)
        self.assertEqual(router.decode_fresh('a',{},b'bytes',lambda:calls.append('live')),b'bytes')
        self.assertEqual(calls,['original','live','original','live'])
        self.assertIs(budget.checkpoint,check);self.assertEqual(router.counts,{'a':1})

    def test_decoder_failure_restores_checkpoint_and_is_not_completion(self):
        def check():pass
        budget=NS(checkpoint=check)
        def run(action):raise ValueError('STOP_SHARED_METADATA_FRAME_DECODER5')
        budget.run=run
        router=module.MetadataRouter(NS(semantic_pins={},physical_pins={},next_case=165),budget)
        with self.assertRaisesRegex(ValueError,'STOP_SHARED'):router.decode_fresh('a',{},b'x',check)
        self.assertIs(budget.checkpoint,check);self.assertEqual(router.counts,{})


class ParentSourceContracts(unittest.TestCase):
    def data(self):
        def pin(name):return dict(path=name,bytes=1,sha256='0'*64)
        step=module.PREFIX+'step-config001.v1.json'
        current={n:pin(n) for n in module.PROGRAMS+(step,)}
        current.update(scope.pins(list(module.PACKAGE)))
        legacy=pin('implementation/p09/evidence/config.json');current[legacy['path']]=legacy
        dependency=pin('tools/p09/dependency.py');current[dependency['path']]=dependency
        return NS(package_sources={dependency['path']:dependency},planned=NS(current=current),
            declared=NS(to_physical=lambda rows:scope.pins(rows))),NS(scope=scope,LEGACY_CONFIG=legacy)

    def test_exact_step_is_supplied_before_whole_audit(self):
        data,batch=self.data();row=module.parent_sources(data,batch)
        step=module.PREFIX+'step-config001.v1.json'
        self.assertEqual(row[step],data.planned.current[step])

    def test_missing_step_fails_before_whole_audit(self):
        data,batch=self.data();del data.planned.current[module.PREFIX+'step-config001.v1.json']
        with self.assertRaisesRegex(ValueError,'STEP_CONFIG_DECLARED_BEFORE_WHOLE_IO'):
            module.parent_sources(data,batch)

    def test_unknown_metadata_dependency_is_not_added_silently(self):
        data,batch=self.data();data.package_sources['tools/p09/dependency.py']['bytes']=2
        data.planned.current['tools/p09/dependency.py']=dict(path='tools/p09/dependency.py',bytes=1,sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'EVERY_PARENT_SOURCE'):
            module.parent_sources(data,batch)
