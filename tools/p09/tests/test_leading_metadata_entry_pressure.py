"""P301: fake CPU windows, 원 callback/guard/read/cleanup 검증. 실제부하 아님."""
import threading
import unittest
from types import SimpleNamespace as NS
import leading_metadata_entry_pressure as p
def fixture(values=(20,)):
    events=[];rows=[dict(system_cpu_percent=values[0])];remaining=list(values[1:])
    owner=NS(samples=rows,lock=threading.Lock())
    def hard():events.append('hard')
    def oldread(n,parse=False):events.append('oldread');return (n,parse)
    def sleep(s):
        events.append('sleep');rows.append(dict(system_cpu_percent=remaining.pop(0) if remaining else rows[-1]['system_cpu_percent']))
    pressure=NS(base=hard,resources=owner);old90=NS(base=pressure)
    pacer=NS(rate=32,opens=0,previous=None,checkpoint=old90)
    reader=NS(read_passes=0,checkpoint=old90,_read=oldread)
    entry=NS(pacer=pacer,active=True);reader._p246_entry_binding=entry
    q=NS(resources=owner,finished=False,reader=reader,entry_binding=entry,pressure=pressure,early_metadata_binding=NS(early=old90))
    return q,owner,sleep,events
class Tests(unittest.TestCase):
    def test_normal(self):
        q,o,s,e=fixture();b=p.Binding(q,o,sleep=s);self.assertEqual(q.reader._read('x',True),('x',True));self.assertEqual(e,['hard','oldread'])
    def test_hot_before_old95(self):
        q,o,s,e=fixture((96,89,88));b=p.Binding(q,o,sleep=s);q.reader._read('x')
        self.assertEqual(e,['hard','sleep','hard','sleep','hard','oldread']);self.assertEqual(b.early.windows,2)
    def test_middle_warning_reset(self):
        q,o,s,e=fixture((96,89,94,89,88));b=p.Binding(q,o,sleep=s);q.reader._read('x');self.assertEqual(b.early.windows,4)
    def test_hard_STOP_first(self):
        q,o,s,e=fixture((100,));q.pressure.base=lambda:(_ for _ in ()).throw(ValueError('STOP_SUSTAINED_SYSTEM_CPU'))
        b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):q.reader._read('x')
        self.assertEqual(e,[]);self.assertEqual(b.failed,1)
    def test_600_stop_retained(self):
        q,o,s,e=fixture();q.pressure.base=lambda:(_ for _ in ()).throw(ValueError('STOP_SQL_IO_SCOPE_TIME'));b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_SQL_IO_SCOPE_TIME'):q.reader._read('x')
    def test_oldread_STOP_retained(self):
        q,o,s,e=fixture();q.reader._read=lambda *a,**kw:(_ for _ in ()).throw(ValueError('ORIGINAL_READ_STOP'));b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_READ_STOP'):q.reader._read('x')
        self.assertEqual(b.failed,1)
    def test_pause_bound(self):
        q,o,s,e=fixture((96,));b=p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):q.reader._read('x')
        self.assertEqual(b.early.windows,8);self.assertNotIn('oldread',e)
    def test_stale_sample(self):
        q,o,s,e=fixture((96,));b=p.Binding(q,o,sleep=lambda s:None)
        with self.assertRaises(ValueError):q.reader._read('x')
        self.assertNotIn('oldread',e)
    def test_close_without_guard(self):
        q,o,s,e=fixture((100,));old=q.reader._read;b=p.Binding(q,o,sleep=s);b.close()
        self.assertIs(q.reader._read,old);self.assertEqual(e,[]);self.assertFalse(b.active)
    def test_callbacks_unchanged(self):
        q,o,s,e=fixture();old=q.reader.checkpoint;pac=q.entry_binding.pacer;b=p.Binding(q,o,sleep=s);q.reader._read('x')
        self.assertIs(q.reader.checkpoint,old);self.assertIs(pac.checkpoint,old);self.assertIs(q.entry_binding.pacer,pac);self.assertEqual(pac.opens,0)
    def test_double_binding(self):
        q,o,s,e=fixture();p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_started_reader(self):
        q,o,s,e=fixture();q.reader.read_passes=1
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_wrong_owner(self):
        q,o,s,e=fixture()
        with self.assertRaises(ValueError):p.Binding(q,NS(),sleep=s)
    def test_wrong_rate(self):
        q,o,s,e=fixture();q.entry_binding.pacer.rate=33
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_finished_reader(self):
        q,o,s,e=fixture();q.finished=True
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_counter_exact(self):
        q,o,s,e=fixture();b=p.Binding(q,o,sleep=s);q.reader._read('x');q.reader._read('y')
        self.assertEqual((b.calls,b.completed,b.failed),(2,2,0));self.assertEqual(e.count('oldread'),2)
    def test_unknown_CPU(self):
        q,o,s,e=fixture((None,));b=p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):q.reader._read('x')
    def test_close_idempotent(self):
        q,o,s,e=fixture();b=p.Binding(q,o,sleep=s);b.close();b.close();self.assertEqual(e,[])
if __name__=='__main__':unittest.main()
