import ast
import copy
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import unittest
import accept_case112_current_epoch as a
import case160_run007_controller as old
import post_product_recovery_window_v1 as tool
import post_product_stop_recovery_v1 as reviewer
from tests.test_strict_product_window_model_v1 import pins

MODULE=None
RAW_WINDOW=(Path(__file__).resolve().parents[3]/tool.WINDOW_PIN["path"]).read_bytes()


def connected():return MODULE.current_window(old.old.prior,tool,RAW_WINDOW)[0]


def fixture():
    raw=(a.c.ROOT/reviewer.CANDIDATE["path"]).read_bytes()
    reviewed=reviewer.review(raw,reviewer.RESPONSE)
    row=dict(reviewed,state=MODULE.REVIEW_STATE,cleanup_confirmed=True,
        fresh_inputs=1,final_fresh_hashes=1,source_pins=[dict(reviewer.CANDIDATE)])
    q=NS(snapshots={},json=lambda name:copy.deepcopy(row),pin=lambda name:dict(reviewer.CANDIDATE))
    def text(name):q.snapshots[name]=dict(reviewer.CANDIDATE);return raw.decode("utf-8")
    q.text=text
    return q,row


class Tests(unittest.TestCase):
    def test_real_private_template_actual_window_budget_and_checker_match(self):
        original=old.old.prior;new=connected()
        self.assertIs(new.template.__code__,original.template.__code__)
        self.assertIs(new.template.__closure__,original.template.__closure__)
        env=new.template.__globals__
        self.assertIs(env["WINDOW"],new.WINDOW);self.assertIs(env["NATIVE"],new.NATIVE)
        self.assertIs(env["DIRECT"],new.DIRECT);self.assertIs(env["WINDOW_LINK"],new.WINDOW_LINK)
        self.assertEqual(new.WINDOW.SECONDS,10);self.assertEqual(original.WINDOW.SECONDS,15)
        row=new.NATIVE.model(pins(),167)
        self.assertEqual(row["product_allowance_seconds"],10)
        self.assertEqual(row["unallocated_margin_seconds"],60)
        self.assertIs(new.DIRECT.runtime_budget.__globals__["views"],new.NATIVE)

    def test_original_history_and_default_namespaces_not_changed(self):
        original=old.old.prior;env=dict(original.template.__globals__)
        native=original.NATIVE.model;check=original.WINDOW_LINK.check_evidence
        connected();connected()
        self.assertEqual(original.template.__globals__,env)
        self.assertIs(original.NATIVE.model,native);self.assertIs(original.WINDOW_LINK.check_evidence,check)
        self.assertEqual(original.NATIVE.model(pins(),167)["product_allowance_seconds"],15)

    def test_complete_capture_checker_inverse_changes_only_window_slot(self):
        original=old.old.prior.WINDOW_LINK.check_evidence;new=connected().WINDOW_LINK.check_evidence
        before=original.__code__;values=list(new.__code__.co_consts)
        slot=next(i for i,v in enumerate(before.co_consts) if type(v) is int and v==15)
        self.assertEqual(values[slot],10);values[slot]=15
        self.assertEqual(new.__code__.replace(co_consts=tuple(values)),before)
        self.assertIs(new.__closure__,original.__closure__)

    def test_full_cost_oracle_changes_product_not_margin_or_inventory(self):
        original=old.old.prior.DIRECT.mechanics_projection
        # Execute the real final mechanics wrapper with an identity prior
        # projection so every original changed_expectations check still runs.
        source='def f():\n fields(budget,dict(product_allowance_seconds=20,unallocated_margin_seconds=60),"RUNTIME_COST")\n'
        new=connected().DIRECT.mechanics_projection
        cells=tuple(__import__("types").CellType(NS(mechanics_projection=lambda node:node))
            if name=="original" else cell for name,cell in zip(new.__code__.co_freevars,new.__closure__))
        isolated=FunctionType(new.__code__,new.__globals__,closure=cells)
        node=isolated(ast.parse(source).body[0]);keywords=node.body[0].value.args[1].keywords
        self.assertEqual([(k.arg,k.value.value) for k in keywords],[("product_allowance_seconds",10),("unallocated_margin_seconds",60)])
        self.assertIn((20,15),original.__code__.co_consts)

    def test_unknown_template_or_already_tightened_window_rejected(self):
        with self.assertRaises(ValueError):MODULE.current_window(NS(template=lambda:None),tool,RAW_WINDOW)
        with self.assertRaises(ValueError):MODULE.current_window(connected(),tool,RAW_WINDOW)

    def test_only_private_current_alias_family_can_be_bound(self):
        family=dict(__name__="p09_exact_fixture",old=old)
        exec("def f():return old\ndef g():return old",family)
        namespace=NS(__name__="p09_exact_fixture",f=family["f"],g=family["g"])
        MODULE.bind_current_prior(namespace,tool,RAW_WINDOW)
        self.assertEqual(namespace.f().old.prior.WINDOW.SECONDS,10)
        self.assertEqual(old.old.prior.WINDOW.SECONDS,15)
        family["__name__"]="not_private"
        with self.assertRaises(ValueError):MODULE.bind_current_prior(namespace,tool,RAW_WINDOW)

    def test_actual_local_import_uses_the_same_private_window(self):
        family=dict(__name__="p09_exact_import_fixture")
        exec("def f():\n import case160_run007_controller as old\n return old.old.prior.WINDOW.SECONDS",family)
        namespace=NS(__name__=family["__name__"],f=family["f"]);before=namespace.f.__code__
        MODULE.bind_current_prior(namespace,tool,RAW_WINDOW)
        self.assertEqual(namespace.f(),10);self.assertIs(namespace.f.__code__,before)
        self.assertEqual(old.old.prior.WINDOW.SECONDS,15)

    def test_receipt_namespace_has_full_inverse_and_no_budget_or_guard_change(self):
        def original():return "old-receipt",600,60,14
        new=MODULE.receipt_namespace(original,{"old-receipt":"new-recovery-receipt"})
        self.assertEqual(new(),("new-recovery-receipt",600,60,14))
        self.assertEqual(original(),("old-receipt",600,60,14))
        with self.assertRaises(ValueError):MODULE.receipt_namespace(new,{"old-receipt":"new-recovery-receipt"})
        with self.assertRaises(ValueError):MODULE.receipt_namespace(original,{"absent":"new"})

    def test_independent_oracle_entire_checker_and_existing_wrapper_retained(self):
        env=dict(base=NS(CONFIG=NS(index=165)),prior=old.CURRENT.M.validator.__globals__["prior"])
        def whole(*args):return "full"
        checker=NS(environment=env,validate_candidate=whole,validator=whole)
        fn=MODULE.connect_oracle(lambda *args:(checker,dict(original=True)),tool,RAW_WINDOW)
        result,proof=fn()
        self.assertIs(result.validate_candidate,whole);self.assertIs(result.validator,whole)
        self.assertEqual(result.environment["prior"].WINDOW.SECONDS,10)
        self.assertTrue(proof["original"])
        self.assertEqual(old.CURRENT.M.validator.__globals__["prior"].WINDOW.SECONDS,15)

    def test_other_oracle_case_cannot_take_current_recovery(self):
        checker=NS(environment=dict(base=NS(CONFIG=NS(index=164))))
        fn=MODULE.connect_oracle(lambda:(checker,{}),tool,RAW_WINDOW)
        with self.assertRaises(ValueError):fn()

    def test_exact_failed_receipt_admitted_only_as_new_full_scope_input(self):
        q,_=fixture();result=MODULE.admit_failed_run(q,NS(index=165,run=8),a,reviewer,lambda *args:True)
        self.assertIn(reviewer.CANDIDATE["path"],q.snapshots)
        self.assertFalse(result["old_body_result_reused"]);self.assertFalse(result["GO_authorized"])
        self.assertTrue(result["two_new_actual_byte_boundaries_and_complete_oracles_required"])

    def test_other_case_run_type_or_existing_next_native_rejected(self):
        q,_=fixture()
        for ctx in (NS(index=164,run=8),NS(index=165,run=7),NS(index=165,run=True)):
            with self.subTest(ctx=vars(ctx)),self.assertRaises(ValueError):MODULE.admit_failed_run(q,ctx,a,reviewer,lambda *args:True)
        for sequence in ([False],[True,False]):
            values=iter(sequence)
            with self.assertRaises(ValueError):MODULE.admit_failed_run(q,NS(index=165,run=8),a,reviewer,lambda *args:next(values))

    def test_review_mismatch_incomplete_hashes_or_fake_GO_rejected(self):
        q,row=fixture()
        for key,value in (("fresh_inputs",True),("final_fresh_hashes",0),("cleanup_confirmed",False),
            ("GO_authorized",True),("candidate_pin",{}),("after_boundary_missing",False),
            ("next_Native_start_authorized",True),("runtime_retry_admission_implemented",True)):
            changed=copy.deepcopy(row);changed[key]=value;q.json=lambda name:changed
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.admit_failed_run(q,NS(index=165,run=8),a,reviewer,lambda *args:True)

    def test_raw_failure_or_current_source_changes_never_accepted(self):
        q,_=fixture();q.snapshots[reviewer.CANDIDATE["path"]]=dict(reviewer.CANDIDATE);q.text=lambda name:"{}"
        with self.assertRaises(ValueError):MODULE.admit_failed_run(q,NS(index=165,run=8),a,reviewer,lambda *args:True)
        q,_=fixture();q.pin=lambda name:dict(reviewer.CANDIDATE,bytes=1)
        with self.assertRaises(ValueError):MODULE.admit_failed_run(q,NS(index=165,run=8),a,reviewer,lambda *args:True)
