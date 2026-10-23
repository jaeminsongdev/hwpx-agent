//! All 36 immutable P77 originals, real signed component, synthetic server; no native/production trust.
use super::*;
#[path = "corpus/verification.rs"]
mod verification;
#[path = "corpus/changed.rs"]
mod changed;
use verification::{expected, verify_package};

fn ingests(s: &StoredFixture) -> AnyResult<usize> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}
fn corpus() -> AnyResult<Vec<Vec<u8>>> {
    super::super::formula_evaluation::fixture::inputs::actual_corpus()
}

#[test]
fn all36_frozen_originals_signed_full_candidates_or_no_formula_denial_and_live_revocation()
-> TestResult {
    let inputs = corpus()?;
    let mut counts = (0, 0, 0, 0, 0, 0);
    let mut receipts = Vec::new();
    for (index, bytes) in inputs.iter().enumerate() {
        let wanted = expected(bytes)?;
        let s = StoredFixture::new(bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        let clock = Clock::default();
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        if wanted.targets == 0 {
            assert!(register(&s, &p, &server, true, 0).is_err());
            assert!(
                StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, bytes)?)
                    .is_err()
            );
            assert!(server.policy.lock().map_err(|_| "row")?.is_none());
            assert!(server.proof.lock().map_err(|_| "proof")?.is_none());
            assert_eq!(ingests(&s)?, 2);
            no_publication(&s)?;
            counts.1 += 1;
            receipts.push(json!({"index":index,"source_sha256":ContentDigest::of(bytes),"outcome":"no_formula_denied_no_policy_proof_or_result"}));
            continue;
        }
        register(&s, &p, &server, true, 0)?;
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, bytes)?)?;
        let candidate = prepared.with_verified_bytes(&p, &deps, <[u8]>::to_vec)?;
        assert!(candidate == wanted.bytes, "full_candidate_index={index}");
        verify_package(bytes, &candidate)?;
        assert_eq!(
            prepared.receipt().product.policy.formula_targets,
            wanted.targets
        );
        assert_eq!(
            prepared.receipt().product.policy.allowed_targets,
            wanted.targets
        );
        assert_eq!(
            prepared.receipt().product.policy.source_package_sha256,
            ContentDigest::of(bytes)
        );
        assert_eq!(prepared.receipt().issuer.policy_generation, 1);
        assert_eq!(
            matches!(
                prepared.receipt().product.product.formula,
                FormulaPreparationReceipt::Changed { .. }
            ),
            wanted.changed
        );
        assert!(prepared.require_current_product_route(&p, &deps).is_err());
        assert_eq!(ingests(&s)?, 4);
        let before = s.metadata.audit_events()?.len();
        server.proof_revoked.store(true, Ordering::SeqCst);
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, bytes)?)
                .is_err()
        );
        assert_eq!(ingests(&s)?, 4);
        assert!(s.metadata.audit_events()?.len() >= before);
        no_publication(&s)?;
        counts.0 += 1;
        counts.2 += wanted.targets;
        counts.3 += wanted.cells;
        if wanted.changed {
            counts.4 += 1;
        } else {
            counts.5 += 1;
        }
        receipts.push(json!({"index":index,"source_sha256":ContentDigest::of(bytes),"candidate_sha256":ContentDigest::of(&candidate),
            "outcome":if wanted.changed {"changed"} else {"unchanged"},"formula_targets":wanted.targets,
            "source_cell_bindings":wanted.cells,"whole_candidate_and_outside_leaves_exact":true,"live_revocation_denied_callback":true}));
    }
    assert_eq!((counts.0, counts.1, counts.2, counts.3), (16, 20, 16, 128));
    assert_eq!(counts.4 + counts.5, 16);
    assert!(corpus()? == inputs, "original_corpus_changed");
    eprintln!(
        "P120_ORIGINAL_CORPUS_RECEIPT:{}",
        serde_json::to_string(&json!({"counts":counts,"originals":receipts,
        "qualification":"all_originals_signed_source_component_NOT_production_trust_SQL_native_or_Gate"}))?
    );
    Ok(())
}

#[test]
fn all16_current_derivatives_are_signed_exact_noops_then_denied_new_policy_and_expired_approval()
-> TestResult {
    let inputs = corpus()?;
    let mut count = 0;
    for bytes in &inputs {
        let wanted = expected(bytes)?;
        if wanted.targets == 0 {
            continue;
        } // All no-formula originals are explicitly denied in all36 test.
        let current = wanted.bytes;
        let s = StoredFixture::new(&current, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        let clock = Clock::default();
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        register(&s, &p, &server, true, 0)?;
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &current)?)?;
        assert!(matches!(
            prepared.receipt().product.product.formula,
            FormulaPreparationReceipt::Unchanged { .. }
        ));
        assert!(
            prepared.with_verified_bytes(&p, &deps, <[u8]>::to_vec)? == current,
            "current_candidate_changed"
        );
        assert!(prepared.require_current_product_route(&p, &deps).is_err());
        clock.value.store(300, Ordering::SeqCst);
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
        clock.value.store(12, Ordering::SeqCst);
        register(&s, &p, &server, false, 1)?;
        assert_eq!(server.policy()?.binding.policy_generation, 2);
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &current)?)
                .is_err()
        );
        assert_eq!(ingests(&s)?, 6);
        no_publication(&s)?;
        count += 1;
    }
    assert_eq!(count, 16);
    assert!(corpus()? == inputs, "original_corpus_changed");
    eprintln!(
        "P120_CURRENT_DERIVATIVES_RECEIPT:16_signed_exact_noop_expiry_and_new_denial_pass_NOT_native_or_production_trust"
    );
    Ok(())
}

#[test]
fn all16_actual_formula_sources_and_current_derivatives_keep_native_cell_protection_denial()
-> TestResult {
    let inputs = corpus()?;
    let mut count = 0;
    for original in &inputs {
        let wanted = expected(original)?;
        if wanted.targets == 0 {
            continue;
        }
        for bytes in [original, &wanted.bytes] {
            let protected = fixture::protect(bytes, "Contents/section0.xml", 0)?;
            let s = StoredFixture::new(&protected, ArtifactKind::Result, false)?;
            let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
            let p = writer(&s, &c)?;
            let server = Server::new(&s)?;
            let clock = Clock::default();
            let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
            register(&s, &p, &server, true, 0)?;
            assert!(
                StoredProductRequest::prepare_formula_with_issuer(
                    &p,
                    &deps,
                    &request(&s, &protected)?
                )
                .is_err()
            );
            assert_eq!(ingests(&s)?, 4);
            no_publication(&s)?;
            count += 1;
        }
    }
    assert_eq!(count, 32);
    assert!(corpus()? == inputs, "original_corpus_changed");
    eprintln!(
        "P120_PROTECTION_DERIVATIVES_RECEIPT:32_signed_protected_original_and_current_denials_pass_NOT_native_or_production_trust"
    );
    Ok(())
}
