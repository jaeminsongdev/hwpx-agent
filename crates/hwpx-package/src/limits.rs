use crate::PackageError;

/// Caller-supplied finite limits. Values above the hard product ceilings are
/// rejected rather than silently clamped.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PackageLimitConfig {
    pub max_archive_bytes: u64,
    pub max_entries: usize,
    pub max_name_bytes: usize,
    pub max_path_depth: usize,
    pub max_extra_field_bytes: usize,
    pub max_comment_bytes: usize,
    pub max_entry_expanded_bytes: u64,
    pub max_total_expanded_bytes: u64,
    pub max_compression_ratio: u64,
}

impl Default for PackageLimitConfig {
    fn default() -> Self {
        Self {
            max_archive_bytes: 512 * 1024 * 1024,
            max_entries: 4_096,
            max_name_bytes: 1_024,
            max_path_depth: 64,
            max_extra_field_bytes: 16 * 1024,
            max_comment_bytes: 4 * 1024,
            max_entry_expanded_bytes: 128 * 1024 * 1024,
            max_total_expanded_bytes: 1024 * 1024 * 1024,
            max_compression_ratio: 200,
        }
    }
}

/// Validated package limits. Construction always enforces finite non-zero
/// values and immutable product ceilings.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PackageLimits(PackageLimitConfig);

impl PackageLimits {
    pub const HARD_MAX_ARCHIVE_BYTES: u64 = 2 * 1024 * 1024 * 1024;
    pub const HARD_MAX_ENTRIES: usize = 16_384;
    pub const HARD_MAX_NAME_BYTES: usize = 4_096;
    pub const HARD_MAX_PATH_DEPTH: usize = 256;
    pub const HARD_MAX_EXTRA_FIELD_BYTES: usize = 65_535;
    pub const HARD_MAX_COMMENT_BYTES: usize = 65_535;
    pub const HARD_MAX_ENTRY_EXPANDED_BYTES: u64 = 512 * 1024 * 1024;
    pub const HARD_MAX_TOTAL_EXPANDED_BYTES: u64 = 4 * 1024 * 1024 * 1024;
    pub const HARD_MAX_COMPRESSION_RATIO: u64 = 1_000;

    /// Validates a finite configuration against immutable product ceilings.
    ///
    /// # Errors
    ///
    /// Returns [`PackageError::InvalidLimit`] for zero or over-ceiling values,
    /// and [`PackageError::InvalidLimitRelation`] for contradictory totals.
    pub fn new(config: PackageLimitConfig) -> Result<Self, PackageError> {
        let values = [
            (
                "max_archive_bytes",
                config.max_archive_bytes,
                Self::HARD_MAX_ARCHIVE_BYTES,
            ),
            (
                "max_entries",
                config.max_entries as u64,
                Self::HARD_MAX_ENTRIES as u64,
            ),
            (
                "max_name_bytes",
                config.max_name_bytes as u64,
                Self::HARD_MAX_NAME_BYTES as u64,
            ),
            (
                "max_path_depth",
                config.max_path_depth as u64,
                Self::HARD_MAX_PATH_DEPTH as u64,
            ),
            (
                "max_extra_field_bytes",
                config.max_extra_field_bytes as u64,
                Self::HARD_MAX_EXTRA_FIELD_BYTES as u64,
            ),
            (
                "max_comment_bytes",
                config.max_comment_bytes as u64,
                Self::HARD_MAX_COMMENT_BYTES as u64,
            ),
            (
                "max_entry_expanded_bytes",
                config.max_entry_expanded_bytes,
                Self::HARD_MAX_ENTRY_EXPANDED_BYTES,
            ),
            (
                "max_total_expanded_bytes",
                config.max_total_expanded_bytes,
                Self::HARD_MAX_TOTAL_EXPANDED_BYTES,
            ),
            (
                "max_compression_ratio",
                config.max_compression_ratio,
                Self::HARD_MAX_COMPRESSION_RATIO,
            ),
        ];
        for (field, value, ceiling) in values {
            if value == 0 || value > ceiling {
                return Err(PackageError::InvalidLimit {
                    field,
                    value,
                    ceiling,
                });
            }
        }
        if config.max_entry_expanded_bytes > config.max_total_expanded_bytes {
            return Err(PackageError::InvalidLimitRelation);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> PackageLimitConfig {
        self.0
    }
}
