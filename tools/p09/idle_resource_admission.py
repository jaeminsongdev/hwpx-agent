"""Shared post-hash idle admission. Original continuous CPU/RAM stop guards are retained."""
import time

from check_idle_resource_window import MAX_SECONDS, REQUIRED, SAMPLE_SECONDS, stable_count
from run_formula_issuer_registry_sql_checks import Resources, require


class IdleResources(Resources):
    def start(self):
        deadline = time.monotonic() + MAX_SECONDS
        count = 0
        while time.monotonic() < deadline:
            time.sleep(SAMPLE_SECONDS)
            sample = self.sample()
            require(not self.stop.is_set(), self.reason or "idle_resource_stop")
            count = stable_count(count, sample)
            if count >= REQUIRED:
                self.thread.start()
                return
        require(False, "post_hash_idle_window_not_admitted")
