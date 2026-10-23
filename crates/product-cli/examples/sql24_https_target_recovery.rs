//! One fresh SQL24 HTTPS job and read-only registered recovery; isolated policy/routes, not admission.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_target_recovery_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_SQL_FIXTURE_ONLY");std::process::exit(2)}
