"""New closed version projection models; no Byte/Frame/product work."""
from types import SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_current_epoch_plan as plan


def pin(name,value='a'):return dict(path=name,bytes=1,sha256=value*64)


class VersionContracts(unittest.TestCase):
    def fixture(self):
        rows=[]
        for i in range(5):
            name=f'crates/x/f{i}.rs';old=pin(name);new=pin(name,'b');archive=dict(old,path='archive/'+name)
            rows.append(dict(original_pin=old,current_pin=new,proposed_archive_pin=archive))
        raw=pin('logical/data.json');carrier=pin('physical/data.json','c')
        def normalize(values):
            result={}
            for name,p in scope.pins(values).items():
                if name==carrier['path']:
                    if p!=carrier:raise ValueError('ORIGINAL_BAD_CARRIER')
                    name=raw['path'];p=raw
                if name==raw['path'] and p!=raw:raise ValueError('ORIGINAL_BAD_SEMANTIC')
                result[name]=dict(p)
            return result
        def physical(values):
            return {carrier['path'] if n==raw['path'] else n:dict(carrier if n==raw['path'] else p)
                    for n,p in normalize(values).items()}
        declared=NS(normalize=normalize,to_physical=physical)
        return plan.Versions(declared,rows,scope,{r['original_pin']['path'] for r in rows}),rows,raw,carrier

    def test_old_source_projects_to_exact_archive_new_source_stays_current(self):
        versions,rows,raw,carrier=self.fixture()
        for row in rows:
            old=row['original_pin'];new=row['current_pin'];archive=row['proposed_archive_pin']
            self.assertEqual(versions.physical([old]),{archive['path']:archive})
            self.assertEqual(versions.physical([new]),{new['path']:new})
            self.assertEqual(versions.physical([archive]),{archive['path']:archive})

    def test_original_wire_alias_rules_and_failures_stay_in_force(self):
        versions,rows,raw,carrier=self.fixture()
        self.assertEqual(versions.physical([raw]),{carrier['path']:carrier})
        self.assertEqual(versions.physical([carrier]),{carrier['path']:carrier})
        for bad in (dict(raw,bytes=2),dict(carrier,bytes=2)):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_BAD_'):versions.physical([bad])

    def test_third_source_version_and_tampered_archive_rejected(self):
        versions,rows,raw,carrier=self.fixture();row=rows[0]
        with self.assertRaisesRegex(ValueError,'NO_THIRD_SOURCE_VERSION_OR_HASH_REBASE'):
            versions.normalize([dict(row['current_pin'],sha256='c'*64)])
        with self.assertRaisesRegex(ValueError,'EXACT_ARCHIVE_SOURCE_VERSION'):
            versions.normalize([dict(row['proposed_archive_pin'],bytes=2)])

    def test_old_and_new_can_coexist_without_silent_pin_overlay(self):
        versions,rows,raw,carrier=self.fixture();row=rows[0]
        archived=versions.normalize([row['original_pin']])
        current=versions.normalize([row['current_pin']])
        joined=scope.extend(archived,current)
        self.assertEqual(len(joined),2)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_PIN'):
            versions.normalize([row['original_pin'],row['current_pin']])


if __name__=='__main__':unittest.main()
