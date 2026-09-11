#![forbid(unsafe_code)]

mod automation;
mod corpus;
mod eqedit;
mod latex;
mod layout;
mod mathml;

pub use automation::{
    EQUATION_AUTOMATION_PROFILE_VERSION, EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION,
    EQUATION_AUTOMATION_SCHEMA_VERSION, EquationAutomationError, EquationAutomationLimitConfig,
    EquationAutomationLimits, EquationAutomationOperationDraft, EquationAutomationPlan,
    EquationAutomationPlanner, EquationAutomationReceiptDraft, EquationAutomationReceiptState,
    EquationAutomationSelection, EquationAutomationSourceState, EquationAutomationTarget,
};
pub use corpus::{
    EQUATION_CORPUS_PROFILE_VERSION, EQUATION_CORPUS_RECEIPT_SCHEMA_VERSION,
    EQUATION_CORPUS_SCHEMA_VERSION, EquationCorpusError, EquationCorpusLimitConfig,
    EquationCorpusLimits, EquationCorpusReceipt, EquationCorpusRunner, LegacyEquationScript,
};
pub use eqedit::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_COMPILER_VERSION, EQEDIT_PARSER_VERSION,
    EQEDIT_PROFILE_VERSION, EqEditCompileResult, EqEditEngine, EqEditError, EqEditLimitConfig,
    EqEditLimits, EqEditParseRequestDraft, EqEditParseResult,
};
pub use latex::{
    LATEX_ADAPTER_SCHEMA_VERSION, LATEX_PARSER_VERSION, LatexAdapter, LatexAdapterError,
    LatexAdapterLimitConfig, LatexAdapterLimits, LatexAmbiguity, LatexAmbiguityKind,
    LatexCandidate, LatexCandidateChoice, LatexMacroDefinition, LatexParseOutcome,
    LatexParseRequestDraft, LatexParseResult,
};
pub use layout::{
    EQUATION_LAYOUT_PROFILE_VERSION, EQUATION_LAYOUT_QUALIFICATION_SCHEMA_VERSION,
    EQUATION_LAYOUT_SCHEMA_VERSION, EquationLayoutError, EquationLayoutEstimate,
    EquationLayoutEstimator, EquationLayoutLimitConfig, EquationLayoutLimits, EquationLayoutMode,
    EquationLayoutSource,
};
pub use mathml::{
    MATHML_ADAPTER_SCHEMA_VERSION, MATHML_NAMESPACE, MATHML_PROFILE_VERSION, MathMlAdapter,
    MathMlAdapterError, MathMlAdapterLimitConfig, MathMlAdapterLimits, MathMlParseRequestDraft,
    MathMlParseResult, MathMlSourceProfile,
};
