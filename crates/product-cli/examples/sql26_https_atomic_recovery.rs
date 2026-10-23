//! New exact26 atomic policy+original CAS, not a Native/product admission permit.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_atomic_recovery_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_ATOMIC_SQL_FIXTURE_ONLY");std::process::exit(2)}
