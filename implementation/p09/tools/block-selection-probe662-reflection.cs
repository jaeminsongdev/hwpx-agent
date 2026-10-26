// Fixed six OUT LONG slots only. No activation, launches or document mutations.
using System;
using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
public sealed class P09Selection662Snapshot {
    public bool ReturnIsBoolean;
    public bool Returned;
    public bool CoordinatesAreInt32;
    public int[] Positions;
}
public static class P09Selection662Reflection {
    private static P09Selection662Snapshot Core(object target) {
        object[] args = { -1, -1, -1, -1, -1, -1 };
        var modifier = new ParameterModifier(6);
        for (int i = 0; i < 6; i++) modifier[i] = true;
        object value = target.GetType().InvokeMember("GetSelectedPos",
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.InvokeMethod,
            null, target, args, new ParameterModifier[] { modifier }, CultureInfo.InvariantCulture, null);
        var result = new P09Selection662Snapshot();
        result.ReturnIsBoolean = value is bool;
        result.Returned = value is bool && (bool)value;
        result.CoordinatesAreInt32 = true;
        for (int i = 0; i < 6; i++) if (!(args[i] is int)) result.CoordinatesAreInt32 = false;
        if (result.CoordinatesAreInt32) {
            result.Positions = new int[6];
            for (int i = 0; i < 6; i++) result.Positions[i] = (int)args[i];
        }
        return result;
    }
    public static P09Selection662Snapshot ReadExistingCom(object target) {
        if (target == null || !Marshal.IsComObject(target)) throw new InvalidOperationException("P09_SELECTION662_EXISTING_COM_REQUIRED");
        return Core(target);
    }
    public sealed class FixedModel {
        private readonly int scenario;
        public FixedModel(int scenario) { this.scenario = scenario; }
        public bool GetSelectedPos(out int a, out int b, out int c, out int d, out int e, out int f) {
            a=0; b=1; c=2; d=0; e=3; f=4;
            if (scenario == 2) throw new COMException("PRIVATE_MODEL_ERROR", unchecked((int)0x80004005));
            return scenario == 0;
        }
    }
    // Fixed managed fixtures only, not caller-supplied objects or Native permits.
    public static P09Selection662Snapshot InspectFixedModel(int scenario) {
        if (scenario < 0 || scenario > 2) throw new ArgumentOutOfRangeException();
        return Core(new FixedModel(scenario));
    }
}
