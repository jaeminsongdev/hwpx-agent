use std::fmt;
use std::mem;
use std::str;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const TABLE_TEXT_CONVERSION_SCHEMA_VERSION: &str = "hwpx-agent.table-text-conversion/v1";
pub const TABLE_TEXT_TO_TABLE_CAPABILITY_ID: &str = "table.text_to_table";
pub const TABLE_TABLE_TO_TEXT_CAPABILITY_ID: &str = "table.table_to_text";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableTextConversionLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub rows: usize,
    pub columns: usize,
    pub cells: usize,
    pub cell_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableTextConversionLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            rows: 10_000,
            columns: 1_024,
            cells: 1_000_000,
            cell_bytes: 1024 * 1024,
            serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableTextConversionLimits(TableTextConversionLimitConfig);

impl TableTextConversionLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_CELL_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for table/text conversion.
    ///
    /// # Errors
    ///
    /// Returns [`TableTextConversionError::InvalidLimit`] when a limit is zero or exceeds its hard
    /// ceiling.
    pub fn new(config: TableTextConversionLimitConfig) -> Result<Self, TableTextConversionError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.cell_bytes == 0
            || config.cell_bytes > Self::HARD_MAX_CELL_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TableTextConversionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableTextConversionLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableDelimiter {
    Tab,
    Comma,
    Semicolon,
}

