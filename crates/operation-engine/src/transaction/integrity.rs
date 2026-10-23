//! Bounded streaming identity checks after callbacks and publication, not a filesystem write lock.
use super::*;

impl WorkspaceTransaction {
    pub(super) fn verify_staged_result_identity(&self) -> Result<(), TransactionError> {
        let staged = self.output_staged.as_ref().ok_or(TransactionError::InvalidState)?;
        self.verify_result_reader(self.workspace.open_staged(staged).map_err(map_workspace)?)
    }

    pub(super) fn verify_published_result_identity(&self) -> Result<(), TransactionError> {
        let relative = self.output_relative.as_ref().ok_or(TransactionError::InvalidState)?;
        self.verify_result_reader(self.workspace.open_output(relative).map_err(map_workspace)?)
    }

    fn verify_result_reader(&self, reader: impl Read) -> Result<(), TransactionError> {
        let expected_size = self.result_size.ok_or(TransactionError::InvalidState)?;
        let expected_sha256 = self.result_sha256.ok_or(TransactionError::InvalidState)?;
        if expected_size == 0 || expected_size > self.limits.max_output_bytes {
            return Err(TransactionError::InvalidOutput);
        }
        let mut reader = reader.take(self.limits.max_output_bytes.saturating_add(1));
        let mut bytes = [0_u8; 64 * 1024];
        let mut digest = Sha256::new();
        let mut size = 0_u64;
        loop {
            let count = reader.read(&mut bytes).map_err(|_| TransactionError::WorkspaceFailure)?;
            if count == 0 { break; }
            size = size.checked_add(u64::try_from(count).map_err(|_| TransactionError::LimitExceeded)?)
                .filter(|n| *n <= expected_size).ok_or(TransactionError::InvalidOutput)?;
            digest.update(&bytes[..count]);
        }
        if size != expected_size || <[u8; 32]>::from(digest.finalize()) != expected_sha256 {
            return Err(TransactionError::InvalidOutput);
        }
        Ok(())
    }
}
