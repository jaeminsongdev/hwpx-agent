"""No SQL or product execution. Exact typed samples/pins and unchanged envelope cap."""
import copy,json,unittest
import compact_receipt_json as compact
import search_sql_receipt as codec

def fixture(n=1210):
    return dict(state='MODEL_NOT_SQL_OR_GATE',source_pins=[dict(path=f'crates/hwpx-package/src/module{i}.rs',bytes=i,sha256=f'{i:064x}')for i in range(1062)],
        resource_samples=[dict(time_utc=f'2026-10-22T04:{i//60:02}:{i%60:02}.123456+00:00',system_cpu_percent=i/31,
            available_ram_mib=i/37,total_ram_mib=31860.92,available_ram_percent=i/813,commit_used_percent=i/71,
            own_cpu_percent=0.0,own_working_set_mib=26.8125,own_private_percent=.0841548257532893)for i in range(n)],
        metadata_padding='x'*12000)

class Models(unittest.TestCase):
    def test_1062_pins_and_1210_samples_fit_original_outer_cap_without_loss(self):
        row=fixture();packet=codec.pack(row);published=(json.dumps(packet,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()
        self.assertLessEqual(len(published),262144);self.assertTrue(codec.canonical(codec.unpack(packet))==codec.canonical(row))
    def test_types_float_precision_and_timestamps_are_exact(self):
        row=dict(state='MODEL',source_pins=[],resource_samples=[dict(value=v,time_utc=f'2026-10-22T04:00:00.{i:06}+00:00')for i,v in enumerate([1,1.0,True,None,'1',.12345678901234567]*30)])
        self.assertTrue(codec.canonical(codec.unpack(codec.pack(row)))==codec.canonical(row))
    def test_invalid_dictionary_index_or_extra_fields_are_denied(self):
        row=dict(state='MODEL',source_pins=[],resource_samples=[dict(a='constant'*8)for _ in range(30)])
        encoded=codec.encode(row);column=encoded['resource_sample_table']['series'][0];self.assertEqual(column['kind'],'dictionary')
        bad=copy.deepcopy(encoded);bad['resource_sample_table']['series'][0]['indices'][0]=True
        with self.assertRaises(ValueError):codec.decode(bad)
        bad=copy.deepcopy(encoded);bad['resource_sample_table']['unrecognized']=True
        with self.assertRaises(ValueError):codec.decode(bad)
    def test_empty_samples_are_exact(self):
        row=dict(state='MODEL',source_pins=[],resource_samples=[]);self.assertEqual(codec.unpack(codec.pack(row)),row)
    def test_oversize_metadata_still_rejected_not_externalized(self):
        row=dict(state='MODEL',source_pins=[],resource_samples=[],data='x'*262144)
        with self.assertRaises(ValueError):codec.pack(row)
    def test_nonfinite_samples_and_unbounded_rows_are_denied(self):
        row=dict(state='MODEL',source_pins=[],resource_samples=[dict(a=float('nan'))])
        with self.assertRaises(ValueError):codec.pack(row)
        with self.assertRaises(ValueError):codec.pack(dict(state='MODEL',source_pins=[],resource_samples=[dict(a=1)]*4097))
