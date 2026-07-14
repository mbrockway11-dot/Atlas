from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("g17_allow",ROOT/"scripts"/"run_investment_orchestrator.py")
rt=importlib.util.module_from_spec(s); sys.modules[s.name]=rt; s.loader.exec_module(rt)

def wrap(job,**kw): return rt.OrchestrationPlan("d",(job,),**kw)

def test_non_allowlisted_rejected():
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(wrap(rt.OrchestrationJob("x","scripts/x.py")),{"scripts/y.py"})

@pytest.mark.parametrize("path",["../x.py","scripts/../../x.py","C:/x.py","scripts/x.ps1"])
def test_unsafe_paths_rejected(path):
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(wrap(rt.OrchestrationJob("x",path)),{path})

@pytest.mark.parametrize("arg",["x;y","x|y","$(whoami)","x>y","a\nb"])
def test_shell_arguments_rejected(arg):
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(wrap(rt.OrchestrationJob("x","scripts/x.py",args=(arg,))),{"scripts/x.py"})

def test_duplicate_ids_rejected():
    p=rt.OrchestrationPlan("d",(rt.OrchestrationJob("x","scripts/x.py"),rt.OrchestrationJob("x","scripts/y.py")))
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(p,{"scripts/x.py","scripts/y.py"})

def test_cycle_rejected():
    p=rt.OrchestrationPlan("d",(rt.OrchestrationJob("a","scripts/a.py",depends_on=("b",)),
        rt.OrchestrationJob("b","scripts/b.py",depends_on=("a",))))
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(p,{"scripts/a.py","scripts/b.py"})

@pytest.mark.parametrize("kw",[{"paper_only":False},{"live_execution":True},{"credentials_used":True},
                               {"shell_execution":True},{"execution_mode":"AUTONOMOUS_LIVE"}])
def test_safety_violations_rejected(kw):
    with pytest.raises(rt.PlanValidationError):
        rt.validate_plan(wrap(rt.OrchestrationJob("x","scripts/x.py"),**kw),{"scripts/x.py"})
