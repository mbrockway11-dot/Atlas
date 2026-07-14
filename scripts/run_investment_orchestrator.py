"""G.17 Section 2B paper-only investment orchestrator."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, tempfile, time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "g17.orchestration.v1"
DEFAULT_OUTPUT_DIR = Path("output/investment_orchestration")
DEFAULT_SCRIPT_ALLOWLIST = frozenset({
    "scripts/build_alpha_portfolio.py",
    "scripts/audit_investment_architecture.py",
    "scripts/audit_investment_scheduler.py",
    "scripts/build_investment_scheduler_decision.py",
    "scripts/run_investment_paper_execution.py",
})
FORBIDDEN = ("&","|",";",">","<","`","$(","${","\n","\r")

class OrchestrationError(RuntimeError): pass
class PlanValidationError(OrchestrationError): pass
class DuplicateDecisionError(OrchestrationError): pass

@dataclass(frozen=True)
class OrchestrationJob:
    job_id: str
    script: str
    args: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    timeout_seconds: int = 300
    @classmethod
    def from_mapping(cls, v: Mapping[str, Any]) -> "OrchestrationJob":
        return cls(str(v["job_id"]), str(v["script"]).replace("\\","/"),
                   tuple(map(str,v.get("args",()))),
                   tuple(map(str,v.get("depends_on",()))),
                   int(v.get("timeout_seconds",300)))

@dataclass(frozen=True)
class OrchestrationPlan:
    decision_id: str
    jobs: tuple[OrchestrationJob, ...]
    paper_only: bool = True
    live_execution: bool = False
    credentials_used: bool = False
    shell_execution: bool = False
    approval_required: bool = False
    execution_mode: str = "DRY_RUN"
    @classmethod
    def from_mapping(cls, v: Mapping[str, Any]) -> "OrchestrationPlan":
        return cls(str(v["decision_id"]),
                   tuple(OrchestrationJob.from_mapping(x) for x in v.get("jobs",())),
                   bool(v.get("paper_only",True)),
                   bool(v.get("live_execution",False)),
                   bool(v.get("credentials_used",False)),
                   bool(v.get("shell_execution",False)),
                   bool(v.get("approval_required",False)),
                   str(v.get("execution_mode","DRY_RUN")))

@dataclass
class JobResult:
    job_id: str
    script: str
    status: str
    command: list[str]
    started_at: str
    finished_at: str
    elapsed_ms: int
    return_code: int | None
    stdout_summary: str
    stderr_summary: str
    depends_on: list[str] = field(default_factory=list)

def now() -> str: return datetime.now(timezone.utc).isoformat()
def canon(v: Any) -> str: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def hash_json(v: Any) -> str: return hashlib.sha256(canon(v).encode()).hexdigest()

def atomic_json(path: Path, payload: Mapping[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(payload,f,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def record_hash(record: Mapping[str,Any]) -> str:
    v=dict(record); v.pop("record_hash",None); return hash_json(v)

def read_history(path: Path) -> list[dict[str,Any]]:
    if not path.exists(): return []
    out=[]
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: v=json.loads(line)
        except json.JSONDecodeError as e: raise OrchestrationError(f"Malformed history line {i}") from e
        if not isinstance(v,dict): raise OrchestrationError(f"History line {i} is not an object")
        out.append(v)
    return out

def validate_history(records: Sequence[Mapping[str,Any]]) -> None:
    prev=""
    for i,r in enumerate(records):
        if r.get("previous_record_hash","") != prev: raise OrchestrationError(f"History chain mismatch at {i}")
        expected=record_hash(r)
        if r.get("record_hash") != expected: raise OrchestrationError(f"History hash mismatch at {i}")
        prev=expected

def ordered(jobs: Sequence[OrchestrationJob]) -> list[OrchestrationJob]:
    by={j.job_id:j for j in jobs}; left={j.job_id:set(j.depends_on) for j in jobs}; out=[]
    while left:
        ready=sorted(k for k,v in left.items() if not v)
        if not ready: raise PlanValidationError("Dependency cycle detected")
        for k in ready:
            out.append(by[k]); left.pop(k)
            for deps in left.values(): deps.discard(k)
    return out

def validate_plan(plan: OrchestrationPlan, allowlist: Iterable[str]=DEFAULT_SCRIPT_ALLOWLIST) -> None:
    allowed={x.replace("\\","/") for x in allowlist}
    if not plan.decision_id.strip() or not plan.jobs: raise PlanValidationError("decision_id and jobs are required")
    if not plan.paper_only or plan.live_execution or plan.credentials_used or plan.shell_execution:
        raise PlanValidationError("Paper-only safety boundary violated")
    if plan.execution_mode not in {"RESEARCH","DRY_RUN","PAPER"}: raise PlanValidationError("Unsupported execution mode")
    ids=[j.job_id for j in plan.jobs]
    if len(ids)!=len(set(ids)): raise PlanValidationError("Duplicate job_id")
    idset=set(ids)
    for j in plan.jobs:
        p=Path(j.script)
        if not j.job_id.strip() or p.is_absolute() or ".." in p.parts or p.suffix.lower()!=".py":
            raise PlanValidationError(f"Unsafe script path: {j.script}")
        if j.script not in allowed: raise PlanValidationError(f"Script is not allowlisted: {j.script}")
        if not 1 <= j.timeout_seconds <= 3600: raise PlanValidationError("Invalid timeout")
        if j.job_id in j.depends_on or set(j.depends_on)-idset: raise PlanValidationError("Invalid dependency")
        for a in j.args:
            if "\x00" in a or any(t in a for t in FORBIDDEN): raise PlanValidationError(f"Unsafe argument: {a!r}")
    ordered(plan.jobs)

def run(plan: OrchestrationPlan, *, repo_root: Path, output_dir: Path=DEFAULT_OUTPUT_DIR,
        dry_run: bool=True, allowlist: Iterable[str]=DEFAULT_SCRIPT_ALLOWLIST) -> dict[str,Any]:
    validate_plan(plan,allowlist)
    out=(repo_root/output_dir).resolve() if not output_dir.is_absolute() else output_dir
    latest,checkpoint,history=out/"latest_report.json",out/"checkpoint.json",out/"history.jsonl"
    records=read_history(history); validate_history(records)
    if any(r.get("decision_id")==plan.decision_id and r.get("status")=="SUCCEEDED" for r in records):
        raise DuplicateDecisionError(f"Decision already completed: {plan.decision_id}")
    started=now(); t0=time.perf_counter(); run_id=hash_json({"decision":plan.decision_id,"started":started})[:20]
    results=[]; statuses={}
    for j in ordered(plan.jobs):
        if any(statuses.get(d) not in {"SUCCEEDED","DRY_RUN"} for d in j.depends_on):
            status,rc,stdout,stderr="BLOCKED",None,"","Dependency failed"
        elif dry_run:
            status,rc,stdout,stderr="DRY_RUN",None,"",""
        else:
            script=repo_root/j.script
            if not script.is_file(): raise OrchestrationError(f"Missing allowlisted script: {j.script}")
            try:
                cp=subprocess.run([sys.executable,str(script),*j.args],cwd=repo_root,capture_output=True,
                                  text=True,timeout=j.timeout_seconds,check=False,shell=False)
                status="SUCCEEDED" if cp.returncode==0 else "FAILED"; rc=cp.returncode
                stdout,stderr=cp.stdout[:4000],cp.stderr[:4000]
            except subprocess.TimeoutExpired as e:
                status,rc,stdout,stderr="TIMED_OUT",None,str(e.stdout or "")[:4000],str(e.stderr or "")[:4000]
        result=asdict(JobResult(j.job_id,j.script,status,[sys.executable,str(repo_root/j.script),*j.args],
                                started,now(),0,rc,stdout,stderr,list(j.depends_on)))
        results.append(result); statuses[j.job_id]=status
        atomic_json(checkpoint,{"schema_version":SCHEMA_VERSION,"run_id":run_id,"decision_id":plan.decision_id,
                                "updated_at":now(),"completed_jobs":results,"paper_only":True,"live_execution":False})
    status="SUCCEEDED" if all(x["status"] in {"SUCCEEDED","DRY_RUN"} for x in results) else "FAILED"
    report={"schema_version":SCHEMA_VERSION,"run_id":run_id,"decision_id":plan.decision_id,"status":status,
            "dry_run":dry_run,"started_at":started,"finished_at":now(),
            "elapsed_ms":int((time.perf_counter()-t0)*1000),"jobs":results,
            "safety":{"paper_only":True,"live_execution":False,"credentials_used":False,
                      "shell_execution":False,"commands_executed":not dry_run,
                      "approval_required":plan.approval_required,
                      "execution_mode":"DRY_RUN" if dry_run else "PAPER"},
            "duplicate_prevention":{"enabled":True,"decision_id":plan.decision_id},
            "previous_record_hash":records[-1]["record_hash"] if records else "","record_hash":""}
    report["record_hash"]=record_hash(report)
    atomic_json(latest,report); out.mkdir(parents=True,exist_ok=True)
    with history.open("a",encoding="utf-8") as f: f.write(canon(report)+"\n")
    atomic_json(checkpoint,{**report,"updated_at":now()})
    return report

def main(argv: Sequence[str]|None=None) -> int:
    p=argparse.ArgumentParser(); p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--repo-root",type=Path,default=Path.cwd()); p.add_argument("--output-dir",type=Path,default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--execute-paper",action="store_true"); a=p.parse_args(argv)
    try:
        payload=json.loads(a.plan.read_text(encoding="utf-8"))
        report=run(OrchestrationPlan.from_mapping(payload),repo_root=a.repo_root.resolve(),
                   output_dir=a.output_dir,dry_run=not a.execute_paper)
    except (OSError,ValueError,OrchestrationError) as e:
        print(json.dumps({"success":False,"error":str(e)},indent=2)); return 2
    print(json.dumps({"success":True,"report":report},indent=2)); return 0 if report["status"]=="SUCCEEDED" else 1
if __name__=="__main__": raise SystemExit(main())
