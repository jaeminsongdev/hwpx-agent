//! One new actual SQL CAS denial; no replay of the successful543 case or Hancom execution.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::https_late_revoke_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_OWNED_HTTPS_LATE_REVOKE_ONLY");std::process::exit(2)}
