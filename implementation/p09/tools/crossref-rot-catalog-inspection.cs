// Isolated diagnostic only. Never GetObject/BindToObject/activation, application properties, documents or process control.
using System;
using System.Threading;
namespace P09CrossrefExisting {
    public sealed class CatalogInspection {
        public int Entries, CandidateNames, OtherNames;
        public bool EnumerationComplete, CatalogReleased;
    }
    public static class CatalogReadback {
        internal static CatalogInspection Inspect(ICatalog catalog) {
            var result=new CatalogInspection();
            try {
                while(true) {
                    IEntry entry=null;
                    if(!catalog.Next(out entry)){Check.That(entry==null,"INSPECTION_END_WITHOUT_ENTRY");result.EnumerationComplete=true;break;}
                    Check.That(entry!=null,"INSPECTION_ENUM_ENTRY");
                    using(entry) {
                        Check.That(result.Entries<ExistingOwner.MaxEntries,"INSPECTION_ENUM_BOUND");
                        // Display-name classification only. IEntry.Existing is deliberately never called.
                        bool candidate=ExistingOwner.CandidateName(entry.Name);result.Entries++;
                        if(candidate)result.CandidateNames++;else result.OtherNames++;
                    }
                }
            }finally {catalog.Dispose();result.CatalogReleased=true;}
            return result;
        }
        public static CatalogInspection InspectCurrentCatalogOnly() {
            Check.That(IntPtr.Size==4 && Thread.CurrentThread.GetApartmentState()==ApartmentState.STA,"INSPECTION_X86_STA_REQUIRED");
            return Inspect(new NativeCatalog());
        }
    }
    public static class CatalogReadbackModels {
        sealed class Entry:IEntry {
            internal string Label="!HwpObject.110.1";internal int Gets,Closes;
            public string Name{get{return Label;}}
            public ICandidate Existing(){Gets++;throw new InvalidOperationException("INSPECTION_MUST_NEVER_GET_OBJECT");}
            public void Dispose(){Closes++;}
        }
        sealed class Catalog:ICatalog {
            internal System.Collections.Generic.List<Entry> Rows=new System.Collections.Generic.List<Entry>();
            internal int Cursor,Closes;internal bool FailEnd,FailClose;
            public bool Next(out IEntry entry){entry=null;if(Cursor==Rows.Count){if(FailEnd)throw new InvalidOperationException("MODEL_ENUM_FAILED");return false;}
                entry=Rows[Cursor++];return true;}
            public void Dispose(){Closes++;if(FailClose)throw new InvalidOperationException("MODEL_CLOSE_FAILED");}
        }
        static void Assert(bool value){Check.That(value,"INSPECTION_MODEL_ASSERTION");}
        static void Released(Catalog catalog){Assert(catalog.Closes==1);foreach(var entry in catalog.Rows){Assert(entry.Gets==0);}}
        static void Reject(Catalog catalog,string code){bool rejected=false;try{CatalogReadback.Inspect(catalog);}catch(InvalidOperationException e){rejected=e.Message==code;}Assert(rejected);Released(catalog);}
        public static void Run(string name){
            var catalog=new Catalog();
            switch(name){
            case "empty":{var r=CatalogReadback.Inspect(catalog);Assert(r.Entries==0&&r.CandidateNames==0&&r.EnumerationComplete&&r.CatalogReleased);Released(catalog);break;}
            case "names_only":{
                catalog.Rows.Add(new Entry());catalog.Rows.Add(new Entry{Label="other-document-private-name"});catalog.Rows.Add(new Entry{Label="!HwpObject.120.1"});
                var r=CatalogReadback.Inspect(catalog);Assert(r.Entries==3&&r.CandidateNames==1&&r.OtherNames==2&&r.EnumerationComplete);Released(catalog);
                foreach(var entry in catalog.Rows)Assert(entry.Closes==1);break;}
            case "exact_limit":{for(int i=0;i<256;i++)catalog.Rows.Add(new Entry());var r=CatalogReadback.Inspect(catalog);Assert(r.Entries==256&&r.CandidateNames==256);Released(catalog);break;}
            case "overflow":{for(int i=0;i<257;i++)catalog.Rows.Add(new Entry());Reject(catalog,"P09_XREF_ROT_INSPECTION_ENUM_BOUND");Assert(catalog.Rows[256].Closes==1);break;}
            case "incomplete":{catalog.Rows.Add(new Entry());catalog.FailEnd=true;Reject(catalog,"MODEL_ENUM_FAILED");break;}
            case "invalid_name":{catalog.Rows.Add(new Entry{Label=new String('x',1025)});Reject(catalog,"P09_XREF_ROT_NAME_BOUND");Assert(catalog.Rows[0].Closes==1);break;}
            case "null_name":{catalog.Rows.Add(new Entry{Label=null});Reject(catalog,"P09_XREF_ROT_NAME_BOUND");break;}
            case "release_failure":{catalog.FailClose=true;Reject(catalog,"MODEL_CLOSE_FAILED");break;}
            default:throw new InvalidOperationException("P09_XREF_ROT_INSPECTION_UNKNOWN_MODEL");
            }
        }
    }
}
