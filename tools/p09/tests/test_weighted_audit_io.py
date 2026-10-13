import hashlib
import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import weighted_audit_io as d
from tests.test_audit_evidence_io import Source

class WeightedAuditTests(unittest.TestCase):
    def pacer(self,rate=None):
        clock=[0.0];sleeps=[]
        def sleep(value):sleeps.append(value);clock[0]+=value
        result=d.WeightedPacer(lambda:clock[0],sleep)
        if rate is not None:result.rate=rate
        return result,clock,sleeps
    def live(self,raw=b'{"v":1}\r\n'):
        resources=SimpleNamespace(checkpoint_io=Mock())
        reader=d.WeightedLiveReader(resources,clock=lambda:0)
        source=Source(raw);p=patch.object(reader.reader,'_source',return_value=source)
        p.start();self.addCleanup(p.stop)
        reader.reader.pacer,_,_=self.pacer()
        return reader,resources,source
    def test_default_original_rate_has_identical_token_timing(self):
        new,_,new_sleeps=self.pacer(d.original.READ_BYTES_PER_SECOND)
        old_clock=[0.0];old_sleeps=[]
        def old_sleep(value):old_sleeps.append(value);old_clock[0]+=value
        old=d.original.AuditReadPacer(lambda:old_clock[0],old_sleep)
        for _ in range(7):
            for p in (new,old):p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES)
        self.assertEqual(new_sleeps,old_sleeps)
        self.assertEqual(new.bytes_paced,old.bytes_paced)
        for name,rate in (('x.exe',d.BINARY_RATE),('x.json',d.OTHER_RATE)):
            p,_,sleeps=self.pacer();p.select(name)
            for _ in range(3):p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES)
            self.assertAlmostEqual(sum(sleeps),2*d.original.CHUNK_BYTES/rate)
            self.assertEqual(p.bytes_by_kind[p.kind],3*d.original.CHUNK_BYTES)
    def test_rate_cannot_be_raised_above_original_or_invalid(self):
        for rate in (0,-1,True,1.5,math.inf,d.original.READ_BYTES_PER_SECOND+1):
            p,_,_=self.pacer(rate)
            with self.assertRaises(ValueError):p.reserve(lambda:None)
    def test_idle_credit_one_chunk_and_rate_switch_stays_bounded(self):
        p,clock,sleeps=self.pacer();p.select('x.json')
        p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES)
        clock[0]+=100;p.select('x.exe');p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES)
        self.assertEqual(sleeps,[])
        p.reserve(lambda:None)
        self.assertAlmostEqual(sum(sleeps),d.original.CHUNK_BYTES/d.BINARY_RATE)
    def test_short_read_eof_refunds_and_stalled_clock_are_closed(self):
        p,_,_=self.pacer();p.reserve(lambda:None);p.refund(17)
        self.assertEqual(p.tokens,d.original.CHUNK_BYTES-17)
        p.reserve(lambda:None);p.refund(0)
        self.assertEqual(p.bytes_paced,17)
        p=d.WeightedPacer(lambda:0,lambda _:None);p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES)
        with self.assertRaisesRegex(ValueError,'clock_not_advancing'):p.reserve(lambda:None)
        for value in (-1,True,d.original.CHUNK_BYTES+1):
            with self.assertRaises(ValueError):p.refund(value)
    def test_stop_before_and_after_sleep_and_invalid_clock(self):
        for stop_after in (1,2):
            p,_,sleeps=self.pacer();p.reserve(lambda:None);p.refund(d.original.CHUNK_BYTES);calls=[0]
            def check():
                calls[0]+=1
                if calls[0]>=stop_after:raise ValueError('STOP_FIXTURE')
            with self.assertRaisesRegex(ValueError,'STOP_FIXTURE'):p.reserve(check)
            self.assertEqual(len(sleeps),stop_after-1)
        p,clock,_=self.pacer();clock[0]=-1
        with self.assertRaises(ValueError):p.reserve(lambda:None)
    def test_every_original_repeated_read_and_final_hash_remain(self):
        r,resources,source=self.live()
        first=r.pin('x.exe');self.assertEqual(first,r.pin('x.exe'))
        self.assertEqual(r.json('x.exe'),{'v':1});self.assertEqual(r.text('x.exe'),'{"v":1}\n')
        r.finish();self.assertEqual(source.opens,5)
        self.assertTrue(all(n==d.original.CHUNK_BYTES for n in source.requests))
        self.assertEqual(r.summary()['final_fresh_hashes'],1)
        self.assertEqual(r.summary()['bytes_read'],len(source.raw)*5)
        self.assertEqual(first['sha256'],hashlib.sha256(source.raw).hexdigest())
        self.assertGreater(resources.checkpoint_io.call_count,5)
    def test_repeat_and_final_drift_never_reuse_old_bytes(self):
        for final in (False,True):
            r,_,source=self.live();r.pin('x.exe');source.raw=b'{"v":2}\r\n'
            with self.assertRaisesRegex(ValueError,'input_changed_during_audit'):
                r.finish() if final else r.pin('x.exe')
            self.assertFalse(r.finished)
    def test_original_parse_budget_scope_time_and_resource_guards(self):
        r,resources,_=self.live();r.reader.maximum_parse_bytes=1
        with self.assertRaisesRegex(ValueError,'audit_parse_budget_exceeded'):r.json('x.json')
        r.clock=lambda:601
        with self.assertRaisesRegex(ValueError,'STOP_SQL_IO_SCOPE_TIME'):r.checkpoint()
        r.clock=lambda:0;resources.checkpoint_io.side_effect=ValueError('STOP_HOST')
        with self.assertRaisesRegex(ValueError,'STOP_HOST'):r.pin('x.exe')
    def test_summary_is_actual_weighted_policy_not_stale_imported8MiB(self):
        r,_,source=self.live();r.pin('x.exe');r.pin('x.json');r.finish();row=r.summary()
        self.assertIsNone(row['read_bytes_per_second'])
        self.assertEqual(row['read_rates_by_kind'],{'binary':2621440,'other':4194304})
        self.assertEqual(row['bytes_read_by_kind'],{'binary':len(source.raw)*2,'other':len(source.raw)*2})
        self.assertEqual(row['pacer_bytes_read'],row['bytes_read'])
        self.assertEqual(row['maximum_scope_seconds'],600)
    def test_resource_tail_reuses_only_last8_no_queries(self):
        import threading
        rows=[dict(time_utc=str(i),system_cpu_percent=99,available_ram_mib=100,total_ram_mib=1000,
            available_ram_percent=10,commit_used_percent=40) for i in range(12)]
        resources=SimpleNamespace(lock=threading.Lock(),samples=rows)
        before=list(rows);tail=d.resource_tail(resources)
        self.assertEqual(tail['original_completed_sample_count'],12)
        self.assertEqual(len(tail['samples']),8);self.assertEqual(tail['samples'][0]['time_utc'],'4')
        self.assertFalse(tail['additional_native_queries_started']);self.assertEqual(resources.samples,before)

if __name__=='__main__':unittest.main()
