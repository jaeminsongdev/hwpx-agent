use super::*;
#[path="../../../../../tests/support/pinned_p02_registry_fixture.rs"]mod material;
type TestResult=Result<(),Box<dyn std::error::Error>>;
#[test]
fn pinned_actual_signature_counts_target_and_disabled_scope_are_independently_checked()->TestResult{
    let m=material::load()?;let out=PinnedP02RegistryEvidence::verify_pinned_snapshot(m.input())?;let r=out.receipt();
    assert!(r.signature_verified);assert!(!r.routing_enabled&&!r.execution_authority&&!r.runtime_probe_reexecuted&&!r.current_installed_target_observed);
    assert_eq!(r.counts,SignedRegistryCounts{bindings:536,candidates:32,unavailable:504,verified_claims:2,failed_claims:1,blocked_claims:17,not_run_claims:12});
    assert_eq!(out.signed_target().profile_id().as_str(),"hancom-hangul-2020-secondary");assert_eq!(out.signed_target().build(),"11.0.0.9136");
    assert_eq!(out.require_routing(),Err(PinnedRegistryError::RoutingDisabled));Ok(())
}
#[test]
fn pinned_actual_payload_signature_is_verified_not_a_boolean_receipt_claim()->TestResult{
    let m=material::load()?;let e=strict(&m.envelope,MAX_ENVELOPE)?;let key=pem(&m.key)?;
    let p=crate::form_product_request::bounded(&e["payload"],MAX_ENVELOPE)?;let sig=base64::decode(text(&e["signature_base64"])?,64)?;
    assert_eq!(hex::encode(hash(&p)),PAYLOAD_SHA);verify_signature(&key,&p,&sig)?;
    let mut altered=p;altered[0]^=1;assert_eq!(verify_signature(&key,&altered,&sig),Err(PinnedRegistryError::Signature));Ok(())
}
#[test]
fn pinned_actual_signature_bit_tamper_truncation_and_wrong_public_key_are_rejected()->TestResult{
    let m=material::load()?;let e=strict(&m.envelope,MAX_ENVELOPE)?;let key=pem(&m.key)?;
    let p=crate::form_product_request::bounded(&e["payload"],MAX_ENVELOPE)?;let sig=base64::decode(text(&e["signature_base64"])?,64)?;
    let mut altered=sig.clone();altered[0]^=1;assert_eq!(verify_signature(&key,&p,&altered),Err(PinnedRegistryError::Signature));
    assert_eq!(verify_signature(&key,&p,&sig[..63]),Err(PinnedRegistryError::Signature));
    let mut wrong=key;wrong[12]^=1;assert_eq!(verify_signature(&wrong,&p,&sig),Err(PinnedRegistryError::Signature));Ok(())
}
#[test]
fn pinned_envelope_policy_and_public_key_cannot_be_replaced_or_resigned_by_a_caller()->TestResult{
    for mode in 0..3{let mut m=material::load()?;let b=match mode{0=>&mut m.envelope,1=>&mut m.policy,_=>&mut m.key};b[0]^=1;
        assert!(matches!(PinnedP02RegistryEvidence::verify_pinned_snapshot(m.input()),Err(PinnedRegistryError::Pin)));}Ok(())
}
#[test]
fn pinned_empty_inputs_are_rejected_before_json_or_signature_work()->TestResult{
    let m=material::load()?;
    for input in[PinnedP02RegistryBytes{envelope:&[],..m.input()},PinnedP02RegistryBytes{policy:&[],..m.input()},PinnedP02RegistryBytes{public_key:&[],..m.input()}]{
        assert!(matches!(PinnedP02RegistryEvidence::verify_pinned_snapshot(input),Err(PinnedRegistryError::Limit)));}Ok(())
}
#[test]
fn pinned_base64_canonical_vectors_match_exact_octets()->TestResult{
    for(encoded,bytes)in[("Zg==",b"f".as_slice()),("Zm8=",b"fo".as_slice()),("Zm9v",b"foo".as_slice()),("AA==",&[0]),("AAA=",&[0,0]),("AAAA",&[0,0,0])]{
        assert_eq!(base64::decode(encoded,bytes.len())?,bytes);}Ok(())
}
#[test]
fn pinned_base64_noncanonical_padding_bits_whitespace_and_extra_groups_are_rejected()->TestResult{
    for raw in["","A","AAA","====","A===","AB==","AAB=","AA=A","AA==AAAA","AA==\n","_AAA","-AAA","AA A"]{
        assert!(base64::decode(raw,1024).is_err());}Ok(())
}
#[test]
fn pinned_base64_output_limit_is_checked_before_reservation()->TestResult{
    assert_eq!(base64::decode("AAAA",2),Err(PinnedRegistryError::Limit));assert_eq!(base64::decode("AA==",0),Err(PinnedRegistryError::Limit));
    assert_eq!(base64::decode("AA==",1)?,[0]);Ok(())
}
#[test]
fn pinned_strict_json_rejects_duplicate_escaped_nested_keys_arrays_and_trailing_values()->TestResult{
    for raw in[br#"{"a":1,"a":2}"#.as_slice(),br#"{"a":1,"\u0061":2}"#.as_slice(),br#"{"a":{"b":1,"b":2}}"#.as_slice(),b"[]",b"null",b"{}{}"]{
        assert_eq!(strict(raw,1024).err(),Some(PinnedRegistryError::Shape));}Ok(())
}
#[test]
fn pinned_closed_root_shape_and_pem_algorithm_are_not_inferred_from_array_or_length()->TestResult{
    assert_eq!(object(&serde_json::json!(["a"]),&["a"]),Err(PinnedRegistryError::Shape));
    assert_eq!(object(&serde_json::json!({"a":1,"extra":2}),&["a"]),Err(PinnedRegistryError::Shape));
    assert!(pem(b"-----BEGIN RSA PUBLIC KEY-----\nAAAA\n-----END RSA PUBLIC KEY-----\n").is_err());
    let m=material::load()?;let der=pem(&m.key)?;assert_eq!(der.len(),44);assert_eq!(hex::encode(hash(&der)),text(&strict(&m.policy,64*1024)?["key_id"])?.trim_start_matches("ed25519-sha256-"));Ok(())
}
#[test]
fn pinned_all_signed_claims_are_indexed_once_without_becoming_verified_router_support()->TestResult{
    let m=material::load()?;let out=PinnedP02RegistryEvidence::verify_pinned_snapshot(m.input())?;
    for(id,claim)in &out.claims{assert_eq!(out.signed_claim(id),Some(*claim));assert_eq!(out.require_routing(),Err(PinnedRegistryError::RoutingDisabled));}
    assert_eq!(out.signed_claim(&CapabilityId::parse("search.synthetic_absent_test")?),None);
    let mut copied=out.receipt().clone();copied.routing_enabled=true;copied.execution_authority=true;
    assert!(copied.routing_enabled&&copied.execution_authority);
    assert_eq!(out.require_routing(),Err(PinnedRegistryError::RoutingDisabled));assert!(!out.receipt().execution_authority);Ok(())
}
#[test]
fn pinned_redacted_output_drops_private_bindings_payload_signature_and_commands()->TestResult{
    let m=material::load()?;let out=PinnedP02RegistryEvidence::verify_pinned_snapshot(m.input())?;
    for s in[serde_json::to_string(out.receipt())?,format!("{out:?}"),format!("{:?}",out.receipt()),format!("{:?}",m.input())]{
        for forbidden in["bytes_base64","signature_base64","binding_key","HAction","PRIVATE","BEGIN PUBLIC KEY"]{assert!(!s.contains(forbidden));}
    }Ok(())
}
