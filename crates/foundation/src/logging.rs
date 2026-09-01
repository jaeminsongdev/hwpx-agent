use std::collections::BTreeMap;

use regex::Regex;
use serde::Serialize;
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use thiserror::Error;
use uuid::Uuid;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ValidationState {
    Passed,
    Failed,
    Unverified,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
enum SafeFieldValue {
    ArtifactSha256(String),
    LogicalNodeId(String),
    SchemaPath(String),
    ValidationState(ValidationState),
    Count(u64),
    DurationMs(u64),
}

/// 생성자를 통과한 allowlisted scalar만 보유한다.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SafeField(SafeFieldValue);

impl SafeField {
    /// lowercase SHA-256 hex field를 만든다.
    ///
    /// # Errors
    ///
    /// 값이 정확한 64자리 lowercase hex가 아니면 실패한다.
    pub fn artifact_sha256(value: impl Into<String>) -> Result<Self, SafeLogError> {
        let value = value.into();
        if value.len() != 64
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(SafeLogError::InvalidSafeField);
        }
        Ok(Self(SafeFieldValue::ArtifactSha256(value)))
    }

    /// 문서 본문이나 PII로 오인될 수 없는 bounded logical node ID를 만든다.
    ///
    /// # Errors
    ///
    /// 값이 비었거나 128자를 넘거나 allowlist 밖 문자를 포함하면 실패한다.
    pub fn logical_node_id(value: impl Into<String>) -> Result<Self, SafeLogError> {
        let value = value.into();
        if !is_bounded_identifier(&value, 128, b"._-:/#") {
            return Err(SafeLogError::InvalidSafeField);
        }
        Ok(Self(SafeFieldValue::LogicalNodeId(value)))
    }

    /// JSON Pointer 또는 schema fragment 경로를 만든다.
    ///
    /// # Errors
    ///
    /// 경로가 `/` 또는 `#/`로 시작하지 않거나 allowlist 밖 문자를 포함하면 실패한다.
    pub fn schema_path(value: impl Into<String>) -> Result<Self, SafeLogError> {
        let value = value.into();
        if !(value.starts_with('/') || value.starts_with("#/"))
            || !is_bounded_identifier(&value, 256, b"._-:/#~")
        {
            return Err(SafeLogError::InvalidSafeField);
        }
        Ok(Self(SafeFieldValue::SchemaPath(value)))
    }

    #[must_use]
    pub fn validation_state(value: ValidationState) -> Self {
        Self(SafeFieldValue::ValidationState(value))
    }

    #[must_use]
    pub fn count(value: u64) -> Self {
        Self(SafeFieldValue::Count(value))
    }

    #[must_use]
    pub fn duration_ms(value: u64) -> Self {
        Self(SafeFieldValue::DurationMs(value))
    }
}

/// 본문과 임의 parameter value를 구조적으로 수용하지 않는 allowlist event다.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SafeEvent {
    event: String,
    request_id: Uuid,
    job_id: Option<Uuid>,
    trace_id: Uuid,
    fields: BTreeMap<String, SafeField>,
}

impl SafeEvent {
    /// 식별자 hierarchy가 있는 빈 safe event를 만든다.
    ///
    /// # Errors
    ///
    /// event 이름이 lowercase dotted identifier 규칙을 위반하면 실패한다.
    pub fn new(
        event: impl Into<String>,
        request_id: Uuid,
        job_id: Option<Uuid>,
        trace_id: Uuid,
    ) -> Result<Self, SafeLogError> {
        let event = event.into();
        if !is_event_name(&event) {
            return Err(SafeLogError::InvalidEventName);
        }
        Ok(Self {
            event,
            request_id,
            job_id,
            trace_id,
            fields: BTreeMap::new(),
        })
    }

    /// allowlisted field를 이름 중복 없이 추가한다.
    ///
    /// # Errors
    ///
    /// field 이름이 안전하지 않거나 이미 존재하면 실패한다.
    pub fn insert_field(
        &mut self,
        name: impl Into<String>,
        field: SafeField,
    ) -> Result<(), SafeLogError> {
        let name = name.into();
        if !is_bounded_identifier(&name, 64, b"._-") {
            return Err(SafeLogError::InvalidFieldName);
        }
        if self.fields.insert(name, field).is_some() {
            return Err(SafeLogError::DuplicateField);
        }
        Ok(())
    }

    /// 이벤트를 한 줄 JSON으로 직렬화한다.
    ///
    /// # Errors
    ///
    /// 직렬화가 실패하면 [`SafeLogError::Serialization`]을 반환한다.
    pub fn to_json_line(&self) -> Result<String, SafeLogError> {
        serde_json::to_string(self)
            .map(|line| format!("{line}\n"))
            .map_err(SafeLogError::Serialization)
    }
}

