"""Closed case progress and churn identities; observed wall times, not CPU proof."""
import math
import re
import host_cpu_group_observer as group

BASE_GROUP=group.Observer


def require(ok,code):group.require(ok,'COST_'+code)


class CaseTrace:
    def __init__(self,names):
        require(type(names) in (list,tuple) and 0<len(names)<=249 and len(set(names))==len(names)
            and all(type(n) is str and re.fullmatch(r'[A-Za-z0-9_:]{1,512}',n) for n in names),'NAMES')
        self.names=frozenset(names);self.pending=bytearray();self.active=None;self.completed=[]
        self.started=set();self.running_count=None;self.summary_seen=False;self.nonstandard_lines=0
        self.last_seconds=None

    def feed(self,chunk,seconds):
        require(type(chunk) is bytes and type(seconds) in (float,int) and math.isfinite(seconds) and seconds>=0,'FEED')
        require(self.last_seconds is None or seconds>=self.last_seconds,'TIME_ORDER');self.last_seconds=seconds
        self.pending.extend(chunk)
        while b'\n' in self.pending:
            raw,_,tail=self.pending.partition(b'\n');self.pending=bytearray(tail)
            self._start(raw,seconds)
            if self.active and (raw.startswith(('test '+self.active['case']+' ... ').encode()) or raw.strip() in (b'ok',b'FAILED',b'ignored')):
                prefix=('test '+self.active['case']+' ... ').encode()
                result=(raw[len(prefix):] if raw.startswith(prefix) else raw).strip()
                if result in (b'ok',b'FAILED',b'ignored'):
                    row=dict(self.active,finished_seconds=seconds,observed_wall_seconds=max(0,seconds-self.active['started_seconds']),
                        result=result.decode('ascii'));self.completed.append(row);self.active=None
                else:self.nonstandard_lines+=1
            elif raw.strip().startswith(b'running '):
                match=re.fullmatch(rb'running ([0-9]+) tests\r?',raw.strip())
                require(match is not None and self.running_count is None and int(match[1])==len(self.names),'RUNNING_COUNT')
                self.running_count=int(match[1])
            elif raw.startswith(b'test result: '):self.summary_seen=True
            elif raw.strip():self.nonstandard_lines+=1  # Never save arbitrary raw lines.
        require(len(self.pending)<=4096,'PENDING_BOUND');self._start(bytes(self.pending),seconds)

    def _start(self,raw,seconds):
        match=re.match(rb'^test ([A-Za-z0-9_:]+) \.\.\. ',raw)
        if not match:return
        name=match[1].decode('ascii');require(name in self.names and self.running_count==len(self.names),'CASE_SCOPE')
        if self.active:
            require(self.active['case']==name,'CONCURRENT_CASE');return
        require(name not in self.started and len(self.started)<len(self.names),'DUPLICATE_CASE')
        self.started.add(name);self.active=dict(case=name,started_seconds=seconds)

    def snapshot(self,seconds):
        require(type(seconds) in (float,int) and math.isfinite(seconds) and seconds>=0,'SNAPSHOT')
        active=dict(self.active,observed_wall_seconds=max(0,seconds-self.active['started_seconds'])) if self.active else None
        return dict(running_count=self.running_count,started_case_count=len(self.started),completed_case_count=len(self.completed),
            completed=list(self.completed),active=active,summary_seen=self.summary_seen,nonstandard_line_count=self.nonstandard_lines,
            observed_times_are_pipe_arrival_wall_times=True,raw_test_output_saved=False)


def churn_summary(pids,baseline):
    current=group.pid_sets(pids);changed=[];unavailable=0
    for name,members in current.items():
        if members is None:unavailable+=1;continue
        old=baseline.get(name)
        if old==members:continue
        known=old is not None
        changed.append(dict(role=group.old.role(name),current_instance_count=len(members),
            identity_granularity='pid' if len(members)==1 else 'group',pid=next(iter(members)) if len(members)==1 else None,
            baseline_known=known,added_pid_count=len(members-old) if known else None,
            removed_pid_count=len(old-members) if known else None,cpu_attribution_unavailable=True))
    changed.sort(key=lambda r:(-r['current_instance_count'],r['role'],r['pid'] or 0))
    return dict(changed_group_count=len(changed),changed_current_instance_count=sum(r['current_instance_count'] for r in changed),
        unavailable_identity_group_count=unavailable,top_changed_groups=changed[:4],identity_only_not_CPU_or_cause=True)


def valid_churn(row):
    require(type(row) is dict and set(row)=={'changed_group_count','changed_current_instance_count',
        'unavailable_identity_group_count','top_changed_groups','identity_only_not_CPU_or_cause'},'CHURN_KEYS')
    for key in ('changed_group_count','changed_current_instance_count','unavailable_identity_group_count'):
        require(type(row[key]) is int and 0<=row[key]<=group.old.MAX_ITEMS,'CHURN_COUNTS')
    require(row['identity_only_not_CPU_or_cause'] is True and type(row['top_changed_groups']) is list
        and len(row['top_changed_groups'])==min(4,row['changed_group_count']),'CHURN_SCOPE')
    for item in row['top_changed_groups']:
        require(type(item) is dict and set(item)=={'role','current_instance_count','identity_granularity','pid','baseline_known',
            'added_pid_count','removed_pid_count','cpu_attribution_unavailable'},'CHURN_ITEM_KEYS')
        require(item['role'] in group.old.ROLES and type(item['current_instance_count']) is int
            and 1<=item['current_instance_count']<=group.old.MAX_ITEMS and type(item['baseline_known']) is bool
            and item['cpu_attribution_unavailable'] is True,'CHURN_ITEM_SCOPE')
        if item['current_instance_count']==1:
            require(item['identity_granularity']=='pid' and type(item['pid']) is int and 1<=item['pid']<=0xffffffff,'CHURN_PID')
        else:require(item['identity_granularity']=='group' and item['pid'] is None,'CHURN_GROUP_NOT_FAKE_PID')
        for key in ('added_pid_count','removed_pid_count'):
            value=item[key]
            require((type(value) is int and 0<=value<=group.old.MAX_ITEMS) if item['baseline_known'] else value is None,'CHURN_BASELINE_UNKNOWN')
    return row


class ChurnObserver(BASE_GROUP):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.last_churn=None
    def collect(self,owned=()):
        require(not self.closed and self.query.value,'QUERY_CLOSED')
        require(group.old.status(self.api.PdhCollectQueryData(self.query))==0,'COLLECT')
        pids=self.array(self.handles[1])
        if self.baseline is None:self.baseline=group.pid_sets(pids);return None
        cpu=self.array(self.handles[0]);self.last_churn=valid_churn(churn_summary(pids,self.baseline))
        result,self.baseline=group.select(cpu,pids,self.baseline,self.processors,owned);return result
