"""P246: byte 제한과 별도로 작은 metadata 파일 시작 밀도를 최대32회/s로 제한.

원 reader/byte pacer/guard/parse/fresh/read-count를 그대로 호출한다. 입력 제외,
pin/JSON 재사용, 원 검사 삭제, 신규 스레드, 전역 상수 수정은 하지 않는다.
"""
import math
import time
import locked_runtime_inputs as locks
SELF='tools/p09/metadata_read_entry_pacing.py'
TEST='tools/p09/tests/test_metadata_read_entry_pacing.py'
RATE=32


def require(ok,code):locks.require(ok,'METADATA_ENTRY_'+code)


class Binding:
    def __init__(self,reader,*,clock=time.monotonic,sleeper=time.sleep):
        require(reader.read_passes==0 and callable(reader.checkpoint) and callable(reader._read)
            and '_p246_entry_binding' not in vars(reader),'FRESH_UNBOUND_READER')
        self.reader=reader;self.original=reader._read;self.had_instance='_read' in vars(reader)
        self.pacer=locks.OpenPacer(reader.checkpoint,rate=RATE,clock=clock,sleeper=sleeper)
        self.active=False;self.used=False;self.calls=self.completed=self.failed=0
    def __enter__(self):
        require(not self.active and not self.used and '_p246_entry_binding' not in vars(self.reader),'ONE_BINDING')
        self.active=self.used=True;self.reader._p246_entry_binding=self
        def read(name,parse=False):
            require(self.active and self.reader._p246_entry_binding is self,'EXACT_ACTIVE_BINDING')
            self.calls+=1
            try:
                self.pacer.reserve()
                result=self.original(name,parse=parse);self.completed+=1;return result
            except BaseException:
                self.failed+=1;raise
        self.reader._read=read;return self
    def __exit__(self,*error):
        # STOP 후 복원에는 checkpoint·sleep·read가 필요하지 않다.
        if self.had_instance:self.reader._read=self.original
        else:del self.reader._read
        del self.reader._p246_entry_binding;self.active=False
        return False
    def summary(self):
        return dict(maximum_metadata_read_entries_per_second=RATE,
            entry_calls=self.calls,completed_original_read_calls=self.completed,failed_calls=self.failed,
            reservations=self.pacer.opens,requested_sleep_seconds=self.pacer.sleep_seconds,
            binding_active=self.active,no_idle_burst=True,original_reader_and_bytes_and_fresh_checks_preserved=True,
            original_CPU_RAM_IO_and_parse_budget_preserved=True,original_pressure_checkpoint_reused=True,
            extra_sampler_or_thread_started=False,original_reads_skipped=False,
            cached_pins_or_parsed_JSON_substituted=False,cleanup_not_guarded_or_paced=True,
            measured_CPU_or_PC_freeze_improvement_claimed=False)


def estimate_budget(native_budget):
    require(native_budget['original_inputs']==1525 and native_budget['original_total_bytes']==119022055
        and native_budget['unchanged_IO_scope_seconds']==600
        and native_budget['prediction_is_not_completion_guarantee'] is True,'SEALED_NATIVE_BUDGET')
    upper_inputs=1540;entry_upper=660
    native=(3*upper_inputs+306)/20;entry=entry_upper/RATE
    total=native+entry+native_budget['unchanged_two_byte_pass_rate_seconds']+native_budget['metadata_allowance_seconds'] \
        +native_budget['product_allowance_seconds']+native_budget['additional_margin_seconds']
    require(math.isfinite(total) and total<600,'COMBINED_WITHIN_UNCHANGED600')
    return dict(new_runtime_inputs_upper_bound=upper_inputs,metadata_original_read_calls_upper_bound=entry_upper,
        future_added_controller_bytes_upper_bound=1048576,metadata_entry_rate=RATE,native_rate=20,
        native_reservation_seconds=native,additional_metadata_entry_seconds=entry,
        predicted_combined_seconds_with_allowances=total,unchanged_IO_scope_seconds=600,
        prediction_is_not_completion_guarantee=True,all_bounds_must_be_enforced_when_runtime_connected=True)
