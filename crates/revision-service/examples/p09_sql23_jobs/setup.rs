//! Fixed owned fixture only; bootstrap uses genuine legacy lease/CAS, never direct seals or disabled guards.
use super::*;
use std::path::Path;
macro_rules! migration { ($file:literal) => { include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/",$file)).as_slice() }; }
const MIGRATIONS: [&[u8];23] = [
    migration!("0001_p14_metadata.up.sql"),migration!("0002_p14_artifact_service.up.sql"),migration!("0003_p14_revision_cas.up.sql"),
    migration!("0004_p14_history_checkpoints.up.sql"),migration!("0005_p14_job_state_machine.up.sql"),migration!("0006_p14_worker_lease_fencing.up.sql"),
    migration!("0007_p14_idempotency_reconciliation.up.sql"),migration!("0008_p14_cancel_cleanup.up.sql"),migration!("0009_p14_retention_local_mirror.up.sql"),
    migration!("0010_p16_artifact_repository.up.sql"),migration!("0011_p16_plan_source.up.sql"),migration!("0012_p16_durable_plan_store.up.sql"),
    migration!("0013_p16_plan_review_evidence.up.sql"),migration!("0014_p17_history_checkpoint_note.up.sql"),migration!("0015_p17_atomic_mirror_checkpoint.up.sql"),
    migration!("0016_p17_durable_git_mirror_push.up.sql"),migration!("0017_p17_durable_git_mirror_pull.up.sql"),migration!("0018_p09_full_document_ir.up.sql"),
    migration!("0019_p09_authorized_full_ir_intent.up.sql"),migration!("0020_p09_source_form_policy.up.sql"),migration!("0021_p09_source_formula_policy.up.sql"),
    migration!("0022_p09_formula_issuer_registry.up.sql"),migration!("0023_p09_stored_revision_jobs.up.sql")];
const SEED: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/postgres_revision_adapter.sql"));
const ROLES: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/sql23_service_roles.sql"));
pub fn fixture() -> Result<Value> {
    let mut c = raw(&value("P09_SQL23_ADMIN_USER")?, &value("P09_SQL23_ADMIN_PASSWORD")?)?;
    let actual: String = c.query_one("SELECT current_setting('data_directory')", &[]).map_err(|_| "JOB_FIXTURE_PATH_QUERY")?
        .try_get(0).map_err(|_| "JOB_FIXTURE_PATH_ROW")?;
    let allowed = Path::new("D:/devdata/hwpx-agent-p09-pg18-job-286/cluster/data");
    let expected = value("P09_SQL23_OWNED_DATA")?;
    let canonical = |p: &Path| std::fs::canonicalize(p).map_err(|_| "JOB_FIXTURE_CANONICAL_PATH");
    check(expected.is_ascii() && Path::new(&expected).is_absolute() && canonical(Path::new(&actual))? == canonical(allowed)?
        && canonical(Path::new(&expected))? == canonical(allowed)?, "JOB_FIXTURE_NOT_OWNED")?;
    for source in MIGRATIONS {
        let sql = std::str::from_utf8(source).map_err(|_| "JOB_MIGRATION_UTF8")?;
        c.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{sql}", ContentDigest::of(source).hex()))
            .map_err(|_| "JOB_MIGRATION_SQL")?;
    }
    c.batch_execute(ROLES).map_err(|_| "JOB_ROLES_SQL")?;
    // Metadata is explicitly synthetic. This does NOT create encrypted blobs or scanner evidence.
    let seed = SEED.replace("hancom-hangul-2020-secondary", PROFILE).replace(
        "CASE WHEN kind='document_ir' THEN 'application/vnd.hwpx-agent.document-graph+json' ELSE 'application/octet-stream' END",
        "CASE WHEN kind='document_ir' THEN 'application/vnd.hwpx-agent.document-graph+json' WHEN kind='receipt' THEN 'application/json' ELSE 'application/vnd.hancom.hwpx+zip' END");
    check(seed != SEED && seed.contains("application/vnd.hancom.hwpx+zip"), "JOB_EXPLICIT_SYNTHETIC_MEDIA_PROFILE")?;
    c.batch_execute(&seed).map_err(|_| "JOB_SEED_SQL")?; scoped(&mut c)?;
    register(&mut c, 23, PROFILE, &"c".repeat(64), "ready")?;
    let row = c.query_one("SELECT * FROM hwpx_agent.claim_idempotent_job_v2($1,$2,$3,$4::character(64),$5,$6,$7,$8,NULL,0,
        $9::character(64),$10::character(64),$11::character(64),$12::character(64),$13::character(64),$14::character(64),
        $15,$16::character(64),3,1,4,600,$17::character(64))", &[&id(1), &id(2), &id(3), &"a".repeat(64), &id(50), &id(51), &id(52), &id(11),
        &"4".repeat(64), &"5".repeat(64), &"1".repeat(64), &"2".repeat(64), &"6".repeat(64), &"7".repeat(64), &PROFILE, &"c".repeat(64), &"8".repeat(64)])
        .map_err(|_| "JOB_BOOTSTRAP_CLAIM")?;
    check(row.try_get::<_, String>("returned_outcome").map_err(|_| "JOB_BOOTSTRAP_CLAIM_ROW")? == "new", "JOB_BOOTSTRAP_NEW")?;
    let row = c.query_one("SELECT * FROM hwpx_agent.lease_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,120,$8::character(64))",
        &[&id(1), &id(2), &"a".repeat(64), &id(50), &id(51), &id(23), &id(53), &"9".repeat(64)]).map_err(|_| "JOB_BOOTSTRAP_LEASE")?;
    let auth: Uuid = row.try_get("returned_commit_authorization_id").map_err(|_| "JOB_BOOTSTRAP_AUTH_ROW")?;
    for (from, to) in [("leased", "staged"), ("staged", "executing"), ("executing", "validating")] {
        c.query_one("SELECT * FROM hwpx_agent.advance_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,1,1,$8,$9,$10::character(64))",
            &[&id(1), &id(2), &"a".repeat(64), &id(50), &id(51), &id(23), &id(53), &from, &to, &"b".repeat(64)]).map_err(|_| "JOB_BOOTSTRAP_ADVANCE")?;
    }
    let row = c.query_one("SELECT * FROM hwpx_agent.commit_idempotent_revision_cas_v2($1,$2,$3,$4::character(64),$5,$6,$7,$8,1,1,$9,$10,NULL,0,$11,ARRAY[]::uuid[],$12,$13,NULL,
        $14::character(64),'verified',$15::character(64),$16::character(64),$17::character(64),$18::character(64))",
        &[&id(1), &id(2), &id(3), &"a".repeat(64), &id(50), &id(51), &id(23), &id(53), &auth, &id(21), &id(20), &id(11), &id(12),
        &"7".repeat(64), &"d".repeat(64), &"6".repeat(64), &"e".repeat(64), &"f".repeat(64)]).map_err(|_| "JOB_BOOTSTRAP_CAS")?;
    check(row.try_get::<_, String>("outcome").map_err(|_| "JOB_BOOTSTRAP_CAS_ROW")? == "committed"
        && row.try_get::<_, i64>("committed_generation").map_err(|_| "JOB_BOOTSTRAP_CAS_ROW")? == 1, "JOB_BOOTSTRAP_CAS_RESULT")?;
    Ok(json!({"state":"PASS_OWNED_SQL23_SYNTHETIC_FIXTURE_WITH_REAL_LEGACY_LEASE_AND_BOOTSTRAP_CAS", "migrations":23,
        "direct_seal_or_revision_insertion":false,"guards_disabled":false,"legacy_rights_granted_to_application":false,"synthetic_metadata":true}))
}
