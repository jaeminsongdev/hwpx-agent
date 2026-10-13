"""P243: Native 파일 접근 fan-out만 32→20/s로 줄이는 새 소유 instance.

원 CPU/RAM/IO/잠금/identity/borrow/cleanup/두 읽기는 변경하지 않는다.
전역 상수·수용된 helper를 바꾸지 않는다. 낮춘 rate도 no-burst 원 pacer다.
"""
import math
import native_open_backpressure as original
SELF='tools/p09/lower_native_acquisition_pressure.py'
TEST='tools/p09/tests/test_lower_native_acquisition_pressure.py'
RATE=20
ORIGINAL_CEILING=32


def require(ok,code):original.borrowed.require(ok,'LOWER_NATIVE_'+code)


class InputLocks(original.PressureInputLocks):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        pacer=self.api.pacer
        require(pacer.rate==ORIGINAL_CEILING and pacer.opens==0 and pacer.previous is None
            and pacer.checkpoint is self.open_pressure,'UNUSED_ORIGINAL_OWNER_PACER')
        pacer.rate=RATE
    def summary(self):
        row=super().summary()
        row['lower_native_fan_out']=dict(original_upper_ceiling_per_second=ORIGINAL_CEILING,
            selected_maximum_reservations_per_second=RATE,nominal_reservation_density_reduction_percent=37.5,
            original_pacer_and_no_burst_preserved=True,original_CPU_RAM_IO_lock_guards_preserved=True,
            all_identity_and_byte_checks_retained=True,cleanup_not_rate_or_pressure_guarded=True,
            measured_CPU_or_PC_freeze_improvement_claimed=False)
        return row


def estimate(input_count,binary_bytes,other_bytes,observed_metadata_seconds):
    """원 STOP frame 집계와 고정 EXE의 실제 크기로만 예산을 추정한다.

    실제 입력 pin을 합성하지 않는다. 미래 실행기는 추가 개수/bytes 상한을
    다시 검사해야 하며 이 예상 시간은 완료 보증이나 수용 증거가 아니다.
    """
    require(type(input_count) is int and input_count==1525
        and type(binary_bytes) is int and binary_bytes>0
        and type(other_bytes) is int and other_bytes>0
        and type(observed_metadata_seconds) in (float,int)
        and math.isfinite(observed_metadata_seconds) and observed_metadata_seconds>0,'ESTIMATE_ORIGINAL_SCOPE')
    # 연결 시 새 제어 코드는 최대11개/1MiB라는 상한을 다시 검사해야 한다.
    upper_inputs=1536;extra=1024*1024
    native=(3*upper_inputs+306)/RATE
    reads=2*binary_bytes/1048576+2*(other_bytes+extra)/2097152
    metadata=observed_metadata_seconds+15
    product_allowance=20;margin=40;total=native+reads+metadata+product_allowance+margin
    require(total<600,'ESTIMATE_CANNOT_FIT_UNCHANGED600_SCOPE')
    return dict(original_inputs=1525,new_generation_input_upper_bound=upper_inputs,
        original_binary_bytes=binary_bytes,original_other_bytes=other_bytes,
        original_total_bytes=binary_bytes+other_bytes,aggregate_evidence_not_synthetic_input_pins=True,
        future_extra_controller_bytes_upper_bound=extra,selected_native_reservations_per_second=RATE,
        native_reservation_seconds=native,unchanged_two_byte_pass_rate_seconds=reads,
        observed_metadata_seconds=observed_metadata_seconds,metadata_allowance_seconds=metadata,
        product_allowance_seconds=product_allowance,additional_margin_seconds=margin,
        predicted_combined_seconds_with_allowances=total,unchanged_IO_scope_seconds=600,
        prediction_is_not_completion_guarantee=True,bounds_must_be_enforced_when_runtime_connected=True)
