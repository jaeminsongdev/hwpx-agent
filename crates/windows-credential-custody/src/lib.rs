//! Windows Credential Manager custody for one externally issued service bearer.
//!
//! This crate deliberately exposes retrieval only. Credential creation, rotation, deletion and
//! service-token issuance belong to a trusted installer or identity broker outside this crate.

#![forbid(unsafe_code)]

#[cfg(windows)]
mod windows {
    use std::collections::HashMap;
    use std::fmt;
    use std::sync::Arc;

    use keyring_core::api::CredentialStoreApi;
    use local_sync::{AuthorizationHeader, CredentialFailure, RemoteCredentialProvider};
    use zeroize::Zeroizing;

    const MAX_LOCATOR_BYTES: usize = 120;
    // CRED_MAX_CREDENTIAL_BLOB_SIZE from wincred.h is 5 * 512 bytes.
    const MAX_TOKEN_BYTES: usize = 2_560;

    /// Single-attempt reader for one short-lived JWT stored by a trusted launcher or broker.
    ///
    /// The credential entry stores the JWT body only, without the `Bearer ` prefix. Product code
    /// can neither create nor delete the entry through this type. A provider instance consumes its
    /// one retrieval attempt even when the platform store is unavailable, so accidental retries
    /// cannot turn credential lookup into an enumeration surface.
    pub struct WindowsCredentialManagerProvider {
        store: Arc<windows_native_keyring_store::Store>,
        target_name: String,
        consumed: bool,
    }

    impl WindowsCredentialManagerProvider {
        /// Binds one exact non-secret Credential Manager locator.
        ///
        /// # Errors
        ///
        /// Rejects empty, oversized, non-ASCII or separator/control-bearing locators, or an
        /// unavailable native credential store.
        pub fn new(service: &str, account: &str) -> Result<Self, CredentialFailure> {
            validate_locator(service)?;
            validate_locator(account)?;
            let target_name = format!("hwpx-agent.remote-sync:{account}:{service}");
            let store = windows_native_keyring_store::Store::new()
                .map_err(|_| CredentialFailure::Unavailable)?;
            Ok(Self {
                store,
                target_name,
                consumed: false,
            })
        }

        /// Reports whether this provider instance has not attempted retrieval yet.
        #[must_use]
        pub const fn available(&self) -> bool {
            !self.consumed
        }

        /// Returns the deterministic non-secret target used by the trusted credential installer.
        #[must_use]
        pub fn target_name(&self) -> &str {
            &self.target_name
        }
    }

    impl fmt::Debug for WindowsCredentialManagerProvider {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter
                .debug_struct("WindowsCredentialManagerProvider")
                .field("locator", &"<redacted>")
                .field("available", &self.available())
                .finish()
        }
    }

    impl RemoteCredentialProvider for WindowsCredentialManagerProvider {
        fn authorization_header(&mut self) -> Result<AuthorizationHeader, CredentialFailure> {
            if self.consumed {
                return Err(CredentialFailure::Unavailable);
            }
            self.consumed = true;

            let modifiers = HashMap::from([("target", self.target_name.as_str())]);
            let entry = self
                .store
                .build(
                    "hwpx-agent.remote-sync",
                    "brokered-service-bearer",
                    Some(&modifiers),
                )
                .map_err(|_| CredentialFailure::Unavailable)?;
            authorization_from_secret(entry.get_secret().map_err(map_read_error)?)
        }
    }

    fn authorization_from_secret(
        secret: Vec<u8>,
    ) -> Result<AuthorizationHeader, CredentialFailure> {
        let secret = Zeroizing::new(secret);
        if secret.is_empty() || secret.len() > MAX_TOKEN_BYTES {
            return Err(CredentialFailure::Rejected);
        }
        let token = match String::from_utf8(secret.to_vec()) {
            Ok(token) => Zeroizing::new(token),
            Err(error) => {
                let _invalid = Zeroizing::new(error.into_bytes());
                return Err(CredentialFailure::Rejected);
            }
        };
        let mut header = String::new();
        header
            .try_reserve_exact("Bearer ".len() + token.len())
            .map_err(|_| CredentialFailure::Unavailable)?;
        header.push_str("Bearer ");
        header.push_str(&token);
        AuthorizationHeader::new(header)
    }

    fn map_read_error(error: keyring_core::Error) -> CredentialFailure {
        match error {
            keyring_core::Error::BadEncoding(bytes)
            | keyring_core::Error::BadDataFormat(bytes, _) => {
                let _secret = Zeroizing::new(bytes);
                CredentialFailure::Rejected
            }
            keyring_core::Error::NoEntry
            | keyring_core::Error::NoStorageAccess(_)
            | keyring_core::Error::PlatformFailure(_)
            | keyring_core::Error::NoDefaultStore
            | keyring_core::Error::NotSupportedByStore(_) => CredentialFailure::Unavailable,
            _ => CredentialFailure::Rejected,
        }
    }

    fn validate_locator(value: &str) -> Result<(), CredentialFailure> {
        if value.is_empty()
            || value.len() > MAX_LOCATOR_BYTES
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        {
            return Err(CredentialFailure::Rejected);
        }
        Ok(())
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn locator_and_debug_are_bounded_and_redacted() {
            let provider =
                WindowsCredentialManagerProvider::new("hwpx-agent.remote-sync.test", "tenant_0001")
                    .unwrap_or_else(|error| panic!("provider: {error}"));
            let debug = format!("{provider:?}");
            assert!(debug.contains("<redacted>"));
            assert!(!debug.contains("tenant_0001"));
            assert!(!debug.contains("hwpx-agent.remote-sync.test"));

            for invalid in [
                "",
                "contains space",
                "contains/slash",
                "contains\\slash",
                "비ASCII",
            ] {
                assert_eq!(
                    WindowsCredentialManagerProvider::new(invalid, "tenant_0001").err(),
                    Some(CredentialFailure::Rejected)
                );
            }
            assert_eq!(
                WindowsCredentialManagerProvider::new(
                    &"x".repeat(MAX_LOCATOR_BYTES + 1),
                    "tenant_0001"
                )
                .err(),
                Some(CredentialFailure::Rejected)
            );
        }

        #[test]
        fn retrieved_secret_shape_fails_closed() {
            for invalid in [
                Vec::new(),
                vec![b'a'; MAX_TOKEN_BYTES + 1],
                vec![0xff, 0xfe],
                b"not-a-jwt".to_vec(),
                b"aaa.bbb.ccc.ddd".to_vec(),
            ] {
                assert!(matches!(
                    authorization_from_secret(invalid),
                    Err(CredentialFailure::Rejected)
                ));
            }
            assert!(authorization_from_secret(b"aaa.bbb.ccc".to_vec()).is_ok());
        }
    }
}

#[cfg(windows)]
pub use windows::WindowsCredentialManagerProvider;
