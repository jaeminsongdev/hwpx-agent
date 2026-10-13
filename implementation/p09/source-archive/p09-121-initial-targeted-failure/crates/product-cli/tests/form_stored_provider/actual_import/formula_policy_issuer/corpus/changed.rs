//! P121: one numeric input leaf in RAM, signed Changed/current consumers; not native/production trust.
use super::*;
#[path = "changed/consumer.rs"]
mod consumer;
#[path = "changed/mutation.rs"]
mod mutation;
use mutation::numeric_derivative;

#[test]
fn all16_original_numeric_derivatives_have_signed_changed_candidates_exact_current_and_live_revocation()
-> TestResult {
    let inputs = corpus()?;
    let mut rows = Vec::new();
    for (index, original) in inputs.iter().enumerate() {
        if expected(original)?.targets == 0 {
            continue; // All original no-formula20 are denied in the unchanged P120 test.
        }
        let derived = numeric_derivative(original)?;
        let wanted = expected(&derived)?;
        assert!(wanted.changed && wanted.targets == 1 && wanted.cells == 8);
        let changed_parts = consumer::changed_parts(&derived, &wanted.bytes)?;
        assert_eq!(changed_parts, 1);
        verify_package(&derived, &wanted.bytes)?;
        consumer::verify_pair(&derived, &wanted.bytes)?;
        rows.push(json!({"index":index,"original_sha256":ContentDigest::of(original),
            "derivative_sha256":ContentDigest::of(&derived),"candidate_sha256":ContentDigest::of(&wanted.bytes),
            "formula_targets":wanted.targets,"source_cell_bindings":wanted.cells,"changed_parts":changed_parts,
            "only_numeric_input_leaf_changed":true,"outside_result_leaves_exact":true,
            "signed_changed_and_current_noop_verified":true,"live_revocation_and_rebinding_denied_callback":true}));
    }
    assert_eq!(rows.len(), 16);
    assert!(corpus()? == inputs, "frozen_original_corpus_changed");
    eprintln!(
        "P121_CHANGED_CORPUS_RECEIPT:{}",
        serde_json::to_string(&json!({"cases":16,"rows":rows}))?
    );
    Ok(())
}

#[test]
fn all32_changed_and_current_numeric_derivatives_keep_valid_signature_cell_protection_denial()
-> TestResult {
    let inputs = corpus()?;
    let mut count = 0;
    for original in &inputs {
        if expected(original)?.targets == 0 {
            continue;
        }
        let derived = numeric_derivative(original)?;
        let wanted = expected(&derived)?;
        assert!(wanted.changed);
        for bytes in [&derived, &wanted.bytes] {
            let protected = fixture::protect(bytes, "Contents/section0.xml", 0)?;
            consumer::verify_protected(&protected)?;
            count += 1;
        }
    }
    assert_eq!(count, 32);
    assert!(corpus()? == inputs, "frozen_original_corpus_changed");
    eprintln!(
        "P121_PROTECTED_CHANGED_RECEIPT:32_signed_changed_and_current_denied_NOT_native_or_production_trust"
    );
    Ok(())
}

#[test]
fn all16_changed_original_comparators_reject_an_extra_numeric_input_leaf_change() -> TestResult {
    let inputs = corpus()?;
    let mut count = 0;
    for original in &inputs {
        if expected(original)?.targets == 0 {
            continue;
        }
        let derived = numeric_derivative(original)?;
        let wanted = expected(&derived)?;
        assert!(wanted.changed);
        verify_package(&derived, &wanted.bytes)?;
        let tampered = numeric_derivative(&wanted.bytes)?;
        let rejected = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            verify_package(&derived, &tampered)
        }));
        assert!(
            matches!(rejected, Err(_) | Ok(Err(_))),
            "outside_leaf_tamper_accepted"
        );
        count += 1;
    }
    assert_eq!(count, 16);
    assert!(corpus()? == inputs, "frozen_original_corpus_changed");
    eprintln!(
        "P121_OUTSIDE_LEAF_COUNTEREXAMPLES_RECEIPT:16_changed_candidate_input_tampers_denied_NOT_native_or_production_trust"
    );
    Ok(())
}
