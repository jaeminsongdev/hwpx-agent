#![forbid(unsafe_code)]

use std::fmt;

/// XML, ZIP, COM, MCP 또는 저장소 구현을 알지 못하는 순수 문서 식별자다.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct DocumentId(String);

impl DocumentId {
    /// 비어 있지 않고 제어 문자가 없는 식별자만 허용한다.
    ///
    /// # Errors
    ///
    /// 값이 비어 있거나 제어 문자를 포함하면 [`InvalidDocumentId`]를 반환한다.
    pub fn parse(value: impl Into<String>) -> Result<Self, InvalidDocumentId> {
        let value = value.into();
        if value.is_empty() || value.chars().any(char::is_control) {
            return Err(InvalidDocumentId);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InvalidDocumentId;

impl fmt::Display for InvalidDocumentId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("document id must be non-empty and contain no control characters")
    }
}

impl std::error::Error for InvalidDocumentId {}

#[cfg(test)]
mod tests {
    use super::DocumentId;

    #[test]
    fn rejects_empty_and_control_characters() {
        assert!(DocumentId::parse("").is_err());
        assert!(DocumentId::parse("doc\n1").is_err());
        assert_eq!(
            DocumentId::parse("doc-1").map(|id| id.as_str().to_owned()),
            Ok("doc-1".to_owned())
        );
    }
}
