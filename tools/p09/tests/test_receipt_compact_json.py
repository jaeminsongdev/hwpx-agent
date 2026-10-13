import copy
import io
import json
import unittest
import receipt_compact_json as d


class CompactReceiptTests(unittest.TestCase):
    def encode(self, doc, **keywords):
        stream = io.StringIO()
        stats = d.dump(doc, stream, checkpoint=lambda: None, **keywords)
        return stream.getvalue(), stats

    def test_nested_fields_samples_failures_and_input_pins_are_not_removed_or_mutated(self):
        doc = dict(state='FAILED_NOT_ACCEPTED', samples=[dict(cpu=99.25, free_ram=43.5)],
            pins=[dict(path='source.rs', bytes=42, sha256='abc')], error_code='STOP_CPU',
            cleanup=True, product=False, note=None, nested={'a': [1, -2, 1.25, False]})
        before = copy.deepcopy(doc)
        text, stats = self.encode(doc, indent=2)
        self.assertEqual(json.loads(text), before)
        self.assertEqual(doc, before)
        self.assertEqual(list(json.loads(text)), list(before))
        self.assertEqual(stats['semantic_fields_intentionally_removed'], 0)
    def test_unicode_values_roundtrip_as_ascii_without_loss(self):
        doc = {'한글': '수식 😀 \u2028', 'path': r'D:\개발\hwpx-agent'}
        text, stats = self.encode(doc)
        self.assertTrue(text.isascii())
        self.assertEqual(json.loads(text), doc)
        self.assertEqual(stats['characters_written'], len(text.encode('utf-8')))
    def test_spaces_tabs_newlines_inside_values_are_not_stripped(self):
        doc = {'text': '  x\t y\n\r\n  ', 'empty': ''}
        text, _ = self.encode(doc)
        self.assertEqual(json.loads(text), doc)
    def test_large_token_is_written_in_bounded_batches(self):
        doc = {'value': 'z' * (3 * d.WRITE_CHARS + 13)}
        text, stats = self.encode(doc)
        self.assertEqual(json.loads(text), doc)
        self.assertEqual(stats['maximum_write_batch_chars'], d.WRITE_CHARS)
        self.assertGreaterEqual(stats['write_batches'], 4)
    def test_original_guard_runs_before_and_after_each_write(self):
        events = []
        class Stream(io.StringIO):
            def write(self, text):
                events.append('write')
                return super().write(text)
        d.dump({'v': 'x' * (2 * d.WRITE_CHARS)}, Stream(), checkpoint=lambda: events.append('guard'))
        for index, event in enumerate(events):
            if event == 'write':
                self.assertEqual(events[index - 1], 'guard')
                self.assertEqual(events[index + 1], 'guard')
    def test_initial_CPU_stop_is_not_swallowed_and_writes_nothing(self):
        stream = io.StringIO()
        def stop():
            raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with self.assertRaisesRegex(ValueError, 'STOP_SUSTAINED_SYSTEM_CPU'):
            d.dump({'v': 1}, stream, checkpoint=stop)
        self.assertEqual(stream.getvalue(), '')
    def test_stop_after_first_write_is_not_retried_or_swallowed(self):
        stream = io.StringIO()
        def stop():
            if stream.tell():
                raise ValueError('STOP_LOW_AVAILABLE_RAM')
        with self.assertRaisesRegex(ValueError, 'STOP_LOW_AVAILABLE_RAM'):
            d.dump({'v': 'x' * (3 * d.WRITE_CHARS)}, stream, checkpoint=stop)
        self.assertEqual(stream.tell(), d.WRITE_CHARS)
    def test_final_guard_stop_is_not_promoted_to_success(self):
        stream = io.StringIO()
        calls = 0
        def stop():
            nonlocal calls
            calls += 1
            if calls == 4:
                raise ValueError('STOP_SQL_IO_SCOPE_TIME')
        with self.assertRaisesRegex(ValueError, 'STOP_SQL_IO_SCOPE_TIME'):
            d.dump({}, stream, checkpoint=stop)
        self.assertEqual(stream.getvalue(), '{}')
    def test_nonfinite_numbers_are_not_replaced_or_silently_accepted(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                self.encode({'value': value})
    def test_unsupported_objects_and_circular_values_fail(self):
        with self.assertRaises(TypeError):
            self.encode({'value': object()})
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(ValueError):
            self.encode(cycle)
    def test_semantic_override_options_are_rejected(self):
        for keywords in ({'skipkeys': True}, {'default': str}, {'allow_nan': True},
                {'sort_keys': True}, {'indent': 4}, {'ensure_ascii': False}):
            with self.subTest(keys=list(keywords)), self.assertRaisesRegex(ValueError, 'ORIGINAL_INDENT_ONLY'):
                self.encode({'v': 1}, **keywords)
    def test_short_writes_fail_without_retry(self):
        class Short:
            def __init__(self):
                self.calls = 0
            def write(self, text):
                self.calls += 1
                return len(text) - 1
        stream = Short()
        with self.assertRaisesRegex(ValueError, 'COMPLETE_SINGLE_WRITE_NO_RETRY'):
            d.dump({'v': 1}, stream, checkpoint=lambda: None)
        self.assertEqual(stream.calls, 1)
