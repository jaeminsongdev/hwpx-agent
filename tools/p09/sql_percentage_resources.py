"""P149 SQL host admission/watch only; no child Job or container qualification.

일반 CPU 부하는 허용한다. host RAM/commit 비율과 포화 상태를 관측하며,
소유 자식의 aggregate Job 상한을 대신한다고 주장하지 않는다.
"""
import threading
import time
import math

from conservative_maintenance import Windows, POLICY, decision, admitted_count, require

MAX_SAMPLES = 1440  # 600s reader scope + cleanup margin, bounded numeric observations only.


def resource_policy():
    return {"logical_cpu_limit": 1, "priority": "BelowNormal",
        "container_memory_bytes": 536870912, "container_swap_total_bytes": 536870912,
        "pids_limit": 64, "sample_seconds": POLICY["sample_seconds"],
        "start_available_ram_min_percent": POLICY["start_ram_min_percent"],
        "start_consecutive_samples": POLICY["start_consecutive_samples"],
        "maximum_admission_seconds": POLICY["admission_max_seconds"],
        "already_saturated_cpu_percent": POLICY["emergency_cpu_percent"],
        "cpu_stop_percent": POLICY["emergency_cpu_percent"],
        "cpu_stop_consecutive_samples": POLICY["emergency_cpu_consecutive_samples"],
        "minimum_available_ram_percent": POLICY["stop_ram_min_percent"],
        "maximum_commit_used_percent": POLICY["stop_commit_used_percent"],
        "host_child_aggregate_job_enforced": False,
        "host_job_launch_path_integrated": True,
        "host_primary_job_ram_max_percent": 7, "host_observation_job_ram_max_percent": 1,
        "host_job_SQL_actual_qualification": False,
        "container_kernel_limits_qualified_by_this_helper": False}


class PercentageResources:
    def __init__(self, windows=None):
        self.windows = Windows() if windows is None else windows
        self.k, self.handle = self.windows.k, self.windows.k.GetCurrentProcess()
        require(self.windows.mask == 1, "sql_parent_affinity_not_exact")
        self.samples, self.hot, self.reason = [], 0, None
        self.stop, self.done = threading.Event(), threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.watch, daemon=True)
        self.last_sample_at = time.monotonic()

    def _failed(self, code):
        self.reason = self.reason or code
        self.stop.set()

    def sample(self):
        # Admission and watcher share one sampler; no overlapping GetSystemTimes deltas.
        with self.lock:
            try:
                require(len(self.samples) < MAX_SAMPLES, "STOP_RESOURCE_SAMPLE_BUDGET")
                row = self.windows.sample()
                require(isinstance(row, dict) and {"system_cpu_percent", "available_ram_percent",
                    "commit_used_percent"}.issubset(row), "STOP_RESOURCE_OBSERVATION_INVALID")
                hot, reason = decision(row, self.hot)
                self.hot = hot
                self.samples.append(row)
                self.last_sample_at = time.monotonic()
                if reason:
                    self._failed(reason)
                return row
            except (ValueError, OSError):
                self._failed("STOP_RESOURCE_OBSERVATION_FAILED")
                raise

    def admit(self, sleep=time.sleep, clock=time.monotonic):
        require(not self.thread.is_alive() and self.thread.ident is None
            and not self.done.is_set(), "sql_admission_lifecycle_invalid")
        deadline, count = clock() + POLICY["admission_max_seconds"], 0
        while clock() < deadline:
            sleep(POLICY["sample_seconds"])
            row = self.sample()
            require(not self.stop.is_set(), self.reason or "bootstrap_resource_stop")
            require(row["system_cpu_percent"] < POLICY["emergency_cpu_percent"],
                "DEFERRED_ALREADY_SATURATED_SYSTEM")
            count = admitted_count(row, count)
            if count >= POLICY["start_consecutive_samples"]:
                require(clock() <= deadline, "bootstrap_idle_window_not_admitted")
                return count
        require(False, "bootstrap_idle_window_not_admitted")

    def start(self):
        self.admit()
        self.thread.start()

    def checkpoint_io(self):
        # Pre-hash has no watcher yet. Runtime uses the existing watcher to avoid
        # racing two GetSystemTimes samplers or multiplying the saturation counter.
        require(self.samples and not self.done.is_set(), "sql_io_without_live_admission")
        require(not self.stop.is_set(), self.reason or "resource_stop")
        now = time.monotonic()
        require(type(now) in (int, float) and math.isfinite(now) and now >= self.last_sample_at,
            "sql_io_clock_invalid")
        if self.thread.ident is None:
            if now-self.last_sample_at >= POLICY["sample_seconds"]:
                self.sample()
        else:
            require(self.thread.is_alive(), "STOP_RESOURCE_WATCHER_NOT_ALIVE")
        require(not self.stop.is_set(), self.reason or "resource_stop")

    def watch(self):
        while not self.done.wait(POLICY["sample_seconds"]):
            try:
                self.sample()
                if self.stop.is_set():
                    return
            except (ValueError, OSError):
                return


def admit(resources):
    return resources.admit()
