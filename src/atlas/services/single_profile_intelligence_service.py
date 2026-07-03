"""Single Profile Intelligence service.

This service is the integration backbone for Atlas dashboard pages.
It builds one canonical payload from compiler, temporal runtime, graph,
fingerprint, and population-ready outputs.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from atlas.core.compiler import compile_profile
from atlas.fingerprint import build_structural_fingerprint
from atlas.graph import (
    build_graph_activation,
    build_temporal_graph,
    compute_graph_metrics,
    propagate_activation,
)
from atlas.ive import build_graph_backed_identity_vector
from atlas.temporal_runtime import TemporalRuntimeEngine, evaluate_forecast


SINGLE_PROFILE_INTELLIGENCE_VERSION = "0.1"


def build_single_profile_intelligence_payload(
    profile_key: str,
    *,
    evaluation_date: str | None = None,
    forecast_days: int = 7,
) -> dict[str, Any]:
    """Build complete single-profile intelligence payload."""
    resolved_date = evaluation_date or date.today().isoformat()

    warnings: list[str] = []
    errors: list[str] = []

    payload: dict[str, Any] = {
        "version": SINGLE_PROFILE_INTELLIGENCE_VERSION,
        "profile_key": profile_key,
        "evaluation_date": resolved_date,
        "success": False,
        "css": {},
        "temporal_runtime": {},
        "forecast": {},
        "semantic_graph": {},
        "graph_metrics": {},
        "graph_activation": {},
        "graph_propagation": {},
        "structural_fingerprint": {},
        "ive": {
            "status": "not_integrated",
        },
        "population": {
            "status": "not_integrated",
        },
        "exports": {},
        "warnings": warnings,
        "errors": errors,
    }

    try:
        css_obj = compile_profile(profile_key)
        css = css_obj.to_dict()
        payload["css"] = css
    except Exception as exc:  # noqa: BLE001
        errors.append(f"CSS compilation failed: {exc}")
        return payload

    try:
        runtime_result = TemporalRuntimeEngine().evaluate(
            profile_key=profile_key,
            css=css,
            evaluation_date=resolved_date,
        )
        payload["temporal_runtime"] = runtime_result.to_dict()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Temporal runtime failed: {exc}")
        runtime_result = None

    try:
        forecast = evaluate_forecast(
            profile_key=profile_key,
            css=css,
            start_date=resolved_date,
            days=forecast_days,
        )
        payload["forecast"] = forecast.to_dict()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Forecast failed: {exc}")

    try:
        graph = build_temporal_graph(
            profile_key=profile_key,
            css=css,
            runtime_result=(
                runtime_result.to_dict()
                if runtime_result is not None
                else None
            ),
        )
        payload["semantic_graph"] = graph.to_dict()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Semantic graph failed: {exc}")
        graph = None

    if graph is not None:
        try:
            metrics = compute_graph_metrics(graph)
            payload["graph_metrics"] = metrics.to_dict()
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Graph metrics failed: {exc}")
            metrics = None

        try:
            activation = build_graph_activation(graph)
            payload["graph_activation"] = activation.to_dict()
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Graph activation failed: {exc}")
            activation = None

        if activation is not None:
            try:
                propagation = propagate_activation(
                    graph=graph,
                    activation=activation,
                )
                payload["graph_propagation"] = propagation.to_dict()
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Graph propagation failed: {exc}")
                propagation = None
        else:
            propagation = None

        if metrics is not None and activation is not None and propagation is not None:
            try:
                fingerprint = build_structural_fingerprint(
                    profile_key=profile_key,
                    metrics=metrics,
                    activation=activation,
                    propagation=propagation,
                )
                payload["structural_fingerprint"] = fingerprint.to_dict()

                try:
                    ive_vector = build_graph_backed_identity_vector(
                        profile_key=profile_key,
                        metrics=metrics,
                        activation=activation,
                        propagation=propagation,
                        fingerprint=fingerprint,
                    )
                    payload["ive"] = ive_vector.to_dict()
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"IVE graph bridge failed: {exc}")
                    payload["ive"] = {
                        "status": "failed",
                        "error": str(exc),
                    }

            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Structural fingerprint failed: {exc}")

    payload["exports"] = {
        "profile_key": profile_key,
        "evaluation_date": resolved_date,
        "payload_version": SINGLE_PROFILE_INTELLIGENCE_VERSION,
    }

    payload["success"] = not errors

    return payload
