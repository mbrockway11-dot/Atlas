from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s)
    sys.modules[name]=m; s.loader.exec_module(m); return m
rt=load("g17_test_runtime",ROOT/"scripts"/"run_investment_orchestrator.py")
audit=load("g17_test_audit",ROOT/"scripts"/"audit_investment_orchestration.py")

def plan(decision="d1"):
    return rt.OrchestrationPlan(decision,(rt.OrchestrationJob("a","scripts/a.py"),
        rt.OrchestrationJob("b","scripts/b.py",depends_on=("a",))))
ALLOW={"scripts/a.py","scripts/b.py"}

def test_dry_run_and_audit(tmp_path):
    r=rt.run(plan(),repo_root=tmp_path,dry_run=True,allowlist=ALLOW)
    assert r["status"]=="SUCCEEDED"
    assert [x["status"] for x in r["jobs"]]==["DRY_RUN","DRY_RUN"]
    assert audit.audit(r)["record_hash_valid"]

def test_paper_execution_and_dependency(tmp_path):
    (tmp_path/"scripts").mkdir()
    (tmp_path/"scripts/a.py").write_text("print('a')\n")
    (tmp_path/"scripts/b.py").write_text("print('b')\n")
    r=rt.run(plan("paper"),repo_root=tmp_path,dry_run=False,allowlist=ALLOW)
    assert r["status"]=="SUCCEEDED"
    assert all(x["status"]=="SUCCEEDED" for x in r["jobs"])

def test_failed_job_blocks_dependency(tmp_path):
    (tmp_path/"scripts").mkdir()
    (tmp_path/"scripts/a.py").write_text("raise SystemExit(3)\n")
    (tmp_path/"scripts/b.py").write_text("print('b')\n")
    r=rt.run(plan("fail"),repo_root=tmp_path,dry_run=False,allowlist=ALLOW)
    assert [x["status"] for x in r["jobs"]]==["FAILED","BLOCKED"]

def test_duplicate_decision_rejected(tmp_path):
    rt.run(plan("dup"),repo_root=tmp_path,dry_run=True,allowlist=ALLOW)
    with pytest.raises(rt.DuplicateDecisionError):
        rt.run(plan("dup"),repo_root=tmp_path,dry_run=True,allowlist=ALLOW)

def test_history_tamper_detected(tmp_path):
    rt.run(plan("tamper"),repo_root=tmp_path,dry_run=True,allowlist=ALLOW)
    p=tmp_path/"output/investment_orchestration/history.jsonl"
    d=json.loads(p.read_text()); d["status"]="FAILED"; p.write_text(json.dumps(d)+"\n")
    with pytest.raises(rt.OrchestrationError):
        rt.validate_history(rt.read_history(p))
