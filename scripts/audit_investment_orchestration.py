"""Audit G.17 Section 2B orchestration artifacts."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

def load_runtime():
    path=Path(__file__).with_name("run_investment_orchestrator.py")
    spec=importlib.util.spec_from_file_location("g17_runtime",path)
    if spec is None or spec.loader is None: raise RuntimeError("Cannot load runtime")
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod
runtime=load_runtime()

def audit(report: dict) -> dict:
    required={"schema_version","run_id","decision_id","status","jobs","safety","record_hash","previous_record_hash"}
    missing=required-set(report)
    if missing: raise ValueError(f"Missing fields: {sorted(missing)}")
    s=report["safety"]
    if s.get("paper_only") is not True or s.get("live_execution") is not False: raise ValueError("Safety boundary violated")
    if s.get("credentials_used") is not False or s.get("shell_execution") is not False: raise ValueError("Unsafe capability reported")
    seen=set(); completed=set()
    for j in report["jobs"]:
        jid=j.get("job_id")
        if not jid or jid in seen: raise ValueError("Duplicate or missing job_id")
        if any(d not in completed for d in j.get("depends_on",[])): raise ValueError("Out-of-order dependency")
        seen.add(jid); completed.add(jid)
    if report["record_hash"] != runtime.record_hash(report): raise ValueError("Report hash mismatch")
    return {"success":True,"decision_id":report["decision_id"],"status":report["status"],
            "job_count":len(report["jobs"]),"record_hash_valid":True,"paper_only":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("output/investment_orchestration/latest_report.json"))
    p.add_argument("--history",type=Path,default=Path("output/investment_orchestration/history.jsonl"))
    p.add_argument("--skip-history",action="store_true"); a=p.parse_args()
    try:
        report=json.loads(a.report.read_text(encoding="utf-8")); result=audit(report)
        if not a.skip_history:
            records=runtime.read_history(a.history); runtime.validate_history(records)
            if not records or records[-1]["record_hash"]!=report["record_hash"]: raise ValueError("History/latest mismatch")
            result["history_chain_valid"]=True; result["history_records"]=len(records)
    except (OSError,ValueError,runtime.OrchestrationError) as e:
        print(json.dumps({"success":False,"error":str(e)},indent=2)); return 1
    print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
