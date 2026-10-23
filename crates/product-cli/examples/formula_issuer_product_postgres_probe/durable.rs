//! Closed driver-owned local backend. No public root/key/authority selector.
//! Same-process handle reopen is not restart recovery or production key custody.
use super::InMemoryBlobStore;
use artifact_service::{ArtifactError, EncryptedBlobStore, LocalEncryptedBlobStore, ObjectKey};
use std::{
    fmt, fs,
    io::Read as _,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
};
use uuid::Uuid;

const MAX_CIPHERTEXT: u64 = 32 * 1024 * 1024 + 16;
const OWNER_FILE: &str = ".p150-owned-run";
const OWNER_SCHEMA: &str = "hwpx-agent.p09-150-owned-blob-root/v1";

#[derive(Clone)]
pub(super) enum ProbeBlobStore {
    Memory(InMemoryBlobStore),
    Local(LocalBinding),
}

impl fmt::Debug for ProbeBlobStore {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ProbeBlobStore(<redacted>)")
    }
}

#[derive(Clone)]
pub(super) struct LocalBinding {
    owner: OwnedRoot,
    store: Arc<Mutex<LocalEncryptedBlobStore>>,
}

#[derive(Clone)]
struct OwnedRoot {
    path: PathBuf,
    run: Uuid,
}

fn repository() -> std::result::Result<PathBuf, ArtifactError> {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .map(Path::to_path_buf)
        .ok_or(ArtifactError::StorageFailure)
}

fn private_base() -> std::result::Result<PathBuf, ArtifactError> {
    Ok(repository()?.join("target/p09-150-signed-durable/private"))
}

fn direct(path: &Path, directory: bool) -> std::result::Result<(), ArtifactError> {
    let metadata = fs::symlink_metadata(path).map_err(|_| ArtifactError::StorageFailure)?;
    if metadata.file_type().is_symlink()
        || directory && !metadata.is_dir()
        || !directory && !metadata.is_file()
    {
        return Err(ArtifactError::StorageFailure);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        if metadata.file_attributes() & 0x400 != 0 {
            return Err(ArtifactError::StorageFailure);
        }
    }
    Ok(())
}

impl OwnedRoot {
    fn verify(&self, fresh: bool) -> std::result::Result<(), ArtifactError> {
        let expected = private_base()?.join(format!("p150-{}", self.run));
        if self.run.is_nil() || !self.path.is_absolute() || self.path != expected {
            return Err(ArtifactError::StorageFailure);
        }
        let repository = repository()?;
        if std::env::current_dir().map_err(|_| ArtifactError::StorageFailure)? != repository {
            return Err(ArtifactError::StorageFailure);
        }
        for parent in self.path.ancestors() {
            direct(parent, true)?;
            if parent == repository {
                break;
            }
        }
        if fs::canonicalize(&self.path).map_err(|_| ArtifactError::StorageFailure)?
            != fs::canonicalize(&expected).map_err(|_| ArtifactError::StorageFailure)?
        {
            return Err(ArtifactError::StorageFailure);
        }
        let marker = self.path.join(OWNER_FILE);
        direct(&marker, false)?;
        let expected_owner = format!("{OWNER_SCHEMA}\n{}\n", self.run);
        let mut content = Vec::new();
        fs::File::open(marker)
            .map_err(|_| ArtifactError::StorageFailure)?
            .take(129)
            .read_to_end(&mut content)
            .map_err(|_| ArtifactError::StorageFailure)?;
        if content != expected_owner.as_bytes() {
            return Err(ArtifactError::StorageFailure);
        }
        if fresh {
            let mut entries =
                fs::read_dir(&self.path).map_err(|_| ArtifactError::StorageFailure)?;
            let only = entries
                .next()
                .ok_or(ArtifactError::StorageFailure)?
                .map_err(|_| ArtifactError::StorageFailure)?;
            if only.file_name() != OWNER_FILE || entries.next().is_some() {
                return Err(ArtifactError::StorageFailure);
            }
        }
        Ok(())
    }
}

