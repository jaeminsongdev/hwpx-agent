use std::collections::BTreeSet;

use unicode_casefold::UnicodeCaseFold as _;
use unicode_normalization::UnicodeNormalization as _;

use crate::{PackageError, PackageLimits};

/// A validated package-relative path. The original UTF-8 spelling is retained;
/// collision checks use NFC plus Unicode case folding.
#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct PackagePath {
    original: String,
    collision_key: String,
    directory: bool,
}

impl PackagePath {
    pub(crate) fn parse(
        raw: &[u8],
        entry_index: usize,
        limits: PackageLimits,
    ) -> Result<Self, PackageError> {
        let config = limits.config();
        if raw.is_empty() || raw.len() > config.max_name_bytes {
            return Err(PackageError::InvalidNameLength {
                entry_index,
                actual: raw.len(),
                limit: config.max_name_bytes,
            });
        }
        let name =
            std::str::from_utf8(raw).map_err(|_| PackageError::NameNotUtf8 { entry_index })?;
        if name.chars().any(char::is_control) {
            return Err(PackageError::NameControlCharacter { entry_index });
        }
        if name.contains('\\') {
            return Err(PackageError::NameBackslash { entry_index });
        }
        if name.starts_with('/') || name.starts_with("//") {
            return Err(PackageError::NameAbsolute { entry_index });
        }

        let directory = name.ends_with('/');
        let body = name.strip_suffix('/').unwrap_or(name);
        if body.is_empty() {
            return Err(PackageError::NameEmptyComponent { entry_index });
        }
        let segments = body.split('/').collect::<Vec<_>>();
        if segments.len() > config.max_path_depth {
            return Err(PackageError::PathTooDeep {
                entry_index,
                actual: segments.len(),
                limit: config.max_path_depth,
            });
        }
        for segment in &segments {
            validate_segment(segment, entry_index)?;
        }

        let normalized = body.nfc().collect::<String>();
        let folded = normalized.case_fold().collect::<String>();
        let collision_key = folded.nfc().collect::<String>();
        Ok(Self {
            original: name.to_owned(),
            collision_key,
            directory,
        })
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.original
    }

    #[must_use]
    pub fn is_directory(&self) -> bool {
        self.directory
    }

    pub(crate) fn collision_key(&self) -> &str {
        &self.collision_key
    }
}

fn validate_segment(segment: &str, entry_index: usize) -> Result<(), PackageError> {
    if segment.is_empty() {
        return Err(PackageError::NameEmptyComponent { entry_index });
    }
    if segment == "." || segment == ".." {
        return Err(PackageError::NameTraversal { entry_index });
    }
    if segment.ends_with('.') || segment.ends_with(' ') {
        return Err(PackageError::NameAmbiguousSuffix { entry_index });
    }
    if segment.contains(':') {
        return Err(PackageError::NameDriveOrStream { entry_index });
    }
    let base = segment.split('.').next().unwrap_or_default();
    let uppercase = base.to_ascii_uppercase();
    let fixed = ["CON", "PRN", "AUX", "NUL", "CLOCK$"];
    let numbered = uppercase
        .strip_prefix("COM")
        .or_else(|| uppercase.strip_prefix("LPT"))
        .is_some_and(|suffix| {
            matches!(suffix, "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9")
        });
    if fixed.contains(&uppercase.as_str()) || numbered {
        return Err(PackageError::NameReserved { entry_index });
    }
    Ok(())
}

pub(crate) fn insert_unique_path(
    keys: &mut BTreeSet<String>,
    path: &PackagePath,
    entry_index: usize,
) -> Result<(), PackageError> {
    if !keys.insert(path.collision_key().to_owned()) {
        return Err(PackageError::NameCollision { entry_index });
    }
    Ok(())
}
