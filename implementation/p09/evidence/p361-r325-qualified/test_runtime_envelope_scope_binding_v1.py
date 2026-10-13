import copy
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_scope_binding_v1 as m

def fixture():
    raw=b'{"unchanged":true}\r\n';encoded=m.source.codec.encode(raw,lambda:None)
    pin=lambda name,data:dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    logical=pin("implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json",raw)
    physical=pin(m.source.PREFIX+"case157-runtime-run001.envelope.v1.json",encoded)
    manifest=pin("implementation/p09/evidence/test-envelope-manifest.v1.json",b"manifest")
    ordinary=pin("crates/product-cli/src/current.rs",b"ordinary")
    desc=m.source.descriptor(logical,physical,next_case=158)
    binding=m.Binding([desc],manifest,next_case=158)
    semantic={p["path"]:p for p in (logical,manifest,ordinary)}
    projection,_=binding.project(semantic,lambda:None)
    return binding,semantic,projection,raw,encoded

def packet():
    b,semantic,p,raw,encoded=fixture();physical=[dict(x) for x in p.physical_pins.values()]
    n=len(physical);total=sum(x["bytes"] for x in physical);old=next(iter(b.originals))
    d=dict(read_passes=n,bytes_read=total,
        explicit_envelope_semantic_decode=dict(counts={old:1},decoded_bytes=len(raw),semantic_bytes_not_reported_as_disk_bytes=True),
        original_live_boundary_guard_during_decode=dict(calls=1,shared_budget_callback_restored=True,
            original_reader_pressure_Frame_and_lock_checkpoint_retained=True))
    frame=dict(frame_state="CLOSED",registered_live_frame=False,original_owned_cleanup_confirmed_before_release=False,
        input_count=n,input_bytes=total,actual_byte_boundaries=[dict(role=role,actual_byte_pins=copy.deepcopy(physical),reader_diagnostics=copy.deepcopy(d)) for role in ("before","after")],
        handles=dict(input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,input_lock_handles_opened=4,
            input_lock_handles_closed=4,handle_close_failed_attempts=0,byte_stream_identity_checks=2*n,
            active_reader_bindings=0,active_byte_streams=0,maximum_lock_seconds=600))
    row=dict(synthetic_fixture_only_not_evidence=True,source_input_representation=b.representation(p),source_freeze=physical,
        source_frame=frame,aggregate_envelope_decoder=dict(aggregate_limit_seconds=5.0,elapsed_decoder_work_seconds=.1,
            attempted_decodes=2,completed_decodes=2,active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True))
    return b,semantic,row

