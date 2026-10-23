//! Fresh584 common-request late-revocation fixture only; never reopen a consumed database.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_common_late584_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_COMMON_LATE584_SQL_FIXTURE_ONLY");std::process::exit(2)}