impl ProbeBlobStore {
    // P151 controlled-negative extension: never accepts a user artifact or raw path.
    pub(super) fn tamper_negative_fixture(
        &self,
        record: &artifact_service::ArtifactRecord,
    ) -> std::result::Result<Vec<u8>, ArtifactError> {
        use artifact_service::{ArtifactKind, ContentDigest, StorageState};
        use std::io::{Read as _, Seek as _, SeekFrom, Write as _};
        let Self::Local(binding) = self else {
            return Err(ArtifactError::InvalidState);
        };
        binding.owner.verify(false)?;
        let expected_key = ObjectKey::for_artifact(
            record.tenant_id(), ArtifactKind::Receipt, StorageState::Available,
            ContentDigest::of(super::durable_negative::PAYLOAD),
        )?;
        if record.kind() != ArtifactKind::Receipt
            || record.storage_state() != StorageState::Available
            || record.content_sha256() != ContentDigest::of(super::durable_negative::PAYLOAD)
            || record.size_bytes() != super::durable_negative::PAYLOAD.len() as u64
            || record.object_key() != &expected_key
        {
            return Err(ArtifactError::InvalidState);
        }
        let path = binding.owner.path.join("output").join(expected_key.as_str());
        for parent in path.parent().ok_or(ArtifactError::StorageFailure)?.ancestors() {
            direct(parent, true)?;
            if parent == binding.owner.path { break; }
        }
        direct(&path, false)?;
        let mut options = fs::OpenOptions::new();
        options.read(true).write(true);
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt as _;
            options.share_mode(0).custom_flags(0x0020_0000); // OPEN_REPARSE_POINT, no shared writer.
        }
        let mut file = options.open(&path).map_err(|_| ArtifactError::StorageFailure)?;
        let metadata = file.metadata().map_err(|_| ArtifactError::StorageFailure)?;
        if !metadata.is_file() { return Err(ArtifactError::StorageFailure); }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 { return Err(ArtifactError::StorageFailure); }
        }
        let size = super::durable_negative::PAYLOAD.len() + 16;
        let mut ciphertext = Vec::new();
        std::io::Read::by_ref(&mut file).take((size + 1) as u64).read_to_end(&mut ciphertext)
            .map_err(|_| ArtifactError::StorageFailure)?;
        if ciphertext.len() != size
            || ContentDigest::of(&ciphertext) != record.encryption().ciphertext_sha256
        {
            return Err(ArtifactError::IntegrityMismatch);
        }
        let last = ciphertext.last_mut().ok_or(ArtifactError::StorageFailure)?;
        *last ^= 1;
        file.seek(SeekFrom::Start((size - 1) as u64)).map_err(|_| ArtifactError::StorageFailure)?;
        file.write_all(&[*last]).map_err(|_| ArtifactError::StorageFailure)?;
        file.sync_all().map_err(|_| ArtifactError::StorageFailure)?;
        drop(file);
        binding.owner.verify(false)?;
        direct(&path, false)?;
        if self.get(record.object_key())? != Some(ciphertext.clone()) {
            return Err(ArtifactError::StorageFailure);
        }
        Ok(ciphertext)
    }

    #[cfg(test)]
    pub(super) fn negative_unit_fixture() -> std::result::Result<Self, ArtifactError> {
        let base = private_base()?;
        let repository = repository()?;
        for path in base.ancestors() {
            direct(path, true)?;
            if path == repository { break; }
        }
        let run = Uuid::new_v4();
        let path = base.join(format!("p150-{run}"));
        fs::create_dir(&path).map_err(|_| ArtifactError::StorageFailure)?;
        fs::write(path.join(OWNER_FILE), format!("{OWNER_SCHEMA}\n{run}\n"))
            .map_err(|_| ArtifactError::StorageFailure)?;
        Self::select(Some(path), Some(run.to_string()))
    }
    // End P151 controlled-negative extension.

    pub(super) fn from_driver_env() -> std::result::Result<Self, ArtifactError> {
        let run = match std::env::var("P150_BLOB_RUN_ID") {
            Ok(value) => Some(value),
            Err(std::env::VarError::NotPresent) => None,
            Err(_) => return Err(ArtifactError::StorageFailure),
        };
        let mode = match std::env::var("P150_BLOB_MODE") {
            Ok(value) => Some(value),
            Err(std::env::VarError::NotPresent) => None,
            Err(_) => return Err(ArtifactError::StorageFailure),
        };
        let root = std::env::var_os("P150_BLOB_ROOT").map(PathBuf::from);
        if root.is_none() && run.is_none() && mode.is_none() {
            return Self::select(None, None);
        }
        if mode.as_deref() != Some("owned_local_v1") {
            return Err(ArtifactError::StorageFailure);
        }
        Self::select(root, run)
    }

    fn select(
        root: Option<PathBuf>,
        run: Option<String>,
    ) -> std::result::Result<Self, ArtifactError> {
        match (root, run) {
            (None, None) => Ok(Self::Memory(InMemoryBlobStore::default())),
            (Some(path), Some(run)) => {
                let id = Uuid::parse_str(&run).map_err(|_| ArtifactError::StorageFailure)?;
                if run != id.to_string() {
                    return Err(ArtifactError::StorageFailure);
                }
                let owner = OwnedRoot { path, run: id };
                owner.verify(true)?;
                let store = LocalEncryptedBlobStore::create(&owner.path, MAX_CIPHERTEXT)?;
                Ok(Self::Local(LocalBinding {
                    owner,
                    store: Arc::new(Mutex::new(store)),
                }))
            }
            _ => Err(ArtifactError::StorageFailure),
        }
    }

    pub(super) const fn is_durable(&self) -> bool {
        matches!(self, Self::Local(_))
    }

    pub(super) fn reopen(&self) -> std::result::Result<(), ArtifactError> {
        let Self::Local(binding) = self else {
            return Err(ArtifactError::InvalidState);
        };
        binding.owner.verify(false)?;
        let replacement = LocalEncryptedBlobStore::create(&binding.owner.path, MAX_CIPHERTEXT)?;
        *binding
            .store
            .lock()
            .map_err(|_| ArtifactError::StorageFailure)? = replacement;
        Ok(())
    }
}

