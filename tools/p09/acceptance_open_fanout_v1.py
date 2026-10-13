"""Acceptance-only conservative file-open fanout:20/s ->10/s.
Same original pacer, fresh reads/final hashes/guards/deadlines/one sampler.
New qualification is a fresh acceptance witness, NOT retroactive Native input.
"""
from types import FunctionType,SimpleNamespace as NS
import optimized_current_queue_acceptance_v3 as prior

SELF="tools/p09/acceptance_open_fanout_v1.py"
TEST="tools/p09/tests/test_acceptance_open_fanout_v1.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case151-acceptance-open-fanout-code6-r501.v1.json"
QUAL_STATE="PASS_ACCEPTANCE_FILE_OPEN_FANOUT_CODE6_NOT_ACCEPTANCE"
OPEN_RATE=10

def require(ok,code):
    if not ok:raise ValueError("ACCEPTANCE_OPEN_FANOUT_"+code)

def runtime(original):
    readers=[]
    class Reader(original.a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            p=self.open_pacer
            require(type(p.rate) is int and p.rate==20 and p.opens==0 and p.previous is None,
                    "ONE_ORIGINAL_UNSTARTED_PACER")
            # Do not replace the pacer, clock, credit, checkpoint or sampler.
            p.rate=OPEN_RATE
            readers.append(self)
    result=NS(**{**vars(original),"a":NS(**{**vars(original.a),"AcceptanceReader":Reader})})
    return result,readers

def qualify(q,m,pin):
    require(pin["path"]==QUAL_PATH,"EXACT_QUALIFICATION")
    row=m.a.read_exact(q,pin)
    m.a.fields(row,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
       cleanup_confirmed=True,Native_product_or_acceptance_executed=False,open_rate=OPEN_RATE),"CODE6_NOT_ACCEPTANCE")
    require(set(m.base.scope.pins(row["new_code_pins"],2))=={SELF,TEST},"EXACT_CODE2")
    for p in row["new_code_pins"]:m.a.exact(q.pin(p["path"]),p,"FRESH_QUALIFIED_CODE")

def summary(readers):
    return [dict(open_rate=r.open_pacer.rate,actual_open_reservations=r.open_pacer.opens,
       paced_sleep_seconds=r.open_pacer.sleep_seconds,same_original_pacer=True,
       original_byte_rates_source_reads_final_hashes_and_guards_retained=True,
       new_sampler_thread_or_process=False,Native_input_claimed=False) for r in readers]

def run(m,root,old,persistent,terminal,qualification,diagnostic):
    private,readers=runtime(m)
    def projection(runtime,raw,rp,op,np,tp,leaf):
        execute,state=prior.projection(runtime,raw,rp,op,np,tp,leaf)
        before=execute.__globals__["prepare"]
        def prepare(q):
            result=before(q);qualify(q,m,qualification);return result
        return FunctionType(execute.__code__,dict(execute.__globals__,prepare=prepare),
                    argdefs=execute.__defaults__,closure=execute.__closure__),state
    runner=FunctionType(prior.run.__code__,dict(prior.run.__globals__,projection=projection),
                    argdefs=prior.run.__defaults__,closure=prior.run.__closure__)
    row,pin=runner(private,root,old,persistent,terminal,diagnostic)
    return row,pin,summary(readers)
