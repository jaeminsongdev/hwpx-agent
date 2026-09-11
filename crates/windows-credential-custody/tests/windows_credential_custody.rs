#![cfg(windows)]

use std::collections::HashMap;
use std::error::Error;

use keyring_core::api::CredentialStoreApi;
use local_sync::{CredentialFailure, RemoteCredentialProvider};
use remote_credential_broker::{CredentialVault, VaultObservation};
use serde_json::json;
use sha2::{Digest as _, Sha256};
use uuid::Uuid;
use windows_credential_custody::{WindowsCredentialManagerProvider, WindowsCredentialManagerVault};
use zeroize::Zeroizing;

type TestResult = Result<(), Box<dyn Error>>;
const SYNTHETIC_TOKEN: &[u8] = b"aaa.bbb.ccc";

struct CredentialCleanup {
    entry: keyring_core::Entry,
    armed: bool,
}

impl Drop for CredentialCleanup {
    fn drop(&mut self) {
        if self.armed {
            let _ = self.entry.delete_credential();
        }
    }
}

#[test]
#[ignore = "creates and deletes one unique synthetic Windows Credential Manager entry"]
fn current_user_store_is_persistent_redacted_and_single_attempt() -> TestResult {
    let nonce = Uuid::new_v4().simple().to_string();
    let service = format!("qualification.{nonce}");
    let account = format!("synthetic.{nonce}");
    let mut provider = WindowsCredentialManagerProvider::new(&service, &account)?;
    let mut vault = WindowsCredentialManagerVault::new(&service, &account)?;
    let target = provider.target_name().to_owned();
    assert_eq!(vault.target_name(), target);
    let store = windows_native_keyring_store::Store::new()?;
    let modifiers = HashMap::from([("target", target.as_str()), ("persistence", "Local")]);
    let entry = store.build(
        "hwpx-agent.remote-sync",
        "brokered-service-bearer",
        Some(&modifiers),
    )?;
    if vault.observe()? != VaultObservation::Absent
        || !matches!(entry.get_secret(), Err(keyring_core::Error::NoEntry))
    {
        return Err("unique preflight credential is not exactly absent".into());
    }

    vault.store(std::str::from_utf8(SYNTHETIC_TOKEN)?)?;
    let mut cleanup = CredentialCleanup { entry, armed: true };

    let authorization = provider.authorization_header()?;
    let authorization_debug = format!("{authorization:?}");
    let provider_debug = format!("{provider:?}");
    assert!(matches!(
        provider.authorization_header(),
        Err(CredentialFailure::Unavailable)
    ));
    assert!(authorization_debug.contains("<redacted>"));
    assert!(!authorization_debug.contains("aaa.bbb.ccc"));
    assert!(provider_debug.contains("<redacted>"));
    assert!(!provider_debug.contains(&target));

    let persisted = Zeroizing::new(cleanup.entry.get_secret()?);
    assert_eq!(persisted.as_slice(), SYNTHETIC_TOKEN);
    assert_eq!(
        vault.observe()?,
        VaultObservation::Present {
            credential_sha256: hex::encode(Sha256::digest(SYNTHETIC_TOKEN))
        }
    );
    assert_eq!(
        cleanup.entry.get_attributes()?.get("persistence"),
        Some(&"Local".to_owned())
    );

    vault.delete()?;
    cleanup.armed = false;
    assert_eq!(vault.observe()?, VaultObservation::Absent);
    assert!(matches!(
        cleanup.entry.get_secret(),
        Err(keyring_core::Error::NoEntry)
    ));
    let receipt = json!({
        "schema_version": "hwpx-agent.windows-credential-custody-runtime/v1",
        "backend": "windows_credential_manager",
        "persistence": "local_machine_current_user_until_delete",
        "credential_target_sha256": hex::encode(Sha256::digest(target.as_bytes())),
        "checks": {
            "unique_target_preflight_absent": true,
            "product_vault_secret_written": true,
            "product_vault_digest_observed": true,
            "product_provider_read": true,
            "authorization_shape_accepted": true,
            "provider_single_attempt": true,
            "secret_persisted_after_read": true,
            "debug_redacted": true,
            "product_vault_credential_deleted": true,
            "post_cleanup_absent": true
        },
        "claims": {
            "synthetic_credential_only": true,
            "existing_credentials_enumerated": false,
            "real_service_credential": false,
            "actual_remote_network": false,
            "registered_host": false,
            "production": false,
            "p17_06_complete": false,
            "product_complete": false
        }
    });
    println!(
        "HWPX_AGENT_CREDENTIAL_CUSTODY_RECEIPT={}",
        serde_json::to_string(&receipt)?
    );
    Ok(())
}
