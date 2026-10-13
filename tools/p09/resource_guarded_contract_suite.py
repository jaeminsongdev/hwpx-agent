"""계약검사의 setUp 전/tearDown 후 기존 보호 콜백을 확인한다.

실제 제품 수용을 대신하지 않는다. 검사 제외, 별도 sampler/thread, 새 대기,
CPU/RAM 기준 변경 없이 기존 unittest의 실행과 결과를 그대로 유지한다.
"""
from contextlib import contextmanager
from unittest.mock import patch
import unittest

SELF = 'tools/p09/resource_guarded_contract_suite.py'
TEST = 'tools/p09/tests/test_resource_guarded_contract_suite.py'
_ORIGINAL_RUNNER = unittest.TextTestRunner
_ACTIVE = False


class ContractCheckpoints:
    def __init__(self, checkpoint):
        if not callable(checkpoint):
            raise ValueError('CONTRACT_CHECKPOINT_REQUIRED')
        self.checkpoint = checkpoint
        self.started = self.stopped = self.before_checks = self.after_checks = 0
        self.runner_before_checks = self.runner_after_checks = 0
        self.runner_calls = self.returned_runner_calls = 0

    def runner_type(self):
        owner = self

        class GuardedRunner(_ORIGINAL_RUNNER):
            def _makeResult(self):
                original_result = self.resultclass

                class GuardedResult(original_result):
                    def startTest(self, test):
                        # TestCase.__call__의 setUp보다 먼저 실행된다.
                        owner.checkpoint()
                        owner.before_checks += 1
                        super().startTest(test)
                        owner.started += 1

                    def stopTest(self, test):
                        # unittest 원래 결과 처리를 유지; STOP은 다음 검사로 전달하지 않는다.
                        super().stopTest(test)
                        owner.stopped += 1
                        owner.checkpoint()
                        owner.after_checks += 1

                return GuardedResult(self.stream, self.descriptions, self.verbosity)

            def run(self, test):
                owner.runner_calls += 1
                owner.checkpoint()
                owner.runner_before_checks += 1
                result = super().run(test)
                owner.checkpoint()
                owner.runner_after_checks += 1
                owner.returned_runner_calls += 1
                return result

        return GuardedRunner

    def summary(self):
        return dict(
            started_tests=self.started, stopped_tests=self.stopped,
            successful_before_test_checks=self.before_checks,
            successful_after_test_checks=self.after_checks,
            runner_calls=self.runner_calls, returned_runner_calls=self.returned_runner_calls,
            successful_before_runner_checks=self.runner_before_checks,
            successful_after_runner_checks=self.runner_after_checks,
            original_unittest_results_preserved=True,
            new_sampler_or_thread_or_sleep_started=False,
            original_guard_or_test_coverage_relaxed=False,
            test_results_are_not_product_acceptance=True,
        )


@contextmanager
def bind(checkpoint):
    """단일 동기 실행 구간만 교체하고 오류/STOP에도 원래 실행기를 복원한다."""
    global _ACTIVE
    if _ACTIVE or unittest.TextTestRunner is not _ORIGINAL_RUNNER:
        raise ValueError('CONTRACT_RUNNER_ALREADY_BOUND_OR_CHANGED')
    statistics = ContractCheckpoints(checkpoint)
    _ACTIVE = True
    try:
        with patch.object(unittest, 'TextTestRunner', statistics.runner_type()):
            yield statistics
    finally:
        _ACTIVE = False
