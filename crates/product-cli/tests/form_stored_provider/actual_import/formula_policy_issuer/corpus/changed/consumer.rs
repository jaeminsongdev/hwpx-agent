//! Original production component + synthetic issuer only; current/live guards and no publication.
use super::*;

pub(super) fn changed_parts(source: &[u8], candidate: &[u8]) -> AnyResult<usize> {
    let before = fixture::entries(source)?;
    let after = fixture::entries(candidate)?;
    assert!(before.keys().eq(after.keys()));
    Ok(before
        .iter()
        .filter(|(key, value)| after.get(*key) != Some(*value))
        .count())
}

pub(super) fn verify_pair(derived: &[u8], candidate: &[u8]) -> TestResult {
    #[cfg(test)]
    let mut timer = super::cost_profile::Timer::current();
    let s = StoredFixture::new(derived, ArtifactKind::Result, false)?;
    let context = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &context)?;
    let server = Server::new(&s)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    #[cfg(test)]
    timer.record("changed_setup");
    register(&s, &p, &server, true, 0)?;
    #[cfg(test)]
    timer.record("changed_register");
    let product =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, derived)?)?;
    assert!(matches!(
        product.receipt().product.product.formula,
        FormulaPreparationReceipt::Changed { .. }
    ));
    #[cfg(test)]
    timer.record("changed_prepare");
    assert!(
        product.with_verified_bytes(&p, &deps, <[u8]>::to_vec)? == candidate,
        "signed_changed_candidate_mismatch"
    );
    #[cfg(test)]
    timer.record("changed_consume");
    assert!(product.require_current_product_route(&p, &deps).is_err());
    assert_eq!(ingests(&s)?, 4);
    no_publication(&s)?;
    #[cfg(test)]
    timer.record("changed_route_denied");

    let fresh = expected(candidate)?;
    assert!(
        !fresh.changed && fresh.targets == 1 && fresh.cells == 8 && fresh.bytes == candidate,
        "current_recalculation_not_exact_noop"
    );
    #[cfg(test)]
    timer.record("current_expected");
    let current = StoredFixture::new(candidate, ArtifactKind::Result, false)?;
    let current_context =
        RevisionRequestContext::new(current.owner.tenant_id(), current.owner.subject());
    let current_provider = writer(&current, &current_context)?;
    let current_server = Server::new(&current)?;
    let current_clock = Clock::default();
    let current_deps = FormulaIssuerDependencies::new(
        &current_server,
        &current_server,
        &current_server,
        &current_clock,
    );
    #[cfg(test)]
    timer.record("current_setup");
    register(&current, &current_provider, &current_server, true, 0)?;
    #[cfg(test)]
    timer.record("current_register");
    let current_product = StoredProductRequest::prepare_formula_with_issuer(
        &current_provider,
        &current_deps,
        &request(&current, candidate)?,
    )?;
    assert!(matches!(
        current_product.receipt().product.product.formula,
        FormulaPreparationReceipt::Unchanged { .. }
    ));
    #[cfg(test)]
    timer.record("current_prepare");
    assert!(
        current_product.with_verified_bytes(&current_provider, &current_deps, <[u8]>::to_vec)?
            == candidate,
        "signed_current_candidate_changed"
    );
    #[cfg(test)]
    timer.record("current_consume");
    let called = std::cell::Cell::new(false);
    assert!(
        product
            .with_verified_bytes(&current_provider, &current_deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert_eq!(ingests(&current)?, 4);
    no_publication(&current)?;
    #[cfg(test)]
    timer.record("rebind_denied");

    server.proof_revoked.store(true, Ordering::SeqCst);
    let called = std::cell::Cell::new(false);
    assert!(
        product
            .with_verified_bytes(&p, &deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, derived)?)
            .is_err()
    );
    assert_eq!(ingests(&s)?, 4);
    no_publication(&s)?;
    #[cfg(test)]
    timer.record("live_revocation_denied");
    Ok(())
}

pub(super) fn verify_protected(bytes: &[u8]) -> TestResult {
    let s = StoredFixture::new(bytes, ArtifactKind::Result, false)?;
    let context = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &context)?;
    let server = Server::new(&s)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    register(&s, &p, &server, true, 0)?;
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, bytes)?).is_err()
    );
    assert_eq!(ingests(&s)?, 4);
    no_publication(&s)?;
    Ok(())
}
