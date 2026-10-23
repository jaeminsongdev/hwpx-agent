# Readonly preparation gate. A positive first host reply NEVER reaches case IO.
# Native qualification must use a different, explicit, fully qualified entry.
class P09PreassignedPreparationDenyReader : System.IO.TextReader {
    [System.IO.TextReader]$Inner
    [string]$Pending=''
    [int]$Offset=0
    [bool]$FirstReplyChecked=$false
    [bool]$FirstReplyRejected=$false
    P09PreassignedPreparationDenyReader([System.IO.TextReader]$inner) {$this.Inner=$inner}
    [int]Read() {
        if ($this.Offset -lt $this.Pending.Length) {
            $answer=[int][char]$this.Pending[$this.Offset];$this.Offset++;return $answer
        }
        $builder=[Text.StringBuilder]::new();$line=$null
        for ($i=0;$i -le 4096;$i++) {
            $value=$this.Inner.Read()
            if ($value -lt 0) {return -1}
            if ($value -eq 10) {$line=$builder.ToString().TrimEnd([char]13);break}
            [void]$builder.Append([char]$value)
        }
        if ($null -eq $line -or [Text.Encoding]::UTF8.GetByteCount($line) -gt 4096) {throw 'P09_XREF_BIND_PREPARATION_REPLY_LIMIT'}
        if (-not $this.FirstReplyChecked) {
            $this.FirstReplyChecked=$true
            $pattern='^\{"schema_version":"hwpx-agent\.private\.crossref-preassigned-host-response/v2","sequence":1,"case_index":1,"acknowledged":false,"error_code":"(XREF_HOST_|XREF_NATIVE_STARTUP_|XREF_NATIVE_LIMITS_|XREF_PREASSIGNED_SCOPE_|STOP_|P09_XREF_|P58_)[A-Z0-9_]{1,120}","owner_descriptor":null,"native_execution_authorized":false,"p09_complete":false\}$'
            if (-not [regex]::IsMatch($line,$pattern,[Text.RegularExpressions.RegexOptions]::CultureInvariant)) {
                $this.FirstReplyRejected=$true;throw 'P09_XREF_BIND_PREPARATION_REQUIRES_DENIAL'
            }
        }
        $this.Pending=$line+"`n";$this.Offset=1;return [int][char]$this.Pending[0]
    }
}
