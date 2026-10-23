"""Full original monitor projection/inverse, no Job or child creation."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_current_epoch_owned_audit as owned


class OwnedAuditProjectionContracts(unittest.TestCase):
    def test_race_at_original_monitor_call_preserves_failure_without_resetting_failed_monitor(self):
        marker_error='NATIVE011_OWNED_METADATA_AUDIT_NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS'
        class Monitor:
            seen=2;failed=False;MARKERS=('a','b','c','d')
            def accept(self,markers,process):
                self.failed=True;raise ValueError(marker_error)
        monitor=Monitor();process=NS(returncode=2,observe=lambda:None)
        capture=NS(progress=lambda:(['a','b','c'],[]),communicate=lambda timeout:(json.dumps(dict(error_code='MODEL_CHILD_ROOT_CAUSE')),''))
        row=dict(owned={})
        with self.assertRaisesRegex(ValueError,'MODEL_CHILD_ROOT_CAUSE'):
            owned.observe_markers(monitor,['a','b','c'],process,capture,row,owned.preserve_terminal_failure)
        self.assertTrue(monitor.failed);self.assertEqual(monitor.seen,2)
        self.assertEqual(row['owned']['child_summary']['error_code'],'MODEL_CHILD_ROOT_CAUSE')

    def test_terminal_error_preserved_without_any_late_phase_credit(self):
        observed=[];monitor=NS(seen=2,MARKERS=('a','b','c','d'))
        process=NS(returncode=2,observe=lambda:observed.append(1))
        capture=NS(progress=lambda:(['a','b','c'],[]));row=dict(owned={})
        summary=dict(error_code='MODEL_ORIGINAL_METADATA_FAILURE')
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_METADATA_FAILURE'):
            owned.preserve_terminal_failure(process,capture,row,json.dumps(summary),'',monitor)
        self.assertEqual(row['owned']['child_summary'],summary)
        self.assertEqual(row['owned']['uncredited_terminal_markers'],['c'])
        self.assertEqual(monitor.seen,2);self.assertEqual(observed,[1])

    def test_successful_or_live_child_cannot_use_failure_route(self):
        for code in (None,0,False):
            with self.assertRaisesRegex(ValueError,'TERMINAL_FAILED_CHILD_ONLY'):
                owned.preserve_terminal_failure(NS(returncode=code),None,None,None,None,None)

    def test_only_named_identity_labels_and_explicit_original_source_role(self):
        raw=(Path(__file__).resolve().parents[3]/owned.SOURCE['path']).read_bytes()
        node,proof=owned.project(raw)
        values=[n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and type(n.value) is str]
        self.assertTrue(all(value in values for value in owned.LABELS.values()))
        self.assertTrue(all(value not in values for value in owned.LABELS))
        self.assertIn(owned.SOURCE['path'],values)
        self.assertTrue(proof['entire_original_monitor_main_AST_inverse'])

    def test_original_deadline_and_zero_native_guard_literals_retained(self):
        raw=(Path(__file__).resolve().parents[3]/owned.SOURCE['path']).read_bytes()
        node,_=owned.project(raw)
        numbers=[n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and type(n.value) is int]
        self.assertIn(2400,numbers)
        names={n.attr for n in ast.walk(node) if isinstance(n,ast.Attribute)}
        self.assertTrue({'progress','observe','check','finish','close'}<=names)

    def test_nonoriginal_monitor_rejected_before_compilation_or_child(self):
        with self.assertRaisesRegex(ValueError,'EXACT_ENTIRE_ORIGINAL_OWNED_MONITOR_SOURCE'):
            owned.project(b'not the original monitor')
