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
