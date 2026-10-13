"""Combine cooperative cancellation and accounting without editing SQL drivers.

원래 main/reader/자원 제한/cleanup 경로는 보존한다. 이 연결부만으로 실제 SQL 중
취소나 컨테이너 제거를 검증했다고 주장하지 않는다. 동시 호출용 전역 patch가 아니다.
"""
import time
from unittest.mock import patch

import conservative_maintenance as c
from sql_call_accounting import account_driver_call, closed_code
from sql_cooperative_cancel import cancellable_resource_type


def account_cancellable_driver_call(driver, arguments, cancel, *, clock=time.monotonic):
    c.require(callable(getattr(cancel, "is_set", None)), "SQL_CANCELLED_CALL_OBSERVER_REQUIRED")
    original, constructed = driver.IdleResources, []
    derived = cancellable_resource_type(original, cancel)

    class TrackedResources(derived):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            constructed.append(self)

    # 원래 main 호출의 admission/pre-hash/finally 전체를 동일한 collector로 관측한다.
    # 관측/취소 dependency만 호출 범위 안에서 바꾸고 모든 예외에서도 자동 복구한다.
    with patch.object(driver, "IdleResources", TrackedResources):
        row = account_driver_call(driver, arguments, clock=clock)
    row.update(cooperative_resource_count=len(constructed), cooperative_resource_stop_reason=None,
        cooperative_resource_stop_latched=None, original_resource_type_inherited=None,
        original_driver_dependencies_restored=driver.IdleResources is original,
        full_SQL_wrapper_cancellation_and_container_cleanup_qualified=False)
    if len(constructed) > 1:
        row["state"], row["cooperative_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCELLED_CALL_RESOURCE_INVENTORY_CHANGED"
    elif len(constructed) == 1:
        resources = constructed[0]
        try:
            reason, stopped = resources.reason, resources.stop.is_set()
            c.require(type(stopped) is bool and (reason is None or isinstance(reason, str)),
                "SQL_CANCELLED_CALL_RESOURCE_OBSERVATION_INVALID")
            c.require(stopped == (reason is not None), "SQL_CANCELLED_CALL_RESOURCE_OBSERVATION_INVALID")
            row["cooperative_resource_stop_reason"] = closed_code(ValueError(reason)) if reason is not None else None
            row["cooperative_resource_stop_latched"] = stopped
            row["original_resource_type_inherited"] = isinstance(resources, original)
            if stopped and row["driver_return_code"] == 0:
                row["state"], row["cooperative_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCELLED_CALL_STOP_RETURNED_SUCCESS"
        except (ValueError, OSError, AttributeError, TypeError):
            row["state"], row["cooperative_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CANCELLED_CALL_RESOURCE_OBSERVATION_INVALID"
    return row
