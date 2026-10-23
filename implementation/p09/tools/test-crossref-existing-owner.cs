// Same-assembly controlled models. No NativeCatalog/Attach call, ROT or COM API.
using System;
using System.Collections.Generic;
namespace P09CrossrefExisting {
    public static class ExistingOwnerTests {
        private static ExpectedOwner Expected(){return new ExpectedOwner(101,1,133000000000000001);}
        private static Observation Row(){return new Observation{Pid=101,Session=1,Birth=133000000000000001,
            Window=123,WindowVerified=true,Image=ExistingOwner.Image,Version="11.0.0.9136"};}
        private static void Assert(bool ok){Check.That(ok,"MODEL_ASSERTION");}
        private static void Reject(Action action,string code){bool rejected=false;try{action();}
            catch(InvalidOperationException e){rejected=e.Message=="P09_XREF_ROT_"+code;}Assert(rejected);}
        private sealed class Candidate:ICandidate {
            internal int Reads,Closes;internal Func<int,Observation> Source=delegate(int n){return Row();};
            public object Application{get{return this;}}public object Windows{get{return this;}}public object Window{get{return this;}}
            public Observation Read(){Reads++;return Source(Reads);}public void Dispose(){Closes++;}
        }
        private sealed class Entry:IEntry {
            internal string Label="!HwpObject.110.1";internal Candidate Value=new Candidate();internal int Gets,Closes;
            public string Name{get{return Label;}}public ICandidate Existing(){Gets++;return Value;}
            public void Dispose(){Closes++;}
        }
        private sealed class Catalog:ICatalog {
            internal readonly List<Entry> Rows=new List<Entry>();internal int Cursor,Closes;internal bool FailEnd,FailClose;
            public bool Next(out IEntry entry){entry=null;if(Cursor==Rows.Count){if(FailEnd)throw new InvalidOperationException("MODEL_ENUM_FAILED");return false;}
                entry=Rows[Cursor++];return true;}
            public void Dispose(){Closes++;if(FailClose)throw new InvalidOperationException("MODEL_CLOSE_FAILED");}
        }
        private static Catalog One(){var result=new Catalog();result.Rows.Add(new Entry());return result;}
        private static void Drift(string field,object value){var source=One();source.Rows[0].Value.Source=delegate(int n){var r=Row();
            typeof(Observation).GetField(field).SetValue(r,value);return r;};
            Reject(delegate{ExistingOwner.Select(source,Expected());},"EXACT_NATIVE_KERNEL_WINDOW_VERSION");
            Assert(source.Rows[0].Value.Closes==1 && source.Closes==1);}
        public static void Run(string name) {
            switch(name) {
            case "name_family":
                Assert(ExistingOwner.CandidateName("!HwpObject.110.1") && ExistingOwner.CandidateName("!HwpObject.110.72"));
                foreach(var value in new[]{"!HwpObject.120.1","!hwpObject.110.1","!HwpObject.110.","!HwpObject.110.-1","!HwpObject.110.1x","!HwpObject.110.1\n"})Assert(!ExistingOwner.CandidateName(value));break;
            case "name_bound":
                Reject(delegate{ExistingOwner.CandidateName(null);},"NAME_BOUND");
                Reject(delegate{ExistingOwner.CandidateName(new String('x',1025));},"NAME_BOUND");break;
            case "one_exact_owner": {
                var cat=One();var value=cat.Rows[0].Value;var lease=ExistingOwner.Select(cat,Expected());
                Assert(cat.Closes==1 && cat.Rows[0].Closes==1 && value.Reads==2 && value.Closes==0 && !lease.NativeStartupQualified);
                Assert(lease.Application==value && lease.Windows==value && lease.Window==value);lease.Dispose();Assert(value.Closes==1);break;}
            case "no_owner_no_fallback": {
                var cat=new Catalog();Reject(delegate{ExistingOwner.Select(cat,Expected());},"NO_EXACT_EXISTING_OWNER");Assert(cat.Closes==1);break;}
            case "duplicate_owners": {
                var cat=One();cat.Rows.Add(new Entry());Reject(delegate{ExistingOwner.Select(cat,Expected());},"AMBIGUOUS_RUNNING_OWNERS");
                Assert(cat.Rows[0].Value.Closes==1 && cat.Rows[1].Value.Closes==1 && cat.Rows[1].Closes==1 && cat.Closes==1);break;}
            case "incomplete_enumeration": {
                var cat=One();cat.FailEnd=true;bool caught=false;try{ExistingOwner.Select(cat,Expected());}catch(InvalidOperationException e){caught=e.Message=="MODEL_ENUM_FAILED";}
                Assert(caught && cat.Rows[0].Value.Closes==1 && cat.Closes==1);break;}
            case "pid_mismatch":Drift("Pid",102);break;
            case "session_mismatch":Drift("Session",2);break;
            case "birth_one_tick_mismatch":Drift("Birth",133000000000000002L);break;
            case "image_mismatch":Drift("Image",@"D:\other\hwp.exe");break;
            case "version_mismatch":Drift("Version","11.0.0.9137");break;
            case "window_required":Drift("Window",0);Drift("WindowVerified",false);break;
            case "window_changed_after_scan": {
                var cat=One();cat.Rows[0].Value.Source=delegate(int n){var r=Row();if(n==2)r.Window=124;return r;};
                Reject(delegate{ExistingOwner.Select(cat,Expected());},"SAME_OWNER_BEFORE_AFTER");Assert(cat.Rows[0].Value.Closes==1);break;}
            case "exact_enum_limit": {
                var cat=One();for(int i=1;i<256;i++)cat.Rows.Add(new Entry{Label="other"+i});
                using(var lease=ExistingOwner.Select(cat,Expected())){Assert(cat.Cursor==256);}Assert(cat.Rows[0].Value.Closes==1);break;}
            case "enum_overflow_not_first_match": {
                var cat=One();for(int i=1;i<257;i++)cat.Rows.Add(new Entry{Label="other"+i});
                Reject(delegate{ExistingOwner.Select(cat,Expected());},"ENUM_BOUND");Assert(cat.Rows[0].Value.Closes==1 && cat.Rows[256].Closes==1);break;}
            case "get_object_missing": {
                var cat=One();cat.Rows[0].Value=null;Reject(delegate{ExistingOwner.Select(cat,Expected());},"RUNNING_OBJECT_MISSING");Assert(cat.Rows[0].Closes==1 && cat.Closes==1);break;}
            case "catalog_cleanup_failure": {
                var cat=One();cat.FailClose=true;bool caught=false;try{ExistingOwner.Select(cat,Expected());}catch(InvalidOperationException e){caught=e.Message=="MODEL_CLOSE_FAILED";}
                Assert(caught && cat.Rows[0].Value.Closes==1 && cat.Closes==1);break;}
            case "invalid_expected_identity":
                Reject(delegate{new ExpectedOwner(0,1,1);},"EXPECTED_IDENTITY");Reject(delegate{new ExpectedOwner(1,-1,1);},"EXPECTED_IDENTITY");
                Reject(delegate{new ExpectedOwner(1,1,0);},"EXPECTED_IDENTITY");break;
            case "unknown_names_never_get_objects": {
                var cat=One();cat.Rows.Insert(0,new Entry{Label="!HwpObject.120.1"});cat.Rows.Add(new Entry{Label="PRIVATE-MONIKER-NOT-OUTPUT"});
                using(var lease=ExistingOwner.Select(cat,Expected())){Assert(cat.Rows[0].Gets==0 && cat.Rows[2].Gets==0);}break;}
            case "lease_close_once": {
                var cat=One();var lease=ExistingOwner.Select(cat,Expected());lease.Dispose();lease.Dispose();Assert(cat.Rows[0].Value.Closes==1);
                Reject(delegate{var ignored=lease.Application;},"LEASE_CLOSED");break;}
            case "stable_kernel_self_not_hancom": {
                var first=ExistingOwner.InspectCurrentProcessOnly();var second=ExistingOwner.InspectCurrentProcessOnly();
                Assert(first.Pid==second.Pid && first.Session==second.Session && first.Birth==second.Birth && first.Birth>0
                    && first.Image==second.Image && !first.WindowVerified && first.Window==0);
                Reject(delegate{ExistingOwner.Validate(new ExpectedOwner(first.Pid,first.Session,first.Birth),first);},"EXACT_NATIVE_KERNEL_WINDOW_VERSION");break;}
            default:throw new InvalidOperationException("P09_XREF_ROT_MODEL_UNKNOWN_CASE");
            }
        }
    }
}
