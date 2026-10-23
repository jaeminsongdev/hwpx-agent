// Private existing-ROT adapter only. No COM activation, document actions, launch,
// retry, timeout or process termination. Attach requires a future qualified host.
using System;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;
using System.Threading;

namespace P09CrossrefExisting {
    public sealed class ExpectedOwner {
        public readonly int Pid, Session;
        public readonly long Birth;
        public ExpectedOwner(int pid, int session, long birth) {
            Check.That(pid>0 && session>=0 && birth>0,"EXPECTED_IDENTITY");
            Pid=pid;Session=session;Birth=birth;
        }
    }
    public sealed class Observation {
        public int Pid,Session,Window;
        public long Birth;
        public string Image,Version;
        public bool WindowVerified;
    }
    internal static class Check {
        internal static void That(bool ok,string code) {if(!ok)throw new InvalidOperationException("P09_XREF_ROT_"+code);}
        internal static void Release(object value) {if(value!=null && Marshal.IsComObject(value))Marshal.ReleaseComObject(value);}
    }
    internal interface ICandidate:IDisposable {
        Observation Read(); object Application {get;} object Windows {get;} object Window {get;}
    }
    internal interface IEntry:IDisposable {string Name {get;} ICandidate Existing();}
    internal interface ICatalog:IDisposable {bool Next(out IEntry entry);}
    public sealed class ExistingOwnerLease:IDisposable {
        private ICandidate candidate;
        public readonly Observation Identity;
        internal ExistingOwnerLease(ICandidate value,Observation identity) {candidate=value;Identity=identity;}
        public object Application {get {Check.That(candidate!=null,"LEASE_CLOSED");return candidate.Application;}}
        public object Windows {get {Check.That(candidate!=null,"LEASE_CLOSED");return candidate.Windows;}}
        public object Window {get {Check.That(candidate!=null,"LEASE_CLOSED");return candidate.Window;}}
        public bool NativeStartupQualified {get {return false;}}
        public void Dispose() {if(candidate!=null){var owned=candidate;candidate=null;owned.Dispose();}}
    }
    public static class ExistingOwner {
        public const string Image=@"C:\Program Files (x86)\HNC\Office 2020\HOffice110\bin\hwp.exe";
        internal const int MaxEntries=256,MaxName=1024;
        internal static bool CandidateName(string name) {
            Check.That(name!=null && name.Length<=MaxName,"NAME_BOUND");
            const string prefix="!HwpObject.110.";
            if(!name.StartsWith(prefix,StringComparison.Ordinal))return false;
            int n=name.Length-prefix.Length;if(n<1 || n>10)return false;
            for(int i=prefix.Length;i<name.Length;i++)if(name[i]<'0'||name[i]>'9')return false;
            return true;
        }
        internal static void Validate(ExpectedOwner expected,Observation value) {
            Check.That(value!=null && value.Pid==expected.Pid && value.Session==expected.Session
                && value.Birth==expected.Birth && value.Window!=0 && value.WindowVerified
                && String.Equals(value.Image,Image,StringComparison.OrdinalIgnoreCase)
                && value.Version=="11.0.0.9136","EXACT_NATIVE_KERNEL_WINDOW_VERSION");
        }
        internal static ExistingOwnerLease Select(ICatalog catalog,ExpectedOwner expected) {
            ICandidate selected=null;Observation before=null;ExistingOwnerLease output=null;
            try {
                for(int count=0;;count++) {
                    IEntry entry=null;
                    if(!catalog.Next(out entry)){Check.That(entry==null,"END_WITHOUT_ENTRY");break;}
                    Check.That(entry!=null,"ENUM_ENTRY");
                    using(entry) {
                        Check.That(count<MaxEntries,"ENUM_BOUND");
                        if(!CandidateName(entry.Name))continue;
                        ICandidate current=null;
                        try {
                            current=entry.Existing();Check.That(current!=null,"RUNNING_OBJECT_MISSING");
                            var identity=current.Read();Validate(expected,identity);
                            Check.That(selected==null,"AMBIGUOUS_RUNNING_OWNERS");
                            selected=current;before=identity;current=null;
                        } finally {if(current!=null)current.Dispose();}
                    }
                }
                Check.That(selected!=null,"NO_EXACT_EXISTING_OWNER");
                var after=selected.Read();Validate(expected,after);
                Check.That(before.Window==after.Window && before.Pid==after.Pid && before.Session==after.Session
                    && before.Birth==after.Birth && before.Image==after.Image && before.Version==after.Version,
                    "SAME_OWNER_BEFORE_AFTER");
                output=new ExistingOwnerLease(selected,after);selected=null;
            } finally {
                try {catalog.Dispose();}
                catch {if(output!=null)output.Dispose();throw;}
                finally {if(selected!=null)selected.Dispose();}
            }
            return output;
        }
        public static ExistingOwnerLease Attach(ExpectedOwner expected) {
            Check.That(expected!=null && IntPtr.Size==4 && Thread.CurrentThread.GetApartmentState()==ApartmentState.STA,
                "X86_STA_WORKER_REQUIRED");
            // No moniker BindToObject or ProgID activation fallback.
            return Select(new NativeCatalog(),expected);
        }
        // Qualification helper reads only this worker's own kernel handle.
        // Its non-Hancom image can never pass Validate as an owned native process.
        public static Observation InspectCurrentProcessOnly() {return NativeIdentity.Read(NativeIdentity.CurrentPid(),0);}
    }
    internal sealed class NativeCatalog:ICatalog {
        [DllImport("ole32.dll")]private static extern int GetRunningObjectTable(uint reserved,out IRunningObjectTable table);
        [DllImport("ole32.dll")]private static extern int CreateBindCtx(uint reserved,out IBindCtx context);
        private IRunningObjectTable table;private IBindCtx context;private IEnumMoniker enumeration;
        internal NativeCatalog() {
            try {
                Check.That(GetRunningObjectTable(0,out table)==0 && table!=null,"GET_RUNNING_TABLE");
                Check.That(CreateBindCtx(0,out context)==0 && context!=null,"CREATE_BIND_CONTEXT");
                table.EnumRunning(out enumeration);Check.That(enumeration!=null,"ENUM_RUNNING");
            } catch {Dispose();throw;}
        }
        public bool Next(out IEntry entry) {
            var items=new IMoniker[1];int status=enumeration.Next(1,items,IntPtr.Zero);entry=null;
            try {
                if(status==1){Check.That(items[0]==null,"COMPLETE_ENUM_END");return false;}
                Check.That(status==0 && items[0]!=null,"ENUM_NEXT_RESULT");
                entry=new NativeEntry(items[0],table,context);items[0]=null;return true;
            }finally {Check.Release(items[0]);}
        }
        public void Dispose() {
            try {Check.Release(enumeration);}finally {enumeration=null;
                try {Check.Release(context);}finally {context=null;Check.Release(table);table=null;}}
        }
    }
    internal sealed class NativeEntry:IEntry {
        private IMoniker moniker;private readonly IRunningObjectTable table;private readonly IBindCtx context;
        internal NativeEntry(IMoniker value,IRunningObjectTable running,IBindCtx binding){moniker=value;table=running;context=binding;}
        public string Name {get {string value;moniker.GetDisplayName(context,null,out value);return value;}}
        public ICandidate Existing() {
            object value=null;
            try {Check.That(table.GetObject(moniker,out value)==0 && value!=null,"GET_EXISTING_OBJECT");
                var result=new NativeCandidate(value);value=null;return result;
            } finally {Check.Release(value);}
        }
        public void Dispose(){Check.Release(moniker);moniker=null;}
    }
    internal sealed class NativeCandidate:ICandidate {
        private object application,windows,window;
        internal NativeCandidate(object value){Check.That(Marshal.IsComObject(value),"REAL_EXISTING_COM_REQUIRED");application=value;}
        private static object Property(object value,string name) {
            return value.GetType().InvokeMember(name,BindingFlags.GetProperty,null,value,null);
        }
        public object Application {get{return application;}}public object Windows {get{return windows;}}public object Window {get{return window;}}
        public Observation Read() {
            if(windows==null)windows=Property(application,"XHwpWindows");
            Check.That(Marshal.IsComObject(windows),"REAL_WINDOW_COLLECTION");
            if(window==null)window=windows.GetType().InvokeMember("Item",BindingFlags.GetProperty|BindingFlags.InvokeMethod,null,windows,new object[]{0});
            Check.That(Marshal.IsComObject(window),"REAL_WINDOW_OBJECT");
            var raw=Property(window,"WindowHandle");Check.That(raw is int && (int)raw!=0,"EXACT_INT32_WINDOW_HANDLE");
            int pid=NativeIdentity.WindowPid((int)raw);var row=NativeIdentity.Read(pid,(int)raw);
            row.Version=Convert.ToString(Property(application,"Version"),System.Globalization.CultureInfo.InvariantCulture).Replace(',','.').Replace(" ","");
            return row;
        }
        public void Dispose() {
            try {Check.Release(window);}finally {window=null;
                try {Check.Release(windows);}finally {windows=null;Check.Release(application);application=null;}}
        }
    }
    internal static class NativeIdentity {
        [StructLayout(LayoutKind.Sequential)]private struct FileTime{public uint Low,High;}
        [DllImport("kernel32.dll")]internal static extern int GetCurrentProcessId();
        [DllImport("kernel32.dll",SetLastError=true)]private static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
        [DllImport("kernel32.dll")]private static extern int GetProcessId(IntPtr handle);
        [DllImport("kernel32.dll")]private static extern uint WaitForSingleObject(IntPtr handle,uint millis);
        [DllImport("kernel32.dll",SetLastError=true)]private static extern bool GetProcessTimes(IntPtr handle,out FileTime birth,out FileTime exit,out FileTime kernel,out FileTime user);
        [DllImport("kernel32.dll",SetLastError=true)]private static extern bool GetExitCodeProcess(IntPtr handle,out uint code);
        [DllImport("kernel32.dll",SetLastError=true)]private static extern bool ProcessIdToSessionId(int pid,out int session);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]private static extern bool QueryFullProcessImageName(IntPtr handle,uint flags,StringBuilder image,ref uint size);
        [DllImport("kernel32.dll",SetLastError=true)]private static extern bool CloseHandle(IntPtr handle);
        [DllImport("user32.dll")]private static extern uint GetWindowThreadProcessId(IntPtr window,out int pid);
        internal static int CurrentPid(){return GetCurrentProcessId();}
        internal static int WindowPid(int window) {
            int pid;var handle=IntPtr.Size==4?new IntPtr(window):new IntPtr((long)(uint)window);
            Check.That(GetWindowThreadProcessId(handle,out pid)!=0 && pid>0,"WINDOW_PROCESS_ID");return pid;
        }
        internal static Observation Read(int pid,int window) {
            Check.That(pid>0 && (window!=0 || pid==CurrentPid()),"QUERY_NATIVE_WINDOW_OR_SELF_ONLY");
            var handle=OpenProcess(0x00101000,false,pid);Check.That(handle!=IntPtr.Zero,"OPEN_QUERY_SYNCHRONIZE_ONLY");
            try {
                FileTime birth=new FileTime(),exit,kernel,user;uint code=0;int session=0;var image=new StringBuilder(32768);uint size=32768;
                Check.That(GetProcessId(handle)==pid && WaitForSingleObject(handle,0)==258
                    && GetProcessTimes(handle,out birth,out exit,out kernel,out user)
                    && GetExitCodeProcess(handle,out code) && code==259 && ProcessIdToSessionId(pid,out session)
                    && QueryFullProcessImageName(handle,0,image,ref size),"LIVE_HELD_KERNEL_IDENTITY");
                Check.That(window==0 || WindowPid(window)==pid,"HELD_WINDOW_PROCESS");
                Check.That(WaitForSingleObject(handle,0)==258 && GetProcessId(handle)==pid,"SAME_LIVE_HELD_PROCESS");
                return new Observation{Pid=pid,Session=session,Birth=(long)(((ulong)birth.High<<32)|birth.Low),Image=image.ToString(),Window=window,WindowVerified=window!=0};
            }finally{Check.That(CloseHandle(handle),"CLOSE_QUERY_HANDLE");}
        }
    }
}
