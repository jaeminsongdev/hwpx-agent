//! Fresh564 only;563 database/binary are consumed and never restarted/replayed.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_common_recovery564_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_COMMON564_SQL_FIXTURE_ONLY");std::process::exit(2)}
