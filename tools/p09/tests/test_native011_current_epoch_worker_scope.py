"""Private dependency routing models; no worker, product or timing body runs."""
from types import FunctionType, ModuleType, SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_current_epoch_worker_scope as route


def pin(name,value='a'):return dict(path=name,bytes=1,sha256=value*64)


class WorkerScopeContracts(unittest.TestCase):
    def fixture(self):
        old=pin('old.exe');new=pin('new.exe','b');original_scope=NS(EXE_PIN=old,CASE112='case165',OTHER=object())
        env=dict(scope=original_scope)
        exec('def arguments(): return [scope.CASE112,"--exact"]\ndef worker(task): raise AssertionError("must not run")\ndef engine(): raise AssertionError("must not run")',env)
        linked=NS(original_worker=env['worker'],engine=NS(worker=env['worker'],run_owned=env['engine']),
            state=NS(original=env['worker'],attempts=0,calls=0,completed=False))
        return linked,old,new,original_scope,env

    def test_one_private_field_changes_without_worker_call_or_argument_change(self):
        linked,old,new,original,env=self.fixture();worker=linked.original_worker;code=worker.__code__
        proof=route.route(linked,old,new,scope,modules=[])
        self.assertIs(linked.original_worker,worker);self.assertIs(worker.__code__,code)
        self.assertEqual(env['scope'].EXE_PIN,new);self.assertEqual(original.EXE_PIN,old)
        self.assertEqual(env['arguments'](),['case165','--exact'])
        self.assertFalse(proof['worker_executed']);self.assertFalse(proof['default_modules_mutated'])

    def test_default_module_globals_are_never_mutated(self):
        linked,old,new,original,env=self.fixture();module=ModuleType('default_module')
        module.__dict__.update(env)
        worker=FunctionType(linked.original_worker.__code__,module.__dict__)
        engine=FunctionType(linked.engine.run_owned.__code__,module.__dict__)
        linked.original_worker=linked.engine.worker=linked.state.original=worker;linked.engine.run_owned=engine
        with self.assertRaisesRegex(ValueError,'PRIVATE_NAMESPACE_NOT_DEFAULT_MODULE_GLOBALS'):
            route.route(linked,old,new,scope,modules=[module])
        self.assertIs(module.scope,original)

    def test_after_attempt_or_unknown_previous_candidate_or_repeat_is_denied(self):
        linked,old,new,original,env=self.fixture();linked.state.attempts=1
        with self.assertRaisesRegex(ValueError,'BEFORE_ANY_WORKER_ATTEMPT_ONLY'):route.route(linked,old,new,scope,modules=[])
        linked,old,new,original,env=self.fixture()
        with self.assertRaisesRegex(ValueError,'EXACT_PREVIOUS_CANDIDATE_NO_REPEATED_ROUTING'):
            route.route(linked,pin('other.exe'),new,scope,modules=[])
        route.route(linked,old,new,scope,modules=[])
        with self.assertRaisesRegex(ValueError,'EXACT_PREVIOUS_CANDIDATE_NO_REPEATED_ROUTING'):
            route.route(linked,old,new,scope,modules=[])

    def test_changed_original_worker_identity_is_rejected(self):
        linked,old,new,original,env=self.fixture();linked.engine.worker=lambda task:None
        with self.assertRaisesRegex(ValueError,'SAME_ORIGINAL_WORKER_AND_ENGINE'):
            route.route(linked,old,new,scope,modules=[])


if __name__=='__main__':unittest.main()
