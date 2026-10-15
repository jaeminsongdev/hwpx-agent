"""Registration must reach actual dispatch globals, not just wrapper globals."""
from types import FunctionType,SimpleNamespace as NS
import unittest
import closed_preparation_private_entry_v1 as m


class Tests(unittest.TestCase):
    def test_distinct_wrapper_and_dispatch_families_both_updated(self):
        def main(q):return current_namespaces(q)
        old=lambda q:("old",q)
        family=dict(__name__="p09_exact_dispatch",current_namespaces=old)
        execute=FunctionType(main.__code__,family)
        replacement=lambda q:("new",q)
        dispatch=NS(main=execute,current_namespaces=replacement)
        m.publish_dynamic_family(dispatch)
        self.assertEqual(dispatch.main("reader"),("new","reader"))
        self.assertIs(execute.__code__,main.__code__)
    def test_entry_loader_updates_current_and_future_dynamic_connections(self):
        def main(q):return current_namespaces(q)
        family=dict(__name__="p09_exact_dispatch",current_namespaces=lambda q:"old")
        dispatch=NS(main=FunctionType(main.__code__,family),current_namespaces=lambda q:"initial")
        def connect_dynamic(namespace,configure):namespace.current_namespaces=configure;return "proof"
        linked=NS(modules=NS(current_queue_successor_dispatch=dispatch),connection=NS(connect_dynamic=connect_dynamic))
        entry=NS(load=lambda *args,**kwargs:linked)
        loader=NS(load=lambda *args,**kwargs:(NS(closed_prebody_factory_admission_fix_v1=entry),[]))
        modules,_=m.entry_loader(loader).load()
        api=NS(require=lambda ok,label:None,AcceptanceReader=object)
        result=modules.closed_prebody_factory_admission_fix_v1.load(None,api)
        self.assertEqual(dispatch.main(None),"initial")
        self.assertEqual(result.connection.connect_dynamic(dispatch,lambda q:"later"),"proof")
        self.assertEqual(dispatch.main(None),"later")
    def test_default_functions_not_mutated(self):
        def main(q):return q
        before=dict(main.__globals__)
        m.publish_dynamic_family(NS(main=main,current_namespaces=lambda q:q))
        self.assertEqual(main.__globals__,before)


if __name__=="__main__":unittest.main()
