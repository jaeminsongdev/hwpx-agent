#![forbid(unsafe_code)]

mod automation;
mod eqedit;
mod latex;
mod mathml;

pub use automation::{
    EQUATION_AUTOMATION_PROFILE_VERSION, EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION,
    EQUATION_AUTOMATION_SCHEMA_VERSION, EquationAutomationError, EquationAutomationLimitConfig,
    EquationAutomationLimits, EquationAutomationOperationDraft, EquationAutomationPlan,
    EquationAutomationPlanner, EquationAutomationReceiptDraft, EquationAutomationReceiptState,
    EquationAutomationSelection, EquationAutomationSourceState, EquationAutomationTarget,
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
pub use mathml::{
    MATHML_ADAPTER_SCHEMA_VERSION, MATHML_NAMESPACE, MATHML_PROFILE_VERSION, MathMlAdapter,
    MathMlAdapterError, MathMlAdapterLimitConfig, MathMlAdapterLimits, MathMlParseRequestDraft,
    MathMlParseResult, MathMlSourceProfile,
};
