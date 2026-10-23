//! Fresh schema24/OS-key fixture: public strict request to registered effect, no saved locator.
#[cfg(windows)]#[path="sql23_storage.rs"]#[allow(dead_code)]mod storage;
#[cfg(windows)]fn main(){storage::public_request_recovery_main()}
#[cfg(not(windows))]fn main(){eprintln!("WINDOWS_PUBLIC_REQUEST_RECOVERY_FIXTURE_ONLY");std::process::exit(2)}
