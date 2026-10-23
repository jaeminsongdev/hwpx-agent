"""Small profile contracts; mocks do not qualify worker or Native execution."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import batch_zlib_runtime as module
import batch_worker_launch as worker
import current_stored_runtime_scope as scope


def pin(name):return dict(path=name,bytes=1,sha256='0'*64)


def exact(actual,expected,label):
    if type(actual) is not type(expected) or actual!=expected:raise ValueError(label)


def fields(actual,expected,label):
    for k,v in expected.items():exact(actual.get(k),v,label)


class ProfileContracts(unittest.TestCase):
    def fixture(self):
        source=[pin(n) for n in module.CODE]
        self.proof=dict(state='QUALIFIED_NEW_BINDING_AND_DISK_TRANSPORT_NOT_LIVE_NATIVE_OR_ACCEPTANCE',
            GO_authorized=False,accepted_count_delta=0,installed_in_product=False,current_result=dict(
                state='PASS_NEW_ZLIB_BINDING_AND_FRESH_DISK_TRANSPORT_NOT_NATIVE',descriptor_count=162,
                new_manifest_and_full_table_independently_reconstructed=True,cleanup_confirmed=True,
                fresh_inputs=79,final_fresh_hashes=79,publication_pins=copy.deepcopy(list(module.PACKAGE)),
                binding_proof=dict(historical_roles_preserved=list(range(8))),source_pins=source))
        self.opened=[]
        self.q=NS(pin=lambda n:self.opened.append(n) or pin(n))
        self.a=NS(read_exact=lambda q,p:copy.deepcopy(self.proof),exact=exact,fields=fields)
        self.base=dict(source_pins=[pin('tools/p09/original.py')],fresh_inputs=64,final_fresh_hashes=64)
        self.known={'tools/p09/original.py':pin('tools/p09/original.py')}

    def admit(self):
        return module.admit(Path('D:/explicit-root'),self.q,self.a,scope,self.base,self.known,worker.SELF)

    def test_only_named_source3_and_current_profile_worker_added(self):
        self.fixture();before=copy.deepcopy(self.base);report,known=self.admit()
        self.assertEqual(set(known),set(self.known)|set(module.CODE)|{module.SELF,worker.SELF})
        self.assertEqual(set(self.opened),set(module.CODE)|{module.SELF,worker.SELF})
        self.assertEqual(self.base,before)
        self.assertEqual(report['source_pins'],before['source_pins'])
        self.assertEqual(report['bootstrap_pin'],module.PACKAGE[2])
        self.assertEqual(report['manifest_pin'],module.PACKAGE[0])

    def test_changed_qualified_source_cannot_reuse_preparation(self):
        self.fixture();self.q.pin=lambda n:dict(pin(n),bytes=2)
        with self.assertRaisesRegex(ValueError,'UNCHANGED_QUALIFIED'):self.admit()

    def test_old_package_or_subset_or_other_hash_rejected(self):
        for change in ('old','subset','hash'):
            self.fixture();pins=self.proof['current_result']['publication_pins']
            if change=='old':pins[2]['path']='implementation/p09/evidence/old-bootstrap.v1.json'
            elif change=='subset':pins.pop()
            else:pins[0]['sha256']='1'*64
            with self.assertRaisesRegex(ValueError,'EXACT_DISTINCT_ZLIB_PACKAGE'):self.admit()

    def test_not_qualified_or_go_or_acceptance_cannot_be_inherited(self):
        for change in ({'state':'NOT_RUN'},{'GO_authorized':True},{'accepted_count_delta':1}):
            self.fixture();self.proof.update(change)
            with self.assertRaises(ValueError):self.admit()

    def test_incomplete_closing_or_missing_history_rejected(self):
        for change in ({'final_fresh_hashes':78},{'cleanup_confirmed':False},
                       {'binding_proof':{'historical_roles_preserved':list(range(7))}}):
            self.fixture();self.proof['current_result'].update(change)
            with self.assertRaises(ValueError):self.admit()

    def test_zlib_profile_requires_explicit_no_go_flag(self):
        args=['--ready-handle','123','--task',worker.TASK]
        self.assertEqual(worker.preparation_profile(False,args),(False,args))
        self.assertEqual(worker.preparation_profile(True,['--zlib',*args]),(True,args))
        with self.assertRaisesRegex(ValueError,'REQUIRES_NO_GO_PROBE'):
            worker.preparation_profile(False,['--zlib',*args])

    def test_worker_private_prepare_forwards_exact_selected_package(self):
        import runtime_envelope_namespace_bundle_v1 as loader
        root=Path(module.__file__).resolve().parents[2]
        api=worker.worker_api(root,loader,package=module)
        with patch.object(worker,'prepare',return_value='prepared') as prepare:
            self.assertEqual(api.prepare(root),'prepared')
            prepare.assert_called_once_with(root,package=module)

    def test_diagnostic_zlib_command_keeps_closed_original_handles_and_task(self):
        import sys
        import probe_batch_worker_readiness as probe
        root=Path(module.__file__).resolve().parents[2]
        command=[sys.executable,'-B',str(root/worker.SELF),'--ready-handle','123','--task',worker.TASK]
        self.assertEqual(probe.diagnostic_command(command,root,worker,zlib=True),
            [*command[:3],'--probe-no-go','--zlib',*command[3:]])
        with self.assertRaises(ValueError):probe.diagnostic_command(command,root,worker,zlib='yes')

    def terminal(self):
        linked=NS(preparation_evidence=dict(zlib_profile=True,fresh_inputs=60,final_fresh_hashes=60,
            package_pins=copy.deepcopy(list(module.PACKAGE)),entry_proof=dict(zlib_profile=True,metadata_byte_admissions=4),
            source_pins=[pin(n) for n in module.CODE+(module.SELF,worker.SELF)]))
        row=dict(terminal='WORKER_NOT_AUTHORIZED',task=worker.TASK,descriptor_count=162,
            actual_worker_calls=1,raw_policy_restored=True)
        return linked,row

    def test_terminal_evidence_preserves_all_original_fields(self):
        linked,row=self.terminal();before=copy.deepcopy(row);new=module.terminal_evidence(linked,row)
        self.assertEqual({n:new[n] for n in row},before)
        self.assertEqual(row,before)
        self.assertEqual(new['zlib_preparation']['package_pins'],list(module.PACKAGE))
        self.assertEqual(len(new['zlib_preparation']['source_pins']),5)

    def test_unfinished_or_wrong_package_cannot_be_reported_as_measured(self):
        for change in ({'zlib_profile':False},{'final_fresh_hashes':59},{'package_pins':[]},{'source_pins':[]}):
            linked,row=self.terminal();linked.preparation_evidence.update(change)
            with self.assertRaises(ValueError):module.terminal_evidence(linked,row)

    def test_profile_json_requires_a_real_preparation_result(self):
        import runtime_envelope_namespace_bundle_v1 as loader
        root=Path(module.__file__).resolve().parents[2]
        api=worker.worker_api(root,loader,package=module)
        with self.assertRaisesRegex(ValueError,'ONE_MEASURED_CHILD_PREPARATION'):
            api.main.__globals__['json'].dumps(self.terminal()[1])
        linked,row=self.terminal()
        with patch.object(worker,'prepare',return_value=(linked,'protocol')):api.prepare(root)
        self.assertIn('zlib_preparation',api.main.__globals__['json'].loads(api.main.__globals__['json'].dumps(row)))


if __name__=='__main__':unittest.main()
