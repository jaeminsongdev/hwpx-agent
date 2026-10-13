use super::super::{ImportedDocumentFieldSemantics, ImportedFieldMeaning};
use super::{SourceFormulaCellBinding, SourceFormulaEvaluationError as Error, SourceFormulaValue};
use crate::document_import::ImportedSourcePackage;
use crate::{PreservingXmlDocument, XmlElementToken};
use domain_ir::formula_evaluation::{
    EvaluationCell, EvaluationInput, EvaluationLimits, EvaluationReceipt, FormulaEvaluationContext,
};
use domain_ir::{
    CellCoordinate, Flow, FormulaCell, FormulaGridDimensions, FormulaLimits, Inline, LogicalId,
    Node, SourceAnchorHandle, TableCell, TableNode,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeMap, io};
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const MAX_WORK: usize = 8_000_000;
type Output = (
    Vec<SourceFormulaValue>,
    Vec<SourceFormulaCellBinding>,
    Vec<EvaluationReceipt>,
);
struct Target<'a> {
    reference: &'a LogicalId,
    cell: &'a TableCell,
    formula: &'a FormulaCell,
    anchor: &'a SourceAnchorHandle,
}

pub(super) fn evaluate(meanings: &ImportedDocumentFieldSemantics<'_, '_>) -> Result<Output, Error> {
    let original = meanings.fields.forms.source();
    let mut work = 0usize;
    let mut tables = BTreeMap::new();
    let document = meanings.graph().clone().into_draft();
    for section in &document.sections {
        collect(&section.body, &mut tables, &mut work)?;
    }
    for note in &document.notes {
        collect(&note.body, &mut tables, &mut work)?;
    }
    let ranges: BTreeMap<_, _> = meanings
        .fields
        .fields()
        .iter()
        .map(|f| (&f.reference_id, f))
        .collect();
    let mut grouped: BTreeMap<&LogicalId, Vec<Target<'_>>> = BTreeMap::new();
    for meaning in meanings.observations() {
        if let ImportedFieldMeaning::TableFormula {
            dimensions,
            formula,
        } = &meaning.meaning
        {
            let field = ranges.get(&meaning.reference_id).ok_or(Error::Binding)?;
            let begin = original
                .resolve_anchor(&field.begin_anchor)
                .map_err(|_| Error::Binding)?;
            let xml = begin.part().xml().ok_or(Error::Binding)?;
            let begin_index = begin.element_index().ok_or(Error::Binding)?;
            let table_index = ancestor(xml, begin_index, "tbl")?;
            let cell_index = ancestor(xml, begin_index, "tc")?;
            let table_anchor = begin
                .part()
                .element_anchor(table_index)
                .ok_or(Error::Binding)?;
            let table = *tables
                .get(&table_anchor.opaque_handle)
                .ok_or(Error::Binding)?;
            if *dimensions
                != (FormulaGridDimensions {
                    rows: table.rows,
                    columns: table.columns,
                })
            {
                return Err(Error::Binding);
            }
            let cell_anchor = begin
                .part()
                .element_anchor(cell_index)
                .ok_or(Error::Binding)?;
            let cell_id = LogicalId::parse(format!("cell-{}", cell_anchor.opaque_handle.as_str()))
                .map_err(|_| Error::Binding)?;
            let cell = table
                .cells
                .iter()
                .find(|c| c.cell_id == cell_id)
                .ok_or(Error::Binding)?;
            if formula.owner()
                != (CellCoordinate {
                    row: cell.row,
                    column: cell.column,
                })
            {
                return Err(Error::Binding);
            }
            grouped
                .entry(&table_anchor.opaque_handle)
                .or_default()
                .push(Target {
                    reference: &meaning.reference_id,
                    cell,
                    formula,
                    anchor: &field.begin_anchor,
                });
            add_work(&mut work, 1)?;
        }
    }
    let mut values = Vec::new();
    let mut bindings = Vec::new();
    let mut receipts = Vec::new();
    for (anchor, targets) in grouped {
        let table = *tables.get(anchor).ok_or(Error::Binding)?;
        let binding = evaluate_table(original, table, &targets, &mut work)?;
        values.extend(binding.0);
        bindings.extend(binding.1);
        receipts.push(binding.2);
    }
    if values.len() != meanings.receipt().table_formula_asts {
        return Err(Error::Binding);
    }
    Ok((values, bindings, receipts))
}
fn collect<'a>(
    flow: &'a Flow,
    tables: &mut BTreeMap<&'a LogicalId, &'a TableNode>,
    work: &mut usize,
) -> Result<(), Error> {
    for node in &flow.children {
        add_work(work, 1)?;
        match node {
            Node::Table(table) => {
                let anchor = table.common.source_anchor.as_ref().ok_or(Error::Binding)?;
                if tables.insert(&anchor.opaque_handle, table).is_some() {
                    return Err(Error::Binding);
                }
                for cell in &table.cells {
                    add_work(work, 1)?;
                    collect(&cell.body, tables, work)?;
                }
            }
            Node::Drawing(drawing) => collect(&drawing.children, tables, work)?,
            _ => (),
        }
    }
    Ok(())
}
fn evaluate_table(
    original: &ImportedSourcePackage,
    table: &TableNode,
    targets: &[Target<'_>],
    work: &mut usize,
) -> Result<
    (
        Vec<SourceFormulaValue>,
        Vec<SourceFormulaCellBinding>,
        EvaluationReceipt,
    ),
    Error,
> {
    let resolved = original
        .resolve_anchor(table.common.source_anchor.as_ref().ok_or(Error::Binding)?)
        .map_err(|_| Error::Binding)?;
    let xml = resolved.part().xml().ok_or(Error::Binding)?;
    let table_index = resolved.element_index().ok_or(Error::Binding)?;
    let mut cells = BTreeMap::new();
    for row in children(xml, table_index)? {
        if !named(&xml.elements()[row], "tr") {
            continue;
        }
        for cell in children(xml, row)? {
            if !named(&xml.elements()[cell], "tc") {
                return Err(Error::Binding);
            }
            let anchor = resolved.part().element_anchor(cell).ok_or(Error::Binding)?;
            let id = LogicalId::parse(format!("cell-{}", anchor.opaque_handle.as_str()))
                .map_err(|_| Error::Binding)?;
            if cells.insert(id, anchor).is_some() {
                return Err(Error::Binding);
            }
        }
    }
    if cells.len() != table.cells.len() {
        return Err(Error::Binding);
    }
    let mut formulas = BTreeMap::new();
    for target in targets {
        if formulas
            .insert(&target.cell.cell_id, target.formula.ast())
            .is_some()
        {
            return Err(Error::Binding);
        }
    }
    let mut inputs = Vec::new();
    let mut bindings = Vec::new();
    for cell in &table.cells {
        let coordinate = CellCoordinate {
            row: cell.row,
            column: cell.column,
        };
        let anchor = *cells.get(&cell.cell_id).ok_or(Error::Binding)?;
        original
            .resolve_anchor(anchor)
            .map_err(|_| Error::Binding)?;
        let input = if let Some(ast) = formulas.get(&cell.cell_id) {
            EvaluationInput::Formula { ast }
        } else {
            numeric_input(cell, work)?
        };
        let interpretation = match input {
            EvaluationInput::Decimal { .. } => "observed_canonical_decimal_text",
            EvaluationInput::Formula { .. } => "original_source_formula_ast",
            EvaluationInput::Unavailable => "unavailable_not_defaulted",
        };
        inputs.push(EvaluationCell { coordinate, input });
        bindings.push(SourceFormulaCellBinding {
            table_id: table.common.node_id.clone(),
            cell_id: cell.cell_id.clone(),
            coordinate,
            source_anchor: anchor.clone(),
            interpretation,
        });
    }
    let ctx = FormulaEvaluationContext::bind(
        FormulaGridDimensions {
            rows: table.rows,
            columns: table.columns,
        },
        &inputs,
        EvaluationLimits::default(),
        FormulaLimits::default(),
    )?;
    let coordinates: Vec<_> = targets.iter().map(|t| t.formula.owner()).collect();
    let evaluated = ctx.evaluate(&coordinates)?;
    add_work(work, evaluated.receipt().work_steps)?;
    let mut values = Vec::new();
    for (target, value) in targets.iter().zip(evaluated.values()) {
        if target.formula.owner() != value.coordinate {
            return Err(Error::Binding);
        }
        values.push(SourceFormulaValue {
            reference_id: target.reference.clone(),
            table_id: table.common.node_id.clone(),
            cell_id: target.cell.cell_id.clone(),
            coordinate: value.coordinate,
            begin_anchor: target.anchor.clone(),
            value: value.value,
        });
    }
    Ok((values, bindings, evaluated.receipt().clone()))
}
fn numeric_input<'a>(cell: &TableCell, work: &mut usize) -> Result<EvaluationInput<'a>, Error> {
    let [Node::Paragraph(paragraph)] = cell.body.children.as_slice() else {
        return Ok(EvaluationInput::Unavailable);
    };
    let mut text = String::new();
    for inline in &paragraph.inlines {
        let Inline::Text { text: part } = inline else {
            return Ok(EvaluationInput::Unavailable);
        };
        add_work(work, part.len())?;
        if text
            .len()
            .checked_add(part.len())
            .is_none_or(|n| n > FormulaLimits::default().config().input_bytes)
        {
            return Ok(EvaluationInput::Unavailable);
        }
        text.push_str(part);
    }
    Ok(
        crate::table_formula::parse_canonical_decimal(&text, FormulaLimits::default())
            .map_or(EvaluationInput::Unavailable, |value| {
                EvaluationInput::Decimal { value }
            }),
    )
}
fn add_work(work: &mut usize, count: usize) -> Result<(), Error> {
    *work = work
        .checked_add(count)
        .filter(|n| *n <= MAX_WORK)
        .ok_or(Error::Limit)?;
    Ok(())
}
fn named(e: &XmlElementToken, tag: &str) -> bool {
    e.name().namespace() == Some(HP) && e.name().local_name() == tag
}
fn ancestor(xml: &PreservingXmlDocument, index: usize, tag: &str) -> Result<usize, Error> {
    let mut next = xml.elements().get(index).ok_or(Error::Binding)?.parent();
    while let Some(index) = next {
        let e = xml.elements().get(index).ok_or(Error::Binding)?;
        if named(e, tag) {
            return Ok(index);
        }
        next = e.parent();
    }
    Err(Error::Binding)
}
fn children(xml: &PreservingXmlDocument, index: usize) -> Result<Vec<usize>, Error> {
    let mut result = Vec::new();
    let mut next = xml
        .elements()
        .get(index)
        .ok_or(Error::Binding)?
        .first_child();
    while let Some(index) = next {
        result.push(index);
        next = xml
            .elements()
            .get(index)
            .ok_or(Error::Binding)?
            .next_sibling();
    }
    Ok(result)
}
struct BoundedHash {
    digest: Sha256,
    bytes: usize,
}
impl io::Write for BoundedHash {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.bytes = self
            .bytes
            .checked_add(bytes.len())
            .filter(|n| *n <= 16 * 1024 * 1024)
            .ok_or_else(|| io::Error::other("source evaluation evidence limit"))?;
        self.digest.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
pub(super) fn digest<A: Serialize, B: Serialize>(a: &A, b: &B) -> Result<[u8; 32], Error> {
    let mut writer = BoundedHash {
        digest: Sha256::new(),
        bytes: 0,
    };
    serde_json::to_writer(&mut writer, &(a, b)).map_err(|_| Error::Limit)?;
    Ok(writer.digest.finalize().into())
}
