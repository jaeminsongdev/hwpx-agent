import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bounded_cpu_attribution_probe_v1 as probe


class Tests(unittest.TestCase):
    def snapshot(self, time, pid=1, ticks=0, creation=10):
        return dict(time_monotonic=time, rows={pid:dict(pid=pid,parent=0,role="python.exe",creation=creation,ticks=ticks)},
                    unavailable=2,truncated=False)

    def test_machine_normalization(self):
        out=probe.compare(self.snapshot(1),self.snapshot(3,ticks=20000000),16)
        self.assertEqual(out["top_processes"][0]["machine_CPU_percent"],6.25)
        self.assertFalse(out["complete_system_CPU_attribution"])

    def test_new_or_reused_pid_never_false_delta(self):
        for current in (self.snapshot(3,pid=2,ticks=100),self.snapshot(3,ticks=100,creation=11)):
            out=probe.compare(self.snapshot(1),current,16)
            self.assertEqual(out["top_processes"],[])
            self.assertEqual(out["new_or_reused_pid_no_baseline"],1)

    def test_negative_delta_unknown(self):
        out=probe.compare(self.snapshot(1,ticks=100),self.snapshot(3,ticks=0),16)
        self.assertEqual(out["negative_delta_unresolved"],1)
        self.assertEqual(out["top_processes"],[])

    def test_window_and_processor_validation(self):
        for processors in (0,65,True,1.5):
            with self.assertRaises(ValueError):probe.compare(self.snapshot(1),self.snapshot(3),processors)
        with self.assertRaises(ValueError):probe.compare(self.snapshot(3),self.snapshot(1),16)

    def test_unknown_names_redacted(self):
        self.assertEqual(probe.role("MsMpEng.exe"),"msmpeng.exe")
        self.assertEqual(probe.role("private-name.exe"),"other")
        self.assertEqual(probe.role(None),"other")

    def test_top8_and_missing_not_zero(self):
        old=self.snapshot(1);new=self.snapshot(3)
        for pid in range(1,20):
            old["rows"][pid]=dict(pid=pid,parent=0,role="other",creation=10,ticks=0)
            new["rows"][pid]=dict(pid=pid,parent=0,role="other",creation=10,ticks=pid*10000000)
        out=probe.compare(old,new,16)
        self.assertEqual(len(out["top_processes"]),8)
        self.assertEqual(out["top_processes"][0]["pid"],19)
        self.assertEqual(out["unavailable_current"],2)

    def test_no_helper_process_or_watcher(self):
        tree=ast.parse(Path(probe.__file__).read_text(encoding="utf-8"))
        attrs={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(attrs & {"Popen","Thread","check_output","TerminateProcess","QueryFullProcessImageNameW"})
        self.assertEqual((probe.MAX_PROCESSES,probe.MAX_OBSERVATIONS),(512,17))


if __name__ == "__main__":unittest.main()
