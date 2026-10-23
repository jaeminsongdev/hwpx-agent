//! Fresh schema24/HWPX/Windows-key fixture with archived-manifest recovery, not a product route.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::windows_custody_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_ARCHIVED_CUSTODY_FIXTURE_ONLY");std::process::exit(2)}
