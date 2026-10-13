import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import owned_source_read_pressure as d
import build_xml_capacity_product_r2 as build

class OwnedSourceReadPressureTests(unittest.TestCase):
    def test_rates_only_reduce_original_ceiling(self):
        p=d.OwnedPacer();p.select('fixture.exe');self.assertEqual(p.rate,1048576)
        p.select('fixture.rs');self.assertEqual(p.rate,2097152)
        self.assertIs(d.WeightedLiveReader,d.prior.WeightedLiveReader)
        self.assertLess(d.BINARY_RATE,d.prior.BINARY_RATE);self.assertLess(d.OTHER_RATE,d.prior.OTHER_RATE)
    def test_original_one_chunk_burst_and_sleep_checkpoints(self):
        now=[0.0];checks=[]
        p=d.OwnedPacer(clock=lambda:now[0],sleeper=lambda delay:now.__setitem__(0,now[0]+delay));p.select('x.exe')
        p.reserve(lambda:checks.append(now[0]));p.refund(65536)
        p.reserve(lambda:checks.append(now[0]));p.refund(65536)
        self.assertAlmostEqual(now[0],0.0625);self.assertEqual(p.bytes_by_kind,{'binary':131072,'other':0})
        self.assertGreaterEqual(len(checks),2);now[0]+=100;p.reserve(lambda:None);p.refund(65536)
        self.assertLessEqual(p.tokens,65536)
    def test_whole_repeat_and_finish_exact(self):
        raw=b'x'*1000;opens=[];path=SimpleNamespace()
        path.open=lambda mode:opens.append(mode) or io.BytesIO(raw)
        reader=d.WeightedReader('fixture',lambda:None)
        with patch.object(reader,'_source',return_value=path):
            first=reader.fresh_pin('x.exe');self.assertEqual(reader.fresh_pin('x.exe'),first);reader.finish()
        self.assertEqual(opens,['rb']*3);self.assertEqual(reader.bytes_read,3000)
        self.assertEqual(reader.pacer.bytes_paced,3000);self.assertEqual(reader.final_fresh_hashes,1)
    def test_final_drift_and_stop_not_bypassed(self):
        raw=[b'old'];path=SimpleNamespace(open=lambda mode:io.BytesIO(raw[0]));reader=d.WeightedReader('fixture',lambda:None)
        with patch.object(reader,'_source',return_value=path):
            reader.fresh_pin('x.exe');raw[0]=b'new'
            with self.assertRaises(ValueError):reader.finish()
        p=d.OwnedPacer();p.select('x.exe');p.tokens=0
        with self.assertRaisesRegex(ValueError,'fixture_stop'):
            p.reserve(lambda:(_ for _ in ()).throw(ValueError('fixture_stop')))
    def test_owned_adapter_uses_original_run_and_new_rate_only(self):
        prior=build.prior;before=prior.weighted;seen=[]
        def run(destination,*binding):seen.append(prior.c.AuditEvidenceReader('fixture',lambda:None));return 2
        with patch.object(prior,'weighted',d),patch.object(prior.p,'run_owned',run):
            self.assertEqual(prior.run_owned('fixture',({},[],[])),2)
        self.assertIs(prior.weighted,before);seen[0].pacer.select('x.exe');self.assertEqual(seen[0].pacer.rate,1048576)
        self.assertEqual(prior.recipe()['compile_maximum_seconds'],600);self.assertEqual(prior.recipe()['full249_maximum_seconds'],1200)
    def test_original_worker_task_not_changed(self):
        with patch.object(build.prior,'worker',return_value=2) as checked:
            self.assertEqual(build.worker('p152-current-stored-build-r07'),2)
        checked.assert_called_once_with('p152-current-stored-build-r07')

if __name__=='__main__':unittest.main()
