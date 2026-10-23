//! Exact checked rational arithmetic; no floating point, rounding, cache mutation or native claims.
use super::EvaluationError;
use crate::{FormulaBinaryOperator, FormulaDecimal, FormulaFunction};

pub(super) struct Accumulator {
    numerator: i128,
    denominator: i128,
    product: bool,
}
impl Accumulator {
    pub(super) fn new(function: FormulaFunction) -> Self {
        Self {
            numerator: i128::from(function == FormulaFunction::Product),
            denominator: 1,
            product: function == FormulaFunction::Product,
        }
    }
    pub(super) fn push(&mut self, value: FormulaDecimal) -> Result<(), EvaluationError> {
        let (n, d) = ratio(value);
        let (new_n, new_d) = if self.product {
            let left = i128::try_from(gcd(self.numerator.unsigned_abs(), d.unsigned_abs()))
                .map_err(|_| EvaluationError::Overflow)?;
            let right = i128::try_from(gcd(n.unsigned_abs(), self.denominator.unsigned_abs()))
                .map_err(|_| EvaluationError::Overflow)?;
            (
                (self.numerator / left).checked_mul(n / right),
                (self.denominator / right).checked_mul(d / left),
            )
        } else {
            let divisor = i128::try_from(gcd(self.denominator.unsigned_abs(), d.unsigned_abs()))
                .map_err(|_| EvaluationError::Overflow)?;
            (
                self.numerator.checked_mul(d / divisor).and_then(|a| {
                    n.checked_mul(self.denominator / divisor)
                        .and_then(|b| a.checked_add(b))
                }),
                self.denominator.checked_mul(d / divisor),
            )
        };
        let new_n = new_n.ok_or(EvaluationError::Overflow)?;
        let new_d = new_d.ok_or(EvaluationError::Overflow)?;
        let divisor = i128::try_from(gcd(new_n.unsigned_abs(), new_d.unsigned_abs()))
            .map_err(|_| EvaluationError::Overflow)?;
        self.numerator = new_n / divisor;
        self.denominator = new_d / divisor;
        Ok(())
    }
    pub(super) fn finish(
        self,
        function: FormulaFunction,
        count: i64,
        places: u8,
    ) -> Result<FormulaDecimal, EvaluationError> {
        let denominator = if function == FormulaFunction::Average {
            self.denominator
                .checked_mul(i128::from(count))
                .ok_or(EvaluationError::Overflow)?
        } else {
            self.denominator
        };
        decimal(self.numerator, denominator, places)
    }
}

