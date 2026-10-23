//! One fresh schema24 common-search storage/recovery path, no Hancom or operational database.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::search_request_recovery_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_SEARCH_SQL_FIXTURE_ONLY");std::process::exit(2)}
