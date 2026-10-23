"""Bounded diagnostic telemetry, not a product or live sampler qualification."""
import json
import unittest
import native011_source_generation_audit as audit


class ReceiptContracts(unittest.TestCase):
    def test_all_samples_contribute_extrema_and_count(self):
        samples=[dict(system_cpu_percent=i,available_ram_percent=100-i,commit_used_percent=i/2)
                 for i in range(100)]
        samples[0]['system_cpu_percent']=99.5
        result=audit.sample_summary(samples)
        self.assertEqual(result['count'],100)
        self.assertEqual(result['system_CPU_max'],99.5)
        self.assertEqual(result['available_RAM_min'],1)
        self.assertEqual(result['commit_used_max'],49.5)
        self.assertEqual(result['last_eight'],samples[-8:])
        self.assertEqual(len(samples),100)

    def test_empty_samples_remain_unobserved(self):
        self.assertEqual(audit.sample_summary([]),dict(count=0,last_eight=[],
            system_CPU_max=None,available_RAM_min=None,commit_used_max=None))

    def test_partial_observation_is_not_missing_or_current_qualified(self):
        old=dict(path='crates/x/src/a.rs',bytes=1,sha256='a'*64)
        unseen=dict(path='crates/x/src/b.rs',bytes=1,sha256='b'*64)
        changed=dict(old,bytes=2)
        added=dict(path='crates/x/src/c.rs',bytes=1,sha256='c'*64)
        result=audit.compare_observed({old['path']:old,unseen['path']:unseen},[changed,added])
        self.assertEqual([x['path'] for x in result['changed']],[old['path']])
        self.assertEqual(result['added'],[added])
        self.assertEqual(result['unobserved_compiled'],[unseen['path']])
        self.assertFalse(result['current_live_freshness_qualified'])
        self.assertFalse(result['closing_boundary_qualified'])

    def test_duplicate_observation_is_rejected(self):
        pin=dict(path='crates/x/src/a.rs',bytes=1,sha256='a'*64)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OBSERVED_INPUT'):
            audit.compare_observed({},[pin,pin])

    def test_max_inventory_pins_and_bounded_summary_fit_original_receipt_limit(self):
        pins=[dict(path='crates/example/src/'+('x'*80)+str(i)+'.rs',bytes=100,
                   sha256='a'*64) for i in range(800)]
        samples=[dict(system_cpu_percent=50,available_ram_percent=30,commit_used_percent=60,
                      extra_observation='x'*180) for _ in range(1200)]
        row=dict(source_pins=pins,resource_summary=audit.sample_summary(samples))
        self.assertLess(len(json.dumps(row,ensure_ascii=True,indent=2).encode()),262144)


if __name__=='__main__':unittest.main()
