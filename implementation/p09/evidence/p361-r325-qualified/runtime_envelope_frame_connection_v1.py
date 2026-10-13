"""Full original Frame code over explicitly projected physical inputs.

Fresh original boundary factory is called once. Its reader object/pacer/pressure
and 64KiB workspace survive unchanged; only a private Python MRO extension adds
fresh semantic decode. No synthetic Job commit or scope acceptance is provided.
"""
from types import MappingProxyType
import held_envelope_boundary_guard_v1 as connection
import runtime_envelope_scope_binding_v1 as binding_module

SELF="tools/p09/runtime_envelope_frame_connection_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_frame_connection_v1.py"


def adopt_fresh_reader(reader, projection, budget):
    original_type=type(reader);before=dict(vars(reader));original_pacer=reader.pacer
    binding_module.require(reader.read_passes==reader.bytes_read==0,"FRESH_FACTORY_READER_ONLY")
    New=connection.boundary_reader_type(original_type,projection,budget)
    reader.__class__=New
    reader.semantic_decode_counts={};reader.semantic_decoded_bytes=0;reader.envelope_original_boundary_guard_calls=0
    binding_module.require(reader.pacer is original_pacer
        and all(vars(reader).get(k) is value for k,value in before.items()),"EVERY_ORIGINAL_READER_FIELD_RETAINED")
    return reader


def frame_type(original, binding):
    binding_module.require(type(original) is type and type(binding) is binding_module.Binding,"EXACT_FRAME_BINDING")
    class Frame(original):
        def __init__(self,registry,required,checkpoint,held=None):
            projection,proof=binding.project(required,checkpoint)
            self.semantic_inputs=MappingProxyType({n:MappingProxyType(dict(p)) for n,p in projection.semantic_pins.items()})
            self.explicit_projection=projection;self.representation=binding.representation(projection)
            self.alias_reconciliation=proof;self.decoder_budget=connection.original.DecoderBudget(checkpoint)
            self.original_boundary_factories=0
            super().__init__(registry,{n:dict(p) for n,p in projection.physical_pins.items()},checkpoint,held=held)
        def read_boundary(self,reader_factory,checkpoint):
            def factory(guard):
                reader=reader_factory(guard);self.original_boundary_factories+=1
                return adopt_fresh_reader(reader,self.explicit_projection,self.decoder_budget)
            return super().read_boundary(factory,checkpoint)
        def summary(self):
            row=super().summary()
            return dict(row,explicit_source_input_representation=self.representation,
                aggregate_envelope_decoder=self.decoder_budget.evidence(),
                lossless_alias_reconciliation=self.alias_reconciliation,
                original_boundary_factory_calls=self.original_boundary_factories,
                original_frame_acquire_check_read_commit_close_code_retained=True,
                semantic_byte_count_not_reported_as_physical_byte_count=True,
                metadata_and_worker_raw_live_access_policy_connected=False,
                whole_product_connection_qualified=False)
    return Frame