impl TableDelimiter {
    const fn character(self) -> char {
        match self {
            Self::Tab => '\t',
            Self::Comma => ',',
            Self::Semicolon => ';',
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableLineEnding {
    Lf,
    CrLf,
}

impl TableLineEnding {
    const fn bytes(self) -> &'static [u8] {
        match self {
            Self::Lf => b"\n",
            Self::CrLf => b"\r\n",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTextGridDraft {
    pub schema_version: String,
    pub rows: Vec<Vec<String>>,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTextGrid {
    schema_version: &'static str,
    rows: Vec<Vec<String>>,
    #[serde(skip)]
    columns: usize,
}

impl TableTextGrid {
    /// Validates a finite rectangular table of semantic cell text.
    ///
    /// # Errors
    ///
    /// Rejects schema drift, empty or ragged grids, over-limit dimensions/content, NUL and carriage
    /// returns. Semantic line breaks inside cells use LF.
    pub fn from_draft(
        draft: TableTextGridDraft,
        limits: TableTextConversionLimits,
    ) -> Result<Self, TableTextConversionError> {
        if draft.schema_version != TABLE_TEXT_CONVERSION_SCHEMA_VERSION {
            return Err(TableTextConversionError::UnsupportedVersion);
        }
        Self::from_rows(draft.rows, limits)
    }

    /// Parses strict bounded JSON into a validated text grid.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate-key or unknown-field JSON and all invalid grids.
    pub fn from_json(
        bytes: &[u8],
        limits: TableTextConversionLimits,
    ) -> Result<Self, TableTextConversionError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableTextConversionError::InputLimit);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableTextConversionError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    /// Parses bounded UTF-8 delimited text with RFC-4180-style double-quote escaping.
    ///
    /// LF and CRLF record endings are accepted and normalized to LF inside quoted cells. Bare CR,
    /// quotes inside unquoted fields, trailing bytes after a closing quote, unterminated quotes and
    /// ragged records fail closed.
    ///
    /// # Errors
    ///
    /// Returns a typed error for encoding, syntax, dimension, allocation or configured-limit
    /// failures.
    pub fn parse_delimited(
        bytes: &[u8],
        delimiter: TableDelimiter,
        limits: TableTextConversionLimits,
    ) -> Result<Self, TableTextConversionError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableTextConversionError::InputLimit);
        }
        let input = str::from_utf8(bytes).map_err(|_| TableTextConversionError::InvalidUtf8)?;
        let mut rows = fallible_vec(0)?;
        let mut row = fallible_vec(0)?;
        let mut field = String::new();
        let mut total_cells = 0usize;
        let mut state = ParseState::Start;
        let mut ended_record = false;
        let mut characters = input.chars().peekable();

        while let Some(character) = characters.next() {
            let is_record_end = match character {
                '\n' => true,
                '\r' => {
                    if characters.next() != Some('\n') {
                        return Err(TableTextConversionError::InvalidLineEnding);
                    }
                    true
                }
                _ => false,
            };

            match state {
                ParseState::Start => {
                    if is_record_end {
                        finish_field(&mut row, &mut field, limits)?;
                        finish_row(&mut rows, &mut row, &mut total_cells, limits)?;
                        ended_record = true;
                    } else if character == delimiter.character() {
                        finish_field(&mut row, &mut field, limits)?;
                        ended_record = false;
                    } else if character == '"' {
                        state = ParseState::Quoted;
                        ended_record = false;
                    } else {
                        push_character(&mut field, character, limits)?;
                        state = ParseState::Unquoted;
                        ended_record = false;
                    }
                }
                ParseState::Unquoted => {
                    if is_record_end {
                        finish_field(&mut row, &mut field, limits)?;
                        finish_row(&mut rows, &mut row, &mut total_cells, limits)?;
                        state = ParseState::Start;
                        ended_record = true;
                    } else if character == delimiter.character() {
                        finish_field(&mut row, &mut field, limits)?;
                        state = ParseState::Start;
                        ended_record = false;
                    } else if character == '"' {
                        return Err(TableTextConversionError::InvalidQuotedField);
                    } else {
                        push_character(&mut field, character, limits)?;
                        ended_record = false;
                    }
                }
                ParseState::Quoted => {
                    if character == '"' {
                        state = ParseState::AfterQuote;
                    } else if is_record_end {
                        push_character(&mut field, '\n', limits)?;
                    } else {
                        push_character(&mut field, character, limits)?;
                    }
                    ended_record = false;
                }
                ParseState::AfterQuote => {
                    if character == '"' && !is_record_end {
                        push_character(&mut field, '"', limits)?;
                        state = ParseState::Quoted;
                        ended_record = false;
                    } else if is_record_end {
                        finish_field(&mut row, &mut field, limits)?;
                        finish_row(&mut rows, &mut row, &mut total_cells, limits)?;
                        state = ParseState::Start;
                        ended_record = true;
                    } else if character == delimiter.character() {
                        finish_field(&mut row, &mut field, limits)?;
                        state = ParseState::Start;
                        ended_record = false;
                    } else {
                        return Err(TableTextConversionError::InvalidQuotedField);
                    }
                }
            }
        }

        if state == ParseState::Quoted {
            return Err(TableTextConversionError::InvalidQuotedField);
        }
        if !ended_record {
            finish_field(&mut row, &mut field, limits)?;
            finish_row(&mut rows, &mut row, &mut total_cells, limits)?;
        }
        Self::from_rows(rows, limits)
    }

    /// Serializes the semantic grid to bounded deterministic delimited UTF-8.
    ///
    /// Fields containing the delimiter, a quote or LF are quoted; quotes are doubled. The selected
    /// line ending is used both between records and for semantic LF inside quoted fields. No final
    /// record ending is emitted.
    ///
    /// # Errors
    ///
    /// Returns an allocation or output-limit error without a partial result.
    pub fn to_delimited(
        &self,
        delimiter: TableDelimiter,
        line_ending: TableLineEnding,
        limits: TableTextConversionLimits,
    ) -> Result<Vec<u8>, TableTextConversionError> {
        let mut output = fallible_vec(0)?;
        for (row_index, row) in self.rows.iter().enumerate() {
            if row_index > 0 {
                append_output(&mut output, line_ending.bytes(), limits)?;
            }
            for (column_index, field) in row.iter().enumerate() {
                if column_index > 0 {
                    let mut encoded = [0u8; 4];
                    append_output(
                        &mut output,
                        delimiter.character().encode_utf8(&mut encoded).as_bytes(),
                        limits,
                    )?;
                }
                let quoted = field.contains(delimiter.character())
                    || field.contains('"')
                    || field.contains('\n');
                if quoted {
                    append_output(&mut output, b"\"", limits)?;
                }
                for character in field.chars() {
                    match character {
                        '"' => append_output(&mut output, b"\"\"", limits)?,
                        '\n' => append_output(&mut output, line_ending.bytes(), limits)?,
                        _ => {
                            let mut encoded = [0u8; 4];
                            append_output(
                                &mut output,
                                character.encode_utf8(&mut encoded).as_bytes(),
                                limits,
                            )?;
                        }
                    }
                }
                if quoted {
                    append_output(&mut output, b"\"", limits)?;
                }
            }
        }
        Ok(output)
    }

    #[must_use]
    pub fn rows(&self) -> &[Vec<String>] {
        &self.rows
    }

    #[must_use]
    pub fn row_count(&self) -> usize {
        self.rows.len()
    }

    #[must_use]
    pub const fn column_count(&self) -> usize {
        self.columns
    }

    #[must_use]
    pub fn cell(&self, row: usize, column: usize) -> Option<&str> {
        self.rows.get(row)?.get(column).map(String::as_str)
    }

    /// Serializes the validated grid to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or exceeds the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableTextConversionLimits,
    ) -> Result<Vec<u8>, TableTextConversionError> {
        let bytes =
            serde_json::to_vec(self).map_err(|_| TableTextConversionError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(TableTextConversionError::OutputLimit);
        }
        Ok(bytes)
    }

    /// Returns SHA-256 over canonical grid JSON.
    ///
    /// # Errors
    ///
    /// Propagates bounded canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableTextConversionLimits,
    ) -> Result<[u8; 32], TableTextConversionError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn from_rows(
        rows: Vec<Vec<String>>,
        limits: TableTextConversionLimits,
    ) -> Result<Self, TableTextConversionError> {
        if rows.is_empty() {
            return Err(TableTextConversionError::EmptyGrid);
        }
        if rows.len() > limits.0.rows {
            return Err(TableTextConversionError::RowLimit);
        }
        let columns = rows[0].len();
        if columns == 0 {
            return Err(TableTextConversionError::EmptyGrid);
        }
        if columns > limits.0.columns {
            return Err(TableTextConversionError::ColumnLimit);
        }
        let cell_count = rows
            .len()
            .checked_mul(columns)
            .ok_or(TableTextConversionError::CellLimit)?;
        if cell_count > limits.0.cells {
            return Err(TableTextConversionError::CellLimit);
        }
        for row in &rows {
            if row.len() != columns {
                return Err(TableTextConversionError::RaggedRows);
            }
            for cell in row {
                if cell.len() > limits.0.cell_bytes {
                    return Err(TableTextConversionError::CellBytes);
                }
                if cell.contains('\0') || cell.contains('\r') {
                    return Err(TableTextConversionError::InvalidControl);
                }
            }
        }
        let grid = Self {
            schema_version: TABLE_TEXT_CONVERSION_SCHEMA_VERSION,
            rows,
            columns,
        };
        let _ = grid.canonical_json(limits)?;
        Ok(grid)
    }
}

