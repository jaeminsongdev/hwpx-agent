import hashlib
import json
import unittest
import validated_compiler_progress_r2 as d

class ReservedCompilerProgressTests(unittest.TestCase):
    def raw(self,count=100):
        dep=dict(reason='compiler-artifact',target=dict(name='private_unreported'),fresh=True)
        rows=[dep]*count
        rows.extend(dict(reason='compiler-artifact',target=dict(name=name),fresh=False)
            for name in ('domain_ir','hwpx_package','hwpx_agent_cli'))
        rows.append(dict(reason='compiler-artifact',target=dict(name='form_stored_provider',kind=['test']),
            profile=dict(d.d.b.EXPECTED_PROFILE),executable='fixture-not-executed',fresh=False))
        rows.append(dict(reason='build-finished',success=True))
        return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()

    def stream(self,raw):
        events=[];stream=d.CargoStream(emit=events.append)
        for i in range(0,len(raw),4096):stream.feed(raw[i:i+4096])
        return stream,events

    def test_late_critical_groups_reserve_four_slots_after_many_dependencies(self):
        stream,events=self.stream(self.raw());stream.finish(0)
        self.assertEqual([r['group'] for r in events[-5:-1]],['domain-ir','hwpx-package','product-cli','product-libtest'])
        self.assertEqual((len(events),events[-1]['omitted_artifacts']),(21,84))

    def test_all_original_records_and_raw_hash_kept(self):
        raw=self.raw();stream,events=self.stream(raw);proof=json.loads(stream.finish(0).splitlines()[-1])
        self.assertEqual(proof['raw_stdout_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual((proof['messages'],proof['raw_stdout_bytes']),(105,len(raw)))

    def test_original_strict_profile_warning_and_duplicate_keys_still_reject(self):
        for raw in (self.raw().replace(b'"test": true',b'"test": false'),
            b'{"reason":"compiler-message","message":{"level":"warning"}}\n',
            b'{"reason":"build-finished","reason":"compiler-artifact"}\n'):
            with self.assertRaises(ValueError):self.stream(raw)

    def test_aliases_cannot_duplicate_critical_group_budget(self):
        raw=self.raw().replace(b'"name": "hwpx_package"',b'"name": "domain-ir"')
        stream,events=self.stream(raw);stream.finish(0)
        self.assertEqual(sum(r['group']=='domain-ir' for r in events),1)
        self.assertEqual(len(stream.critical_saved),3)

    def test_stop_diagnostic_never_becomes_complete_or_exact_phase(self):
        stream,events=self.stream(self.raw())
        observation=d.prior.observe(''.join(d.prior.encode_event(r).decode() for r in events))
        self.assertFalse(observation['closing_observed']);self.assertFalse(observation['exact_compiler_or_linker_phase_verified'])
        self.assertIsNone(observation['unobserved_artifacts'])

    def test_exact_original_stderr_guard_and_frame_limits(self):
        stream,events=self.stream(self.raw())
        with self.assertRaises(ValueError):stream.finish(32769)
        self.assertFalse(any(r['kind']=='closed' for r in events))
        self.assertLessEqual(max(len(d.prior.encode_event(r)) for r in events),256)
        self.assertNotIn('private_unreported',''.join(d.prior.encode_event(r).decode() for r in events))

if __name__=='__main__':unittest.main()
