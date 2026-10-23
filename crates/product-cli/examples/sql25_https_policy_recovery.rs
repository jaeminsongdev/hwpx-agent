//! Fresh exact25 source-bound SQL HTTPS policies + guarded job and public recovery. No Native/admission grant.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_policy_recovery_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_POLICY_SQL_FIXTURE_ONLY");std::process::exit(2)}