pub(super) fn bound(value: FormulaDecimal, places: u8) -> Result<FormulaDecimal, EvaluationError> {
    if value.scale() > places {
        Err(EvaluationError::DecimalPrecision)
    } else {
        Ok(value)
    }
}
fn ratio(value: FormulaDecimal) -> (i128, i128) {
    (
        i128::from(value.coefficient()),
        10i128.pow(u32::from(value.scale())),
    )
}
fn decimal(mut n: i128, mut d: i128, places: u8) -> Result<FormulaDecimal, EvaluationError> {
    if d == 0 {
        return Err(EvaluationError::DivisionByZero);
    }
    if d < 0 {
        n = n.checked_neg().ok_or(EvaluationError::Overflow)?;
        d = d.checked_neg().ok_or(EvaluationError::Overflow)?;
    }
    let divisor = i128::try_from(gcd(n.unsigned_abs(), d.unsigned_abs()))
        .map_err(|_| EvaluationError::Overflow)?;
    n /= divisor;
    d /= divisor;
    let original_d = d;
    let mut twos = 0u8;
    let mut fives = 0u8;
    while d % 2 == 0 {
        d /= 2;
        twos += 1;
    }
    while d % 5 == 0 {
        d /= 5;
        fives += 1;
    }
    if d != 1 {
        return Err(EvaluationError::NonTerminatingDecimal);
    }
    let scale = twos.max(fives);
    if scale > places {
        return Err(EvaluationError::DecimalPrecision);
    }
    let multiplier = 10i128.pow(u32::from(scale)) / original_d;
    let coefficient = n
        .checked_mul(multiplier)
        .and_then(|v| i64::try_from(v).ok())
        .ok_or(EvaluationError::Overflow)?;
    Ok(FormulaDecimal::new(coefficient, scale))
}
fn gcd(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let remainder = a % b;
        a = b;
        b = remainder;
    }
    a
}
pub(super) fn negate(value: FormulaDecimal, places: u8) -> Result<FormulaDecimal, EvaluationError> {
    bound(
        FormulaDecimal::new(
            value
                .coefficient()
                .checked_neg()
                .ok_or(EvaluationError::Overflow)?,
            value.scale(),
        ),
        places,
    )
}
pub(super) fn binary(
    op: FormulaBinaryOperator,
    a: FormulaDecimal,
    b: FormulaDecimal,
    places: u8,
) -> Result<FormulaDecimal, EvaluationError> {
    let (an, ad) = ratio(a);
    let (bn, bd) = ratio(b);
    let pair = match op {
        FormulaBinaryOperator::Add | FormulaBinaryOperator::Subtract => {
            let scale = a.scale().max(b.scale());
            let left = an
                .checked_mul(10i128.pow(u32::from(scale - a.scale())))
                .ok_or(EvaluationError::Overflow)?;
            let right = bn
                .checked_mul(10i128.pow(u32::from(scale - b.scale())))
                .ok_or(EvaluationError::Overflow)?;
            let n = if op == FormulaBinaryOperator::Add {
                left.checked_add(right)
            } else {
                left.checked_sub(right)
            }
            .ok_or(EvaluationError::Overflow)?;
            (n, 10i128.pow(u32::from(scale)))
        }
        FormulaBinaryOperator::Multiply => (
            an.checked_mul(bn).ok_or(EvaluationError::Overflow)?,
            ad.checked_mul(bd).ok_or(EvaluationError::Overflow)?,
        ),
        FormulaBinaryOperator::Divide => {
            if bn == 0 {
                return Err(EvaluationError::DivisionByZero);
            }
            (
                an.checked_mul(bd).ok_or(EvaluationError::Overflow)?,
                ad.checked_mul(bn).ok_or(EvaluationError::Overflow)?,
            )
        }
        FormulaBinaryOperator::Power => return Err(EvaluationError::UnsupportedExponent),
    };
    decimal(pair.0, pair.1, places)
}
pub(super) fn exponent_steps(value: FormulaDecimal, limit: u32) -> Result<u32, EvaluationError> {
    if value.scale() != 0 || value.coefficient().unsigned_abs() > u64::from(limit) {
        return Err(EvaluationError::UnsupportedExponent);
    }
    u32::try_from(value.coefficient().unsigned_abs())
        .map_err(|_| EvaluationError::UnsupportedExponent)
}
pub(super) fn power(
    a: FormulaDecimal,
    b: FormulaDecimal,
    places: u8,
) -> Result<FormulaDecimal, EvaluationError> {
    if a.coefficient() == 0 && b.coefficient() == 0 {
        return Err(EvaluationError::UndefinedPower);
    }
    let (mut bn, mut bd) = ratio(a);
    if b.coefficient() < 0 {
        if bn == 0 {
            return Err(EvaluationError::DivisionByZero);
        }
        std::mem::swap(&mut bn, &mut bd);
    }
    let divisor = i128::try_from(gcd(bn.unsigned_abs(), bd.unsigned_abs()))
        .map_err(|_| EvaluationError::Overflow)?;
    bn /= divisor;
    bd /= divisor;
    let mut numerator = 1i128;
    let mut denominator = 1i128;
    for _ in 0..b.coefficient().unsigned_abs() {
        numerator = numerator.checked_mul(bn).ok_or(EvaluationError::Overflow)?;
        denominator = denominator
            .checked_mul(bd)
            .ok_or(EvaluationError::Overflow)?;
    }
    decimal(numerator, denominator, places)
}
