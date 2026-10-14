"""Facade checks and isolated review configuration; no canonical writer."""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import accept_current_queue_successor as m


def require(value,label):
    if not value:raise ValueError(label)


class Tests(unittest.TestCase):
    def test_wrong_context_rejected_before_acceptor_access(self):
        for index,config in ((True,None),(160,None),(161,NS(index=160,before=154)),(161,NS(index=161,before=153))):
            with self.assertRaises(ValueError):m.facade(NS(require=require,base=NS(CONFIG=config)),NS(),index)
    def test_whole_failure_does_not_read_review_witness(self):
        calls=[]
        def prepare(q,pin):calls.append("whole");raise ValueError("WHOLE_FAILED")
        q=NS(json=lambda name:calls.append("witness"),pin=lambda name:calls.append("pin"))
        with self.assertRaises(ValueError):m.validated_prepare(q,{},prepare,"review",NS())
        self.assertEqual(calls,["whole"])
    def test_private_config_keeps_original_code_and_default_config(self):
        def configure(index):
            global CONFIG
            if CONFIG is not None:raise ValueError("ONCE")
            CONFIG=NS(index=index)
            return CONFIG
        env=dict(CONFIG=NS(index=161),NS=NS)
        fn=FunctionType(configure.__code__,env)
        base=NS(CONFIG=env["CONFIG"],configure=fn)
        private=m.isolate_review_config(NS(old=NS(base=base)))
        self.assertIs(private.old.base.configure.__code__,fn.__code__)
        self.assertIsNone(private.old.base.CONFIG)
        private.old.base.configure(161)
        self.assertEqual(private.old.base.CONFIG.index,161)
        self.assertIs(base.CONFIG,env["CONFIG"])
        with self.assertRaises(ValueError):private.old.base.configure(162)


if __name__=="__main__":unittest.main()
