import hashlib
import json
import unittest
import validated_compiler_progress as d

class CompilerProgressTests(unittest.TestCase):
    def fixture(self,count=0):
        dep=dict(reason='compiler-artifact',target=dict(name='private_unreported_name'),fresh=True,padding='z'*500)
        target=dict(reason='compiler-artifact',target=dict(name='form_stored_provider',kind=['test']),
            profile=dict(d.d.b.EXPECTED_PROFILE),executable='fixture-not-executed',fresh=False)
        return ('\n'.join(json.dumps(r) for r in ([dep]*count+[target,dict(reason='build-finished',success=True)]))+'\n').encode()

    def stream(self,raw):
        events=[];stream=d.CargoStream(emit=events.append)
        for offset in range(0,len(raw),4096):stream.feed(raw[offset:offset+4096])
        return stream,events

    def test_all_large_raw_records_hashed_not_diagnostic_subset(self):
        raw=self.fixture(100);stream,events=self.stream(raw)
        payload=stream.finish(0);proof=json.loads(payload.splitlines()[-1])
        self.assertGreater(len(raw),32768);self.assertEqual(proof['raw_stdout_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(proof['messages'],102);self.assertEqual(proof['raw_stdout_bytes'],len(raw))
        self.assertEqual((len(events),events[-1]['omitted_artifacts']),(21,81))

    def test_only_closed_groups_not_raw_dependency_names(self):
        stream,events=self.stream(self.fixture(1));stream.finish(0)
        text=''.join(d.encode_event(r).decode() for r in events)
        self.assertNotIn('private_unreported_name',text)
        self.assertEqual(events[0]['group'],'dependency');self.assertEqual(events[1]['group'],'product-libtest')

    def test_complete_event_parser_has_explicit_diagnostic_boundary(self):
        stream,events=self.stream(self.fixture());stream.finish(0)
        seen=d.observe(''.join(d.encode_event(r).decode() for r in events))
        self.assertTrue(seen['closing_observed']);self.assertFalse(seen['exact_compiler_or_linker_phase_verified'])
        self.assertFalse(seen['native_Process_query_started']);self.assertEqual(seen['unobserved_artifacts'],0)

    def test_stop_partial_not_complete_stream_or_build(self):
        stream,events=self.stream(self.fixture())
        seen=d.observe(d.encode_event(events[0]).decode()+d.PREFIX+'{"kind":')
        self.assertFalse(seen['closing_observed']);self.assertGreater(seen['partial_marker_bytes'],0)
        self.assertIsNone(seen['unobserved_artifacts'])

    def test_duplicate_sequence_and_after_close_denied(self):
        stream,events=self.stream(self.fixture());stream.finish(0)
        text=''.join(d.encode_event(r).decode() for r in events)
        for wrong in (text+d.encode_event(events[0]).decode(),text.replace('"sequence":1','"sequence":2')):
            with self.assertRaises(ValueError):d.observe(wrong)

    def test_unknown_fields_private_groups_bad_types_denied(self):
        valid=dict(kind='artifact',sequence=1,group='dependency',fresh=None,omitted_artifacts=0)
        for wrong in (dict(valid,path='secret'),dict(valid,group='private'),dict(valid,sequence=True),dict(valid,fresh=1)):
            with self.assertRaises(ValueError):d.encode_event(wrong)

    def test_original_duplicate_json_warning_and_bad_profile_not_bypassed(self):
        for raw in (b'{"reason":"build-finished","reason":"compiler-artifact"}\n',
            b'{"reason":"compiler-message","message":{"level":"warning"}}\n',
            self.fixture().replace(b'"test": true',b'"test": false')):
            with self.assertRaises(ValueError):self.stream(raw)

    def test_original_stderr_and_record_budgets_still_fail(self):
        stream,events=self.stream(self.fixture())
        with self.assertRaises(ValueError):stream.finish(32769)
        self.assertFalse(any(r['kind']=='closed' for r in events))
        with self.assertRaises(ValueError):self.stream(b'x'*32769)

    def test_every_frame_and_total_diagnostic_bound(self):
        stream,events=self.stream(self.fixture(100));stream.finish(0)
        encoded=[d.encode_event(r) for r in events]
        self.assertLessEqual(max(map(len,encoded)),256);self.assertLessEqual(sum(map(len,encoded)),21*256)

    def test_duplicate_close_or_missing_original_finish_denied(self):
        stream,events=self.stream(self.fixture());stream.finish(0)
        with self.assertRaises(ValueError):stream.finish(0)
        stream,events=self.stream(self.fixture().split(b'{"reason": "build-finished"')[0])
        with self.assertRaises(ValueError):stream.finish(0)

if __name__=='__main__':unittest.main()