#[derive(Debug, Error)]
pub enum SafeLogError {
    #[error("event name is not an allowlisted identifier")]
    InvalidEventName,
    #[error("field name is not an allowlisted identifier")]
    InvalidFieldName,
    #[error("field value violates its safe scalar contract")]
    InvalidSafeField,
    #[error("field name already exists")]
    DuplicateField,
    #[error("safe event serialization failed: {0}")]
    Serialization(serde_json::Error),
}

fn is_event_name(value: &str) -> bool {
    value.len() >= 3
        && value.len() <= 128
        && value.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || b"._-".contains(&byte)
        })
        && value.contains('.')
}

fn is_bounded_identifier(value: &str, maximum: usize, extra: &[u8]) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || extra.contains(&byte))
}

/// 신뢰하지 않는 진단 payload를 기록해야 할 때 key와 값 패턴을 함께 제거한다.
#[must_use]
pub fn redact_untrusted(value: &Value) -> Value {
    match value {
        Value::Object(object) => Value::Object(redact_object(object)),
        Value::Array(items) => Value::Array(items.iter().map(redact_untrusted).collect()),
        Value::String(text) => Value::String(redact_string(text)),
        other => other.clone(),
    }
}

fn redact_object(object: &Map<String, Value>) -> Map<String, Value> {
    object
        .iter()
        .map(|(key, value)| {
            let sanitized = if is_sensitive_key(key) {
                redaction_receipt(value)
            } else {
                redact_untrusted(value)
            };
            (key.clone(), sanitized)
        })
        .collect()
}

fn is_sensitive_key(key: &str) -> bool {
    let normalized = key.to_ascii_lowercase().replace(['-', '.'], "_");
    [
        "password",
        "passphrase",
        "token",
        "access_token",
        "authorization",
        "api_key",
        "secret",
        "certificate",
        "signed_url",
        "document_body",
        "body",
        "content",
        "pii",
        "email",
        "phone",
    ]
    .iter()
    .any(|sensitive| normalized == *sensitive || normalized.ends_with(&format!("_{sensitive}")))
}

fn redaction_receipt(value: &Value) -> Value {
    let bytes = serde_json::to_vec(value).unwrap_or_default();
    json!({
        "redacted": true,
        "sha256": hex::encode(Sha256::digest(bytes)),
    })
}

fn redact_string(text: &str) -> String {
    let patterns = [
        r"(?i)bearer\s+[a-z0-9._~+/=-]+",
        r"(?i)([?&](?:token|signature|sig|x-amz-signature|x-goog-signature)=)[^&\s]+",
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        r"\b01[016789][ -]?\d{3,4}[ -]?\d{4}\b",
        r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{12,}\b",
    ];
    patterns.iter().fold(text.to_owned(), |current, pattern| {
        Regex::new(pattern)
            .map(|regex| regex.replace_all(&current, "[REDACTED]").into_owned())
            .unwrap_or(current)
    })
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use uuid::Uuid;

    use super::{SafeEvent, SafeField, ValidationState, redact_untrusted};

    #[test]
    fn event_shape_has_only_allowlisted_fields() {
        let mut event = SafeEvent::new("validation.completed", Uuid::nil(), None, Uuid::nil())
            .unwrap_or_else(|error| panic!("event: {error}"));
        let artifact = SafeField::artifact_sha256("a".repeat(64))
            .unwrap_or_else(|error| panic!("artifact: {error}"));
        event
            .insert_field("artifact", artifact)
            .unwrap_or_else(|error| panic!("insert: {error}"));
        event
            .insert_field(
                "state",
                SafeField::validation_state(ValidationState::Unverified),
            )
            .unwrap_or_else(|error| panic!("insert: {error}"));
        let line = event
            .to_json_line()
            .unwrap_or_else(|error| panic!("serialize: {error}"));
        assert!(line.ends_with('\n'));
        assert!(!line.contains("document_body"));
    }

    #[test]
    fn rejects_unstructured_or_pii_like_safe_fields() {
        assert!(SafeEvent::new("document body", Uuid::nil(), None, Uuid::nil()).is_err());
        assert!(SafeField::artifact_sha256("not-a-checksum").is_err());
        assert!(SafeField::logical_node_id("user@example.com").is_err());
        assert!(SafeField::schema_path("private body").is_err());
    }

    #[test]
    fn redacts_keyed_and_inline_secrets_and_pii() {
        let original = json!({
            "password": "correct horse battery staple",
            "nested": {
                "document_body": "private body",
                "note": "Bearer secret-token and user@example.com and 010-1234-5678",
                "url": "https://example.invalid/a?x=1&signature=abc123"
            }
        });
        let redacted = redact_untrusted(&original).to_string();
        for forbidden in [
            "correct horse",
            "private body",
            "secret-token",
            "user@example.com",
            "010-1234-5678",
            "abc123",
        ] {
            assert!(!redacted.contains(forbidden));
        }
        assert!(redacted.contains("redacted"));
        assert!(redacted.contains("[REDACTED]"));
    }
}
