//! Fresh571 only. Prior consumed databases/binaries are never reopened or replayed.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_common_recovery571_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_COMMON571_SQL_FIXTURE_ONLY");std::process::exit(2)}
