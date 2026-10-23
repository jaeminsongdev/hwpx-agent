// Same-assembly fake candidate only. No Attach/NativeCatalog/COM/kernel call.
using System;
namespace P09CrossrefExisting {
    public static class PreassignedLeaseModels {
        private sealed class FakeCandidate:ICandidate {
            public object Application{get{return this;}}public object Windows{get{return this;}}public object Window{get{return this;}}
            public Observation Read(){throw new InvalidOperationException("P09_XREF_BIND_MODEL_READ_NOT_ALLOWED");}
            public void Dispose(){Disposals++;if(FailDispose)throw new InvalidOperationException("P09_XREF_BIND_MODEL_DISPOSE_FAILED");}
        }
        public static int Disposals;public static bool FailDispose;
        public static ExistingOwnerLease CreateLease(bool fail) {
            Disposals=0;FailDispose=fail;
            return new ExistingOwnerLease(new FakeCandidate(),new Observation{Pid=101,Session=1,Birth=133000000000000001,
                Window=123,WindowVerified=true,Image=ExistingOwner.Image,Version="11.0.0.9136"});
        }
    }
}
