"""Broker-neutral Atlas paper execution plane."""

from atlas.investment.execution.account_store import (
    account_from_mapping,
    load_paper_account,
    write_paper_account,
)
from atlas.investment.execution.contracts import (
    AccountSnapshot,
    FillRecord,
    OrderIntent,
    OrderRecord,
    PositionSnapshot,
    RiskDecision,
    RiskLimits,
)
from atlas.investment.execution.dashboard import (
    build_paper_execution_dashboard_model,
)
from atlas.investment.execution.instruments import (
    INSTRUMENT_REGISTRY,
    InstrumentSpec,
    build_instrument_universe_report,
    get_instrument,
    list_instruments,
    normalize_symbol,
    require_paper_instrument,
)
from atlas.investment.execution.ledger import (
    apply_fill,
)
from atlas.investment.execution.lifecycle import (
    LifecycleRecord,
    LifecycleTransition,
    PaperOrderLifecycleStore,
)
from atlas.investment.execution.paper_broker import (
    PaperBroker,
    PaperBrokerConfig,
)
from atlas.investment.execution.portfolio_bridge import (
    PortfolioTarget,
    RebalanceLine,
    RebalancePolicy,
    build_portfolio_intent_plan,
    load_portfolio_targets,
)
from atlas.investment.execution.provenance import (
    read_execution_events,
    record_execution_events,
    validate_execution_provenance,
)
from atlas.investment.execution.reconciliation import (
    reconcile_paper_execution,
)
from atlas.investment.execution.risk import (
    evaluate_order_intent,
)
from atlas.investment.execution.service import (
    run_paper_execution,
)
from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)

__all__ = [
    "AccountSnapshot",
    "FillRecord",
    "OrderIntent",
    "OrderRecord",
    "LifecycleRecord",
    "LifecycleTransition",
    "InstrumentSpec",
    "INSTRUMENT_REGISTRY",
    "PaperOrderLifecycleStore",
    "PaperBroker",
    "PaperBrokerConfig",
    "PortfolioTarget",
    "RebalanceLine",
    "RebalancePolicy",
    "PositionSnapshot",
    "RiskDecision",
    "RiskLimits",
    "account_from_mapping",
    "apply_fill",
    "build_instrument_universe_report",
    "build_paper_execution_dashboard_model",
    "build_portfolio_intent_plan",
    "evaluate_order_intent",
    "get_instrument",
    "list_instruments",
    "load_paper_account",
    "load_portfolio_targets",
    "normalize_symbol",
    "read_execution_events",
    "reconcile_paper_execution",
    "require_paper_instrument",
    "record_execution_events",
    "run_paper_execution",
    "run_shadow_cycle",
    "validate_execution_provenance",
    "write_paper_account",
]
