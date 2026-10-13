"""P217: 원 Native open pacing에도 기존 P185 부하 완화를 적용한다.

원 수용된 P206/P208/P209/P215 코드는 바꾸지 않는다. 새 실행 frame에 명시적으로
연결할 때만 적용된다. 원 owner 표본/CPU·RAM·IO 및 잠금 deadline을 유지한다.
"""
import borrowed_locked_streams as borrowed
import near_saturation_read_backpressure as pressure

SELF='tools/p09/native_open_backpressure.py'
TEST='tools/p09/tests/test_native_open_backpressure.py'


class PressureInputLocks(borrowed.BorrowedInputLocks):
    def __init__(self,root,checkpoint,resources,*,pressure_sleep=pressure.time.sleep,**kw):
        super().__init__(root,checkpoint,**kw)
        borrowed.require(self.api.pacer.checkpoint is checkpoint,'ORIGINAL_NATIVE_PACER_CHECKPOINT')
        # self.check는 원 owner checkpoint와 원 잠금 deadline을 검사한다.
        # 부하 완화 중에도 이 guard를 매회 실행한다. 새 표본/스레드는 만들지 않는다.
        self.open_pressure=pressure.PressureCheckpoint(self.check,resources,sleep=pressure_sleep)
        self.api.pacer.checkpoint=self.open_pressure

    def summary(self):
        row=super().summary()
        row['native_open_backpressure']=dict(**self.open_pressure.summary(),
            original_frame_deadline_checked_before_open=True,
            original_32_open_rate_limit_and_no_burst_credits_preserved=True,
            pressure_applies_to_native_reservations_including_borrowed_streams=True,
            original_owner_sample_source_reused=True,
            cleanup_not_guarded_by_pressure=True,
            measured_CPU_or_PC_freeze_improvement_claimed=False)
        return row
