"""Run the unchanged P196 runtime closing with bounded P197 attribution.

과거 whole/Gate 확인이나 통과한 product body는 실행하지 않는다.
새 controller 입력은 원 reader의 fresh before/after 확인에 포함한다.
"""
import sys
from types import SimpleNamespace
from unittest.mock import patch

import runtime_source_closing_r07 as runtime
import process_cpu_attribution as attribution

SELF='tools/p09/run_attributed_runtime_closing.py'
SOURCES=(SELF,attribution.SELF,attribution.TEST)


def main():
    raw_controller=runtime.controllers;raw_contracts=runtime.contracts
    def controller(q):
        for name in SOURCES:q.pin(name)
        return raw_controller(q)
    def contracts():
        result=raw_contracts()
        result['process_cpu_attribution_contract_tests_passed']=attribution.contracts()
        return result
    def summary(owner):
        result=runtime_observation.summary(owner)
        result['process_CPU_attribution']=attribution.summary(owner)
        return result
    runtime_observation=runtime.observation
    observer=SimpleNamespace(**vars(runtime_observation))
    observer.Resources=attribution.Resources;observer.summary=summary
    with patch.object(runtime,'observation',observer), \
            patch.object(runtime,'controllers',controller),patch.object(runtime,'contracts',contracts):
        return runtime.main()


if __name__=='__main__':raise SystemExit(main())