class Tests(unittest.TestCase):
    def test_only_exact_both_representations_reconcile_and_inputs_unchanged(self):
        b,s,p,raw,encoded=fixture();both=copy.deepcopy(s)
        both.update({name:dict(pin) for name,pin in b.physical.items()})
        before=copy.deepcopy(both);actual,proof=b.semantic_union(both,lambda:None)
        self.assertEqual(actual,s);self.assertEqual(proof["physical_aliases_encountered"],1);self.assertEqual(both,before)
        physical={n:dict(pin) for n,pin in p.physical_pins.items()}
        self.assertEqual(b.semantic_union(physical,lambda:None)[0],s)
    def test_corrupt_alias_missing_original_and_manifest_rejected(self):
        b,s,p,raw,encoded=fixture();name=next(iter(b.originals))
        for changed in ({n:pin for n,pin in s.items() if n!=name},dict(s,**{name:dict(s[name],sha256="0"*64)})):
            with self.assertRaises(ValueError):b.project(changed,lambda:None)
        with self.assertRaisesRegex(ValueError,"MANIFEST_IN_FULL_SOURCE_SCOPE"):
            b.project({n:pin for n,pin in s.items() if n!=b.manifest_pin["path"]},lambda:None)
    def test_full_physical_and_semantic_accounting_no_go_permission(self):
        b,s,row=packet();proof=b.validate_scope_evidence(row,s,lambda:None,require_committed=False)
        self.assertEqual(proof["semantic_input_count"],3);self.assertEqual(proof["physical_input_count"],3)
        self.assertFalse(proof["GO_authorized"]);self.assertFalse(proof["product_or_Gate_qualified"])
    def test_closed_cannot_be_promoted_to_committed_product(self):
        b,s,row=packet()
        with self.assertRaisesRegex(ValueError,"EXACT_TERMINAL_FRAME_NOT_PROMOTION"):b.validate_scope_evidence(row,s,lambda:None)
    def test_original_semantic_bytes_cannot_replace_physical_disk_counters(self):
        b,s,row=packet();row["source_frame"]["actual_byte_boundaries"][0]["reader_diagnostics"]["bytes_read"]=sum(p["bytes"] for p in s.values())
        with self.assertRaisesRegex(ValueError,"ACTUAL_DISK_BYTE_COUNTERS"):b.validate_scope_evidence(row,s,lambda:None,require_committed=False)
    def test_missing_boundary_wrong_roles_and_decoded_counter_rejected(self):
        b,s,row=packet()
        for changed in ("missing","role","decode","counts"):
            r=copy.deepcopy(row);phases=r["source_frame"]["actual_byte_boundaries"]
            if changed=="missing":phases.pop()
            elif changed=="role":phases[0]["role"]="after"
            elif changed=="decode":phases[0]["reader_diagnostics"]["explicit_envelope_semantic_decode"]["decoded_bytes"]+=1
            else:phases[0]["reader_diagnostics"]["explicit_envelope_semantic_decode"]["counts"][next(iter(b.originals))]=1.0
            with self.assertRaises(ValueError):b.validate_scope_evidence(r,s,lambda:None,require_committed=False)
    def test_decoder_over_budget_or_unrestored_guard_is_never_pass(self):
        b,s,row=packet()
        for changed in ("duration","guard","handles"):
            r=copy.deepcopy(row)
            if changed=="duration":r["aggregate_envelope_decoder"]["elapsed_decoder_work_seconds"]=5.01
            elif changed=="guard":r["source_frame"]["actual_byte_boundaries"][1]["reader_diagnostics"]["original_live_boundary_guard_during_decode"]["shared_budget_callback_restored"]=False
            else:r["source_frame"]["handles"]["input_lock_handles_remaining"]=False
            with self.assertRaises(ValueError):b.validate_scope_evidence(r,s,lambda:None,require_committed=False)
    def test_typed_representation_context_and_original_guard_identity(self):
        b,s,row=packet();row["source_input_representation"]["next_case"]=158.0
        with self.assertRaises(ValueError):b.validate_scope_evidence(row,s,lambda:None,require_committed=False)
        error=ValueError("ORIGINAL_HARD_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:b.project(s,stop)
        self.assertIs(caught.exception,error)
    def test_explicit_extra5_charged_and_original_600_60_not_relaxed(self):
        b,s,p,raw,encoded=fixture();seen=[]
        def budget(physical,requests):
            seen.append((physical,requests));return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,predicted_runtime_combined_seconds=590.0)
        result=b.runtime_budget(s,167,budget,lambda:None)
        self.assertEqual(result["predicted_runtime_combined_seconds"],595.0)
        self.assertEqual(result["aggregate_envelope_decoder_allowance_seconds"],5.0)
        self.assertEqual(seen[0][0],{n:dict(pin) for n,pin in p.physical_pins.items()});self.assertFalse(result["GO_authorized"])
        def too_long(physical,requests):return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,predicted_runtime_combined_seconds=596.0)
        with self.assertRaisesRegex(ValueError,"COMPLETE_COST_PLUS_SHARED_DECODER5"):b.runtime_budget(s,167,too_long,lambda:None)

if __name__=="__main__":unittest.main()
