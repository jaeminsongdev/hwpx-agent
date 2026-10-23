use artifact_service::ArtifactKind;
use retention_sync_service::RetentionClass;

#[test]
fn authoritative_ir_uses_source_policy_not_short_lived_preview_or_diff_ttl() {
    assert_eq!(
        RetentionClass::from(ArtifactKind::DocumentIr),
        RetentionClass::Source
    );
    assert_ne!(
        RetentionClass::from(ArtifactKind::DocumentIr),
        RetentionClass::Preview
    );
    assert_ne!(
        RetentionClass::from(ArtifactKind::DocumentIr),
        RetentionClass::Diff
    );
}
