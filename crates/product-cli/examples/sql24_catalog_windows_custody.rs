//! Owned SQL24 fixture with Windows-backed artifact keys. No operational provisioning or product route.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::windows_custody_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_CUSTODY_FIXTURE_ONLY");std::process::exit(2)}
