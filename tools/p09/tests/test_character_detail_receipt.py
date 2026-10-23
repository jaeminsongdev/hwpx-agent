import copy,unittest
import character_detail_receipt as subject

class Tests(unittest.TestCase):
    def row(self,n=3):
        return dict(state='MODEL_NOT_ACCEPTANCE',before=1,source_pins=[dict(path=f'crates/pkg/src/long_directory/n{i}.rs',bytes=i,sha256='1'*64)for i in range(n)],
            after=2,resource_samples=[dict(cpu=1.25,ram=51.2),dict(cpu=0.0,ram=51.1)])
    def test_roundtrip_preserves_all_values_and_field_order(self):
        row=self.row();saved=copy.deepcopy(row);encoded=subject.encode(row)
        self.assertEqual(subject.compact.raw(subject.decode(encoded)),subject.compact.raw(row));self.assertEqual(row,saved)
        self.assertEqual(subject.unpack(subject.pack(row)),row)
    def test_root_paths_empty_pins_and_optional_empty_samples_roundtrip(self):
        for n in(0,1):
            row=self.row(n);row['resource_samples']=[]
            if n:row['source_pins'][0]['path']='Cargo.toml'
            self.assertEqual(subject.unpack(subject.pack(row)),row)
    def test_realistic_900_pins_are_smaller_without_compression_or_larger_cap(self):
        row=self.row(900);encoded=subject.encode(row)
        self.assertLess(len(subject.compact.raw(encoded)),len(subject.compact.raw(row))*.8)
        self.assertEqual(subject.unpack(subject.pack(row)),row);self.assertEqual(subject.compact.MAXIMUM,262144)
    def test_unknown_pin_fields_are_not_silently_dropped(self):
        row=self.row();row['source_pins'][0]['extra']='private'
        with self.assertRaises(ValueError):subject.encode(row)
    def test_duplicate_directories_invalid_rows_and_boolean_index_reject(self):
        encoded=subject.encode(self.row())
        for mutation in('duplicate','index','shape','slash'):
            bad=copy.deepcopy(encoded);table=bad[subject.KEY]
            if mutation=='duplicate':table['directories'].append(table['directories'][0])
            elif mutation=='index':table['rows'][0][0]=True
            elif mutation=='shape':table['rows'][0].append('bad')
            else:table['rows'][0][1]='../bad.rs'
            with self.assertRaises(ValueError):subject.decode(bad)
    def test_original_cap_still_rejects_oversized_metadata(self):
        row=self.row();row['too_large']='x'*300000
        with self.assertRaises(ValueError):subject.pack(row)

if __name__=='__main__':unittest.main()
