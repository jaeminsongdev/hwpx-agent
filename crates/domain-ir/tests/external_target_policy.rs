use domain_ir::{ExternalLinkPolicy,ExternalTargetApproval,HyperlinkTarget,LinkReferenceLimits,LogicalId};
type Result<T=()>=std::result::Result<T,Box<dyn std::error::Error>>;
fn limits()->Result<LinkReferenceLimits>{Ok(LinkReferenceLimits::new(Default::default())?)}
fn policy(target:&HyperlinkTarget)->Result<ExternalLinkPolicy>{Ok(ExternalLinkPolicy{allow_https:true,allow_mailto:true,allow_managed_documents:true,
    approvals:vec![ExternalTargetApproval{kind:target.external_kind().ok_or("external")?,target_sha256:target.external_approval_sha256(limits()?)?}],policy_revision_sha256:"a".repeat(64)})}
#[test]
fn exact_approvals_keep_original_policy_shape_and_enablement_requirements()->Result{
    let target=HyperlinkTarget::Https{uri:"https://example.org/approved".into()};let valid=policy(&target)?;valid.require_external_target(&target,limits()?)?;
    let mut missing=valid.clone();missing.approvals.clear();assert!(missing.require_external_target(&target,limits()?).is_err());
    let mut disabled=valid.clone();disabled.allow_https=false;assert!(disabled.require_external_target(&target,limits()?).is_err());
    let mut wrong=valid.clone();wrong.approvals[0].target_sha256="b".repeat(64);assert!(wrong.require_external_target(&target,limits()?).is_err());
    let mut duplicate=valid.clone();duplicate.approvals.push(duplicate.approvals[0].clone());assert!(duplicate.require_external_target(&target,limits()?).is_err());
    let mut revision=valid.clone();revision.policy_revision_sha256="invalid".into();assert!(revision.require_external_target(&target,limits()?).is_err());Ok(())
}
#[test]
fn all_original_external_kinds_use_typed_digest_and_internal_targets_are_denied()->Result{
    for target in [HyperlinkTarget::Https{uri:"https://example.org/a?x=1&y=2".into()},HyperlinkTarget::Mailto{address:"person@example.org".into()},
        HyperlinkTarget::ManagedDocument{artifact_id:LogicalId::parse("managed-artifact")?,bookmark_name:None}]{policy(&target)?.require_external_target(&target,limits()?)?;}
    let target=HyperlinkTarget::Https{uri:"https://example.org/a".into()};let p=policy(&target)?;
    assert!(p.require_external_target(&HyperlinkTarget::InternalBookmark{bookmark_id:LogicalId::parse("bookmark")?},limits()?).is_err());Ok(())
}
#[test]
fn uri_shape_validation_and_digest_exactness_cannot_be_bypassed_by_a_policy_flag()->Result{
    let a=HyperlinkTarget::Https{uri:"https://example.org/a".into()};let p=policy(&a)?;
    for uri in ["https://example.org/A","https://example.org/a#fragment","http://example.org/a","https://user@example.org/a","https://example.org:99999/a","javascript:alert(1)"]{
        assert!(p.require_external_target(&HyperlinkTarget::Https{uri:uri.into()},limits()?).is_err());}Ok(())
}
#[test]
fn prepared_binary_lookup_equals_original_rules_across_large_typed_approval_sets()->Result{
    let mut targets=Vec::new();for i in 0..256{targets.push(HyperlinkTarget::Https{uri:format!("https://example.org/approved/{i}")});}
    targets.push(HyperlinkTarget::Mailto{address:"person@example.org".into()});
    targets.push(HyperlinkTarget::ManagedDocument{artifact_id:LogicalId::parse("managed")?,bookmark_name:None});
    let mut p=policy(&targets[0])?;p.approvals.clear();
    for t in &targets{p.approvals.push(ExternalTargetApproval{kind:t.external_kind().ok_or("kind")?,target_sha256:t.external_approval_sha256(limits()?)?});}p.approvals.sort();
    let prepared=p.validated_external_targets(limits()?)?;
    for t in targets.iter().chain([HyperlinkTarget::Https{uri:"https://example.org/missing".into()},HyperlinkTarget::Https{uri:"http://example.org/a".into()},
        HyperlinkTarget::InternalBookmark{bookmark_id:LogicalId::parse("bookmark")?}].iter()){
        assert_eq!(prepared.require_external_target(t),p.require_external_target(t,limits()?));}
    assert!(!format!("{prepared:?}").contains("https:"));Ok(())
}
#[test]
fn prepared_view_never_accepts_invalid_unsorted_or_disabled_policy_state()->Result{
    let a=HyperlinkTarget::Https{uri:"https://example.org/a".into()};let mut p=policy(&a)?;
    p.approvals.push(p.approvals[0].clone());assert!(p.validated_external_targets(limits()?).is_err());
    p.approvals.pop();p.policy_revision_sha256="invalid".into();assert!(p.validated_external_targets(limits()?).is_err());
    p.policy_revision_sha256="a".repeat(64);p.allow_https=false;assert!(p.validated_external_targets(limits()?).is_err());
    p.allow_https=true;let b=HyperlinkTarget::Https{uri:"https://example.org/b".into()};p.approvals.push(ExternalTargetApproval{kind:b.external_kind().ok_or("kind")?,target_sha256:b.external_approval_sha256(limits()?)?});
    p.approvals.sort();p.approvals.reverse();assert!(p.validated_external_targets(limits()?).is_err());Ok(())
}
