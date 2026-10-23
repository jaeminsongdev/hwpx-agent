//! Private TEST-ONLY elapsed observations. Never package/actor/key/policy values.
use std::{cell::Cell, time::Instant};

thread_local! {
    static CASE: Cell<Option<usize>> = const { Cell::new(None) };
}

pub(super) struct Scope(Option<usize>);
impl Scope {
    pub(super) fn enter(index: usize) -> Self {
        Self(CASE.with(|current| current.replace(Some(index))))
    }
}
impl Drop for Scope {
    fn drop(&mut self) {
        CASE.with(|current| current.set(self.0));
    }
}

pub(super) struct Timer {
    index: Option<usize>,
    last: Instant,
}
impl Timer {
    pub(super) fn new(index: usize) -> Self {
        Self { index: Some(index), last: Instant::now() }
    }
    pub(super) fn current() -> Self {
        Self { index: CASE.with(Cell::get), last: Instant::now() }
    }
    pub(super) fn record(&mut self, stage: &'static str) {
        let elapsed = self.last.elapsed().as_micros();
        if let Some(index) = self.index {
            eprintln!("P149_SIGNED_COST:{index}:{stage}:{elapsed}");
        }
        self.last = Instant::now();
    }
}
