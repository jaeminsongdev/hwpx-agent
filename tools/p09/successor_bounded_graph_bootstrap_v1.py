"""Bounded source/capsule bootstrap for the qualified private159 graph.

No historical receipt bytes are read by this reader. Parent admission freshly
validates history and the whole scope before GO; worker keeps original GO/Job
and body checks. This bootstrap is not fresh whole-source or product evidence.
"""
import hashlib
import json

import runtime_successor_binding_v1 as successor
import runtime_successor_manifest_v1 as manifest
import runtime_successor_worker_capsule_v1 as capsule
import successor_runtime_graph_v1 as factory

SELF="tools/p09/successor_bounded_graph_bootstrap_v1.py"
MANIFEST=dict(path=manifest.PATH,bytes=3120,sha256="426684aed1ef2532b29ece7a16fb0809c8a8becbc2105c3a8bf4f9032867b10a")


class Reader:
    def __init__(self,m,checkpoint):
        self.m=m;self.checkpoint=checkpoint;self.snapshots={};self.reads=0;self.bytes_read=0
        self.allowed={p["path"]:dict(p) for p in m.NAMESPACE_SOURCE_PINS+[factory.CAPSULE,MANIFEST]}
    def _read(self,name,parse=False):
        self.checkpoint();self.m.a.require(name in self.allowed,"BOOTSTRAP_ONLY_EXACT_SOURCE_CAPSULE_MANIFEST")
        expected=self.allowed[name]
        self.m.a.require(0<expected["bytes"]<=16384 and self.reads<64,"BOUNDED_BOOTSTRAP_READ")
        self.m.base.stable.stable.prior.build.direct_path(self.m.c.ROOT/name,file_required=True)
        with (self.m.c.ROOT/name).open("rb") as stream:raw=stream.read(expected["bytes"]+1)
        pin=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        self.m.a.exact(pin,expected,"EXACT_BOUNDED_BOOTSTRAP_BYTES")
        self.reads+=1;self.bytes_read+=len(raw)
        self.m.a.require(self.bytes_read<=262144,"BOUNDED_BOOTSTRAP_READER_TOTAL")
        self.checkpoint();return pin,raw
    def _bind(self,name,pin):
        self.m.a.exact(pin,self.allowed[name],"EXACT_BOOTSTRAP_SOURCE_PIN")
        self.snapshots[name]=dict(pin)
    def pin(self,name):
        pin,_=self._read(name);self._bind(name,pin);return dict(pin)
    def json(self,name):
        pin,raw=self._read(name,parse=True);self._bind(name,pin)
        return json.loads(raw.decode("utf-8"),object_pairs_hook=self.m.base.unique)


def load(m,checkpoint):
    q=Reader(m,checkpoint);row=q.json(MANIFEST["path"])
    m.a.fields(row,dict(schema_version=manifest.SCHEMA,index=159,before=152,
        authority152_pin=successor.AUTHORITY,actual158_pin=successor.ROOT),"EXACT_BOUNDED159_MANIFEST_CONTEXT")
    graph=factory.build(q,m,successor,capsule,lineage=row["prior_failure_lineage"])
    m.a.exact(dict(graph.binding.manifest_pin),MANIFEST,"SAME_EXACT159_MANIFEST_NOT_BOOTSTRAP_PLACEHOLDER")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        historical_receipts_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        parent_fresh_whole_admission_and_live_locks_required=True,
        complete_controller_worker_dispatch_or_product_qualified=False,GO_authorized=False)
