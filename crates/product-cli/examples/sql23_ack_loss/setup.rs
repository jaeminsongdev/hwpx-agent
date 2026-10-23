//! One cluster/schema, four isolated tenants. Original bootstrap/role/SQL source is reused unchanged.
use super::*;
// Only the legacy fixture's DB identity check sees the shared cluster root. Its seed/save/artifact
// functions remain the outer case-scoped implementations. No operational path is selectable.
fn owned_root()->Result<PathBuf>{super::common_root()}
#[path="../sql23_storage/setup.rs"] mod legacy;
pub use legacy::{fixture,seed,register};
pub fn provision()->Result<Value>{
    check(case()? != "register_after","ACK_INITIAL_FIXTURE_REQUIRED")?;
    let mut c=raw(&value("P09_SQL23_ADMIN_USER")?,&value("P09_SQL23_ADMIN_PASSWORD")?)?;
    let actual:String=c.query_one("SELECT current_setting('data_directory')",&[])?.try_get(0)?;
    check(fs::canonicalize(actual)?==fs::canonicalize(owned_root()?.join("cluster/data"))?,"ACK_PROVISION_DATABASE_NOT_OWNED")?;
    const SEED:&str=include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/postgres_revision_adapter.sql"));
    check(SEED.matches("WITH seed AS (").count()==1,"ACK_PROVISION_BOUNDARY")?;
    let header=SEED.split("WITH seed AS (").next().ok_or("ACK_PROVISION_HEADER")?
        .replace("00000000-0000-0000-0000-000000000001",&id(1).to_string())
        .replace("p09-revision-probe",&format!("p09-revision-probe-{}",case()?.replace('_',"-"))).replace("hancom-hangul-2020-secondary",PROFILE);
    c.batch_execute(&format!("{header}\nCOMMIT;"))?;
    Ok(json!({"state":"PASS_NEW_ISOLATED_ACK_TENANT_WITHOUT_CLUSTER_OR_SCHEMA_REINITIALIZATION","metadata_artifacts_seeded":0}))
}