impl EncryptedBlobStore for ProbeBlobStore {
    fn put_if_absent(
        &self,
        key: &ObjectKey,
        ciphertext: &[u8],
    ) -> std::result::Result<(), ArtifactError> {
        match self {
            Self::Memory(store) => store.put_if_absent(key, ciphertext),
            Self::Local(binding) => {
                binding.owner.verify(false)?;
                binding
                    .store
                    .lock()
                    .map_err(|_| ArtifactError::StorageFailure)?
                    .put_if_absent(key, ciphertext)
            }
        }
    }

    fn get(&self, key: &ObjectKey) -> std::result::Result<Option<Vec<u8>>, ArtifactError> {
        match self {
            Self::Memory(store) => store.get(key),
            Self::Local(binding) => {
                binding.owner.verify(false)?;
                binding
                    .store
                    .lock()
                    .map_err(|_| ArtifactError::StorageFailure)?
                    .get(key)
            }
        }
    }

    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> std::result::Result<(), ArtifactError> {
        match self {
            Self::Memory(store) => store.relocate_if_absent(source, target),
            Self::Local(binding) => {
                binding.owner.verify(false)?;
                binding
                    .store
                    .lock()
                    .map_err(|_| ArtifactError::StorageFailure)?
                    .relocate_if_absent(source, target)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use artifact_service::{ArtifactKind, ContentDigest, StorageState, TenantId};

    fn root() -> std::result::Result<OwnedRoot, Box<dyn std::error::Error>> {
        let base = private_base()?;
        // Only create new test-owned roots; retain their bounded ciphertext as evidence.
        let repository = repository()?;
        for path in base.ancestors() {
            if path.exists() {
                direct(path, true)?;
            }
            if path == repository {
                break;
            }
        }
        fs::create_dir_all(&base)?;
        let run = Uuid::new_v4();
        let path = base.join(format!("p150-{run}"));
        fs::create_dir(&path)?;
        fs::write(path.join(OWNER_FILE), format!("{OWNER_SCHEMA}\n{run}\n"))?;
        let owner = OwnedRoot { path, run };
        owner.verify(true)?;
        Ok(owner)
    }

    fn local(owner: &OwnedRoot) -> std::result::Result<ProbeBlobStore, ArtifactError> {
        ProbeBlobStore::select(Some(owner.path.clone()), Some(owner.run.to_string()))
    }

    fn key(state: StorageState) -> std::result::Result<ObjectKey, ArtifactError> {
        ObjectKey::for_artifact(
            TenantId::new(Uuid::from_u128(1))?,
            ArtifactKind::Result,
            state,
            ContentDigest::of(b"test-identity"),
        )
    }

    #[test]
    fn legacy_memory_mode_and_shared_clone_unchanged()
    -> std::result::Result<(), Box<dyn std::error::Error>> {
        let store = ProbeBlobStore::select(None, None)?;
        assert!(!store.is_durable());
        let key = key(StorageState::Available)?;
        store.put_if_absent(&key, b"bounded-test-ciphertext")?;
        assert_eq!(
            store.clone().get(&key)?,
            Some(b"bounded-test-ciphertext".to_vec())
        );
        assert!(matches!(store.reopen(), Err(ArtifactError::InvalidState)));
        Ok(())
    }

    #[test]
    fn partial_or_noncanonical_driver_selection_denied() {
        for (path, run) in [
            (Some(PathBuf::from("outside")), None),
            (None, Some(Uuid::new_v4().to_string())),
            (Some(PathBuf::from("outside")), Some("bad".into())),
            (
                Some(PathBuf::from("outside")),
                Some(Uuid::nil().to_string()),
            ),
        ] {
            assert!(matches!(
                ProbeBlobStore::select(path, run),
                Err(ArtifactError::StorageFailure)
            ));
        }
    }

    #[test]
    fn root_owner_mismatch_or_extra_initial_files_denied()
    -> std::result::Result<(), Box<dyn std::error::Error>> {
        let owner = root()?;
        fs::write(owner.path.join(OWNER_FILE), b"wrong-owner")?;
        assert!(matches!(local(&owner), Err(ArtifactError::StorageFailure)));
        let owner = root()?;
        fs::write(owner.path.join("unexpected"), b"bounded")?;
        assert!(matches!(local(&owner), Err(ArtifactError::StorageFailure)));
        Ok(())
    }

    #[test]
    fn local_publish_duplicate_reopen_and_whole_bytes()
    -> std::result::Result<(), Box<dyn std::error::Error>> {
        let owner = root()?;
        let store = local(&owner)?;
        let key = key(StorageState::Available)?;
        let cipher = b"bounded-test-ciphertext-not-AEAD-qualification";
        store.put_if_absent(&key, cipher)?;
        assert!(store.put_if_absent(&key, cipher).is_err());
        store.reopen()?;
        assert_eq!(store.clone().get(&key)?, Some(cipher.to_vec()));
        assert!(matches!(local(&owner), Err(ArtifactError::StorageFailure)));
        Ok(())
    }

    #[test]
    fn local_quarantine_relocation_retains_whole_bytes()
    -> std::result::Result<(), Box<dyn std::error::Error>> {
        let owner = root()?;
        let store = local(&owner)?;
        let available = key(StorageState::Available)?;
        let quarantined = key(StorageState::Quarantined)?;
        store.put_if_absent(&available, b"bounded-test-ciphertext")?;
        store.relocate_if_absent(&available, &quarantined)?;
        store.reopen()?;
        assert!(store.get(&available)?.is_none());
        assert_eq!(
            store.get(&quarantined)?,
            Some(b"bounded-test-ciphertext".to_vec())
        );
        Ok(())
    }

    #[test]
    fn owner_change_denies_reopen_and_reads() -> std::result::Result<(), Box<dyn std::error::Error>>
    {
        let owner = root()?;
        let store = local(&owner)?;
        let key = key(StorageState::Available)?;
        store.put_if_absent(&key, b"bounded-test-ciphertext")?;
        fs::write(owner.path.join(OWNER_FILE), b"wrong-owner")?;
        assert!(matches!(store.reopen(), Err(ArtifactError::StorageFailure)));
        assert!(matches!(
            store.get(&key),
            Err(ArtifactError::StorageFailure)
        ));
        Ok(())
    }

    #[test]
    fn local_ciphertext_bound_retained() -> std::result::Result<(), Box<dyn std::error::Error>> {
        let owner = root()?;
        let store = local(&owner)?;
        let key = key(StorageState::Available)?;
        let oversized = vec![0; usize::try_from(MAX_CIPHERTEXT)? + 1];
        assert!(matches!(
            store.put_if_absent(&key, &oversized),
            Err(ArtifactError::PayloadTooLarge { .. })
        ));
        assert!(store.get(&key)?.is_none());
        Ok(())
    }

    #[test]
    fn debug_never_discloses_owned_path() -> std::result::Result<(), Box<dyn std::error::Error>> {
        let owner = root()?;
        let store = local(&owner)?;
        assert_eq!(format!("{store:?}"), "ProbeBlobStore(<redacted>)");
        Ok(())
    }
}