impl fmt::Debug for TableTextGrid {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextGrid")
            .field("schema_version", &self.schema_version)
            .field("rows", &self.rows.len())
            .field("columns", &self.columns)
            .field("cells", &self.rows.len().saturating_mul(self.columns))
            .field("content", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableTextConversionError {
    #[error("table text conversion limit is invalid")]
    InvalidLimit,
    #[error("table text conversion input is empty or oversized")]
    InputLimit,
    #[error("table text conversion input is not valid UTF-8")]
    InvalidUtf8,
    #[error("table text conversion JSON is invalid")]
    InvalidJson,
    #[error("table text conversion schema version is unsupported")]
    UnsupportedVersion,
    #[error("table text conversion grid is empty")]
    EmptyGrid,
    #[error("table text conversion row limit exceeded")]
    RowLimit,
    #[error("table text conversion column limit exceeded")]
    ColumnLimit,
    #[error("table text conversion cell limit exceeded")]
    CellLimit,
    #[error("table text conversion cell byte limit exceeded")]
    CellBytes,
    #[error("table text conversion rows are ragged")]
    RaggedRows,
    #[error("table text conversion contains a forbidden control")]
    InvalidControl,
    #[error("table text conversion contains a bare carriage return")]
    InvalidLineEnding,
    #[error("table text conversion quoted field is malformed")]
    InvalidQuotedField,
    #[error("table text conversion output limit exceeded")]
    OutputLimit,
    #[error("table text conversion allocation failed")]
    AllocationFailed,
    #[error("table text conversion serialization failed")]
    Serialization,
}

impl TableTextConversionError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_text_conversion_invalid_limit",
            Self::InputLimit => "table_text_conversion_input_limit",
            Self::InvalidUtf8 => "table_text_conversion_invalid_utf8",
            Self::InvalidJson => "table_text_conversion_invalid_json",
            Self::UnsupportedVersion => "table_text_conversion_unsupported_version",
            Self::EmptyGrid => "table_text_conversion_empty_grid",
            Self::RowLimit => "table_text_conversion_row_limit",
            Self::ColumnLimit => "table_text_conversion_column_limit",
            Self::CellLimit => "table_text_conversion_cell_limit",
            Self::CellBytes => "table_text_conversion_cell_bytes",
            Self::RaggedRows => "table_text_conversion_ragged_rows",
            Self::InvalidControl => "table_text_conversion_invalid_control",
            Self::InvalidLineEnding => "table_text_conversion_invalid_line_ending",
            Self::InvalidQuotedField => "table_text_conversion_invalid_quoted_field",
            Self::OutputLimit => "table_text_conversion_output_limit",
            Self::AllocationFailed => "table_text_conversion_allocation_failed",
            Self::Serialization => "table_text_conversion_serialization",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ParseState {
    Start,
    Unquoted,
    Quoted,
    AfterQuote,
}

fn finish_field(
    row: &mut Vec<String>,
    field: &mut String,
    limits: TableTextConversionLimits,
) -> Result<(), TableTextConversionError> {
    if row.len() >= limits.0.columns {
        return Err(TableTextConversionError::ColumnLimit);
    }
    row.try_reserve(1)
        .map_err(|_| TableTextConversionError::AllocationFailed)?;
    row.push(mem::take(field));
    Ok(())
}

fn finish_row(
    rows: &mut Vec<Vec<String>>,
    row: &mut Vec<String>,
    total_cells: &mut usize,
    limits: TableTextConversionLimits,
) -> Result<(), TableTextConversionError> {
    if rows.len() >= limits.0.rows {
        return Err(TableTextConversionError::RowLimit);
    }
    let total = total_cells
        .checked_add(row.len())
        .ok_or(TableTextConversionError::CellLimit)?;
    if total > limits.0.cells {
        return Err(TableTextConversionError::CellLimit);
    }
    rows.try_reserve(1)
        .map_err(|_| TableTextConversionError::AllocationFailed)?;
    rows.push(mem::take(row));
    *total_cells = total;
    Ok(())
}

fn push_character(
    field: &mut String,
    character: char,
    limits: TableTextConversionLimits,
) -> Result<(), TableTextConversionError> {
    if character == '\0' {
        return Err(TableTextConversionError::InvalidControl);
    }
    let next = field
        .len()
        .checked_add(character.len_utf8())
        .ok_or(TableTextConversionError::CellBytes)?;
    if next > limits.0.cell_bytes {
        return Err(TableTextConversionError::CellBytes);
    }
    field
        .try_reserve(character.len_utf8())
        .map_err(|_| TableTextConversionError::AllocationFailed)?;
    field.push(character);
    Ok(())
}

fn append_output(
    output: &mut Vec<u8>,
    bytes: &[u8],
    limits: TableTextConversionLimits,
) -> Result<(), TableTextConversionError> {
    let next = output
        .len()
        .checked_add(bytes.len())
        .ok_or(TableTextConversionError::OutputLimit)?;
    if next > limits.0.output_bytes {
        return Err(TableTextConversionError::OutputLimit);
    }
    output
        .try_reserve(bytes.len())
        .map_err(|_| TableTextConversionError::AllocationFailed)?;
    output.extend_from_slice(bytes);
    Ok(())
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TableTextConversionError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableTextConversionError::AllocationFailed)?;
    Ok(values)
}
