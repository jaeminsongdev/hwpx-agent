#![forbid(unsafe_code)]

mod latex;

pub use latex::{
    LATEX_ADAPTER_SCHEMA_VERSION, LATEX_PARSER_VERSION, LatexAdapter, LatexAdapterError,
    LatexAdapterLimitConfig, LatexAdapterLimits, LatexAmbiguity, LatexAmbiguityKind,
    LatexCandidate, LatexCandidateChoice, LatexMacroDefinition, LatexParseOutcome,
    LatexParseRequestDraft, LatexParseResult,
};
