// User-authorized read-only existing process diagnosis. No activation, document action or process control.
using System;
using System.Reflection;
using System.Runtime.InteropServices;
namespace P09CrossrefExisting {
    public sealed class OwnerReadbackObservation {
        public string State,Phase,ErrorCode,HResult,HandleType;
        public bool ExactKernelWindowVersion,EnumerationComplete,ReferencesReleased;
        public int CandidateNames;
    }
    public static class OwnerReadback {
        static object Property(object value,string name){return value.GetType().InvokeMember(name,BindingFlags.GetProperty,null,value,null);}
        public static string ClosedError(Exception exception){
            var e=exception.GetBaseException();return e is InvalidOperationException && e.Message.StartsWith("P09_XREF_ROT_",StringComparison.Ordinal)
                && System.Text.RegularExpressions.Regex.IsMatch(e.Message,"^P09_XREF_ROT_[A-Z_]{1,120}$")?e.Message:"P09_XREF_ROT_READBACK_FAILURE_NO_RAW_VALUES";
        }
        public static string ErrorHResult(Exception exception){return exception.GetBaseException().HResult.ToString("X8");}
        public static OwnerReadbackObservation Inspect(ExpectedOwner expected){
            Check.That(IntPtr.Size==4&&System.Threading.Thread.CurrentThread.GetApartmentState()==System.Threading.ApartmentState.STA,"READBACK_X86_STA_REQUIRED");
            var r=new OwnerReadbackObservation{State="OBSERVED_EXISTING_OWNER_READBACK_FAILURE_NOT_SESSION",Phase="catalog"};
            ICatalog catalog=null;ICandidate candidate=null;object windows=null,window=null;
            try{
                catalog=new NativeCatalog();
                for(int count=0;;count++){
                    r.Phase="enum_next";IEntry entry=null;
                    if(!catalog.Next(out entry)){Check.That(entry==null,"READBACK_ENUM_END");r.EnumerationComplete=true;break;}
                    Check.That(entry!=null,"READBACK_ENUM_ENTRY");
                    using(entry){
                        Check.That(count<ExistingOwner.MaxEntries,"READBACK_ENUM_BOUND");r.Phase="display_name";
                        if(!ExistingOwner.CandidateName(entry.Name))continue;
                        r.CandidateNames++;Check.That(r.CandidateNames==1,"READBACK_DUPLICATE_CANDIDATES");
                        r.Phase="get_existing_object";candidate=entry.Existing();Check.That(candidate!=null,"READBACK_MISSING_OBJECT");
                        r.Phase="XHwpWindows";windows=Property(candidate.Application,"XHwpWindows");Check.That(Marshal.IsComObject(windows),"READBACK_REAL_WINDOWS");
                        r.Phase="Item";window=windows.GetType().InvokeMember("Item",BindingFlags.GetProperty|BindingFlags.InvokeMethod,null,windows,new object[]{0});
                        Check.That(Marshal.IsComObject(window),"READBACK_REAL_WINDOW");
                        r.Phase="WindowHandle";object handle=Property(window,"WindowHandle");r.HandleType=handle==null?"null":handle.GetType().FullName;
                        Check.That(handle is int&&(int)handle!=0,"EXACT_INT32_WINDOW_HANDLE");
                        r.Phase="kernel_identity";var identity=NativeIdentity.Read(NativeIdentity.WindowPid((int)handle),(int)handle);
                        r.Phase="Version";identity.Version=Convert.ToString(Property(candidate.Application,"Version"),System.Globalization.CultureInfo.InvariantCulture).Replace(',','.').Replace(" ","");
                        r.Phase="exact_expected_identity";ExistingOwner.Validate(expected,identity);
                        r.Phase="original_adapter_read";var original=candidate.Read();ExistingOwner.Validate(expected,original);
                        Check.That(original.Window==identity.Window,"SAME_OWNER_BEFORE_AFTER");r.ExactKernelWindowVersion=true;
                    }
                }
                r.Phase="complete";Check.That(r.CandidateNames==1&&r.ExactKernelWindowVersion,"NO_EXACT_EXISTING_OWNER");
                r.State="OBSERVED_EXISTING_OWNER_READONLY_PROPERTIES_NOT_SESSION_OR_EXECUTION";
            }catch(Exception error){r.ErrorCode=ClosedError(error);r.HResult=ErrorHResult(error);}
            finally{
                try{
                    try{Check.Release(window);}finally{try{Check.Release(windows);}finally{try{if(candidate!=null)candidate.Dispose();}finally{if(catalog!=null)catalog.Dispose();}}}
                    r.ReferencesReleased=true;
                }catch(Exception error){r.State="OBSERVED_EXISTING_OWNER_READBACK_CLEANUP_FAILURE_NOT_SESSION";r.ErrorCode=ClosedError(error);r.HResult=ErrorHResult(error);r.ReferencesReleased=false;}
            }
            return r;
        }
    }
}
