import ctypes
import math
import unittest
from ctypes import wintypes as w
import host_cpu_observer as s


def array(rows):
    size=len(rows)*ctypes.sizeof(s.Item)+sum((len(name)+1)*ctypes.sizeof(ctypes.c_wchar) for name,_,_ in rows)
    buffer=ctypes.create_string_buffer(size);items=ctypes.cast(buffer,ctypes.POINTER(s.Item))
    ptr=ctypes.addressof(buffer)+len(rows)*ctypes.sizeof(s.Item)
    for index,(name,value,status) in enumerate(rows):
        text=ctypes.create_unicode_buffer(name);ctypes.memmove(ptr,text,ctypes.sizeof(text))
        items[index].name=ptr;items[index].value.CStatus=status;items[index].value.doubleValue=value
        ptr+=ctypes.sizeof(text)
    return buffer,size,len(rows)


class Fake:
    def __init__(self):self.closed=0;self.collects=0;self.status=0;self.counter_status=0;self.array_status=0
    def PdhOpenQueryW(self,a,b,out):out._obj.value=9;return self.status
    def PdhAddEnglishCounterW(self,q,path,user,out):out._obj.value=s.PATHS.index(path)+1;return self.counter_status
    def PdhCollectQueryData(self,q):self.collects+=1;return self.status
    def PdhCloseQuery(self,q):self.closed+=1;return self.status
    def PdhGetFormattedCounterArrayW(self,handle,fmt,size,count,buffer):
        if buffer is None:
            fixture,n,c=array([('python',100.0 if handle.value==1 else 50.0,0)])
            size._obj.value=n;count._obj.value=c;return s.MORE_DATA
        fixture,n,c=array([('python',100.0 if handle.value==1 else 50.0,0)])
        ctypes.memmove(buffer,fixture,n)
        # Translate fixture pointer to destination buffer.
        ctypes.cast(buffer,ctypes.POINTER(s.Item))[0].name=ctypes.addressof(buffer)+ctypes.sizeof(s.Item)
        return self.array_status


class HostCPUObserverTests(unittest.TestCase):
    def test_native_layout(self):self.assertEqual(ctypes.sizeof(s.Value),16);self.assertEqual(ctypes.sizeof(s.Item),24)
    def test_unsigned_status(self):self.assertEqual(s.status(-2147481646),s.MORE_DATA)
    def test_buffer_complete(self):self.assertEqual(s.decode(*array([('One',12.0,0),('two',2.0,1)])),{'one':12.0,'two':2.0})
    def test_invalid_counter_unknown_not_zero(self):self.assertEqual(s.decode(*array([('x',math.nan,0xc0000bc6)])),{'x':None})
    def test_pointer_outside_rejected_before_read(self):
        b,n,c=array([('x',1,0)]);ctypes.cast(b,ctypes.POINTER(s.Item))[0].name=1
        with self.assertRaisesRegex(ValueError,'NAME_POINTER'):s.decode(b,n,c)
    def test_pointer_into_items_rejected(self):
        b,n,c=array([('x',1,0)]);ctypes.cast(b,ctypes.POINTER(s.Item))[0].name=ctypes.addressof(b)
        with self.assertRaisesRegex(ValueError,'NAME_POINTER'):s.decode(b,n,c)
    def test_bound_and_count(self):
        b,n,c=array([('x',1,0)])
        for size,count in ((s.MAX_BUFFER+1,c),(n,2049),(n,2),(0,0)):
            with self.assertRaises(ValueError):s.decode(b,size,count)
    def test_name_termination(self):
        with self.assertRaisesRegex(ValueError,'NAME_TERMINATION'):s.decode(*array([('x'*s.MAX_NAME,1,0)]))
    def test_duplicate_and_nonfinite(self):
        for rows in ([('x',1,0),('X',2,0)],[('x',math.inf,0)],[('x',-1,0)]):
            with self.assertRaises(ValueError):s.decode(*array(rows))
    def test_multi_core_not_clamped(self):
        row,_=s.select({'x':800.0},{'x':50.0},{'x':50},16)
        self.assertEqual(row['top'][0]['machine_cpu_percent'],50);self.assertEqual(row['top'][0]['processor_time_raw_percent'],800)
        self.assertEqual(s.FORMAT,0x8200)
    def test_stable_pid_required(self):
        row,_=s.select({'x':800.0},{'x':50.0},{'x':49},16)
        self.assertEqual(row['top'],[]);self.assertEqual(row['unstable_instances'],1)
    def test_unknown_does_not_become_zero(self):
        row,_=s.select({'x':None,'y':3.0},{'x':50.0,'y':None},{'x':50},16)
        self.assertEqual(row['unavailable_instances'],2);self.assertEqual(row['top'],[])
    def test_pid_exact_integer(self):
        for value in (0.,1.5,4294967296.,math.inf):
            with self.assertRaises(ValueError):s.pid_map({'x':value})
    def test_roles_redacted_and_owned(self):
        row,_=s.select({'private-token-string':16.0},{'private-token-string':50.0},{'private-token-string':50},16,(50,))
        self.assertEqual(row['top'][0]['role'],'other');self.assertTrue(row['top'][0]['owned'])
        self.assertNotIn('private-token-string',str(row));self.assertFalse(row['causal_attribution'])
        self.assertEqual(s.role('MsMpEng#1'),'defender');self.assertEqual(s.role('form_stored_provider-p152-r01'),'stored_test')
    def test_process_every_item_before_top_bound(self):
        cpu={f'p{i}':float(i) for i in range(10)};pids={k:float(20+i) for i,k in enumerate(cpu)}
        row,_=s.select(cpu,pids,{k:int(v) for k,v in pids.items()},16)
        self.assertEqual(row['stable_candidate_count'],10);self.assertEqual(len(row['top']),8)
        cpu['last_bad']=-1;pids['last_bad']=50.0
        with self.assertRaises(ValueError):s.select(cpu,pids,{k:int(v) for k,v in pids.items()},16)
    def test_ignore_idle_total(self):
        row,_=s.select({'idle':1200.,'_total':1500.},{'idle':0.,'_total':0.},{},16)
        self.assertEqual(row['top'],[])
    def test_warm_then_sample_close_once(self):
        fake=Fake();o=s.Observer(16,fake);self.assertIsNone(o.collect())
        self.assertEqual(o.collect((50,))['top'][0]['machine_cpu_percent'],6.25)
        o.close();o.close();self.assertEqual(fake.closed,1)
        with self.assertRaisesRegex(ValueError,'QUERY_CLOSED'):o.collect()
    def test_failed_init_closes_handle(self):
        fake=Fake();fake.counter_status=1
        with self.assertRaisesRegex(ValueError,'COUNTER_ADD'):s.Observer(16,fake)
        self.assertEqual(fake.closed,1)
    def test_size_growth_no_unbounded_retry(self):
        fake=Fake();o=s.Observer(16,fake);o.collect();fake.array_status=s.MORE_DATA
        with self.assertRaisesRegex(ValueError,'ARRAY_READ_STATUS'):o.collect()
        o.close()
    def test_bad_processors(self):
        for p in (True,0,65,'16'):
            with self.assertRaisesRegex(ValueError,'PROCESSORS'):s.Observer(p,Fake())


if __name__=='__main__':unittest.main()
