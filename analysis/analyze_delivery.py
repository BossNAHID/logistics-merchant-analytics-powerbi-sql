#!/usr/bin/env python3
"""Run the small statistics exercise used in the portfolio report.

This is a descriptive check on synthetic data, not a claim that slow delivery
causes returns. Results go to analysis/results/ by default.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def hub_delivery_relationship(
    orders: pd.DataFrame, hubs: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Summarize hub-level delivery and return outcomes, then fit a simple line."""
    hub_results = (
        orders.groupby("hub_id", as_index=False)
        .agg(
            order_count=("order_id", "count"),
            returned_orders=("status", lambda status: status.eq("Returned").sum()),
            average_delivery_days=("delivery_days", "mean"),
        )
        .merge(
            hubs[["hub_id", "hub_name", "division"]],
            on="hub_id",
            how="left",
            validate="one_to_one",
        )
    )
    hub_results["return_rate"] = (
        hub_results["returned_orders"] / hub_results["order_count"]
    )
    hub_results = hub_results[
        [
            "hub_id",
            "hub_name",
            "division",
            "order_count",
            "returned_orders",
            "average_delivery_days",
            "return_rate",
        ]
    ].sort_values("hub_id")

    usable = hub_results.dropna(subset=["average_delivery_days", "return_rate"])
    x = usable["average_delivery_days"].to_numpy(dtype=float)
    y = usable["return_rate"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, deg=1)
    correlation = float(np.corrcoef(x, y)[0, 1])
    fitted = slope * x + intercept
    residual_sum = float(np.square(y - fitted).sum())
    total_sum = float(np.square(y - y.mean()).sum())
    r_squared = 1 - residual_sum / total_sum if total_sum else 0.0

    summary = {
        "regression_level": "one row per hub",
        "hub_count": len(usable),
        "hub_slope_return_rate_per_day": float(slope),
        "hub_intercept": float(intercept),
        "hub_correlation": correlation,
        "hub_r_squared": float(r_squared),
        "regression_caveat": (
            "This is an association in synthetic hub-level data, not a causal estimate. "
            "Hub mix and shipment volume can affect the comparison."
        ),
    }
    return hub_results, summary


def moving_average_forecast(orders: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    """Use the latest three complete months as a flat, easy-to-explain baseline."""
    monthly_orders = (
        orders.assign(
            order_month=pd.to_datetime(orders["order_date"])
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        .groupby("order_month")
        .size()
        .sort_index()
    )
    if len(monthly_orders) < 3:
        raise ValueError("At least three months of orders are needed for this forecast")

    baseline = float(monthly_orders.tail(3).mean())
    first_forecast_month = monthly_orders.index[-1] + pd.offsets.MonthBegin(1)
    forecast_months = pd.date_range(first_forecast_month, periods=horizon, freq="MS")
    return pd.DataFrame(
        {
            "month": forecast_months.strftime("%Y-%m-%d"),
            "forecast_orders": [round(baseline, 1)] * horizon,
            "method": ["flat 3-month moving average"] * horizon,
        }
    )


def issue_resolution_summary(issues: pd.DataFrame) -> pd.DataFrame:
    """Summarize resolved tickets only; still-open tickets have no duration yet."""
    resolved = issues.loc[issues["status"].eq("Resolved")].copy()
    resolved["resolution_hours"] = (
        pd.to_datetime(resolved["resolved_at"]) - pd.to_datetime(resolved["opened_at"])
    ).dt.total_seconds() / 3_600
    return (
        resolved.groupby("issue_type", as_index=False)
        .agg(
            resolved_issues=("issue_id", "count"),
            average_resolution_hours=("resolution_hours", "mean"),
            median_resolution_hours=("resolution_hours", "median"),
        )
        .sort_values("average_resolution_hours", ascending=False)
    )


def analyze(data_dir: Path, output_dir: Path) -> dict[str, Any]:
    orders = pd.read_csv(
        data_dir / "orders.csv", parse_dates=["order_date", "delivery_date"]
    )
    hubs = pd.read_csv(data_dir / "hubs.csv")
    issues = pd.read_csv(data_dir / "issues.csv")

    hub_results, summary = hub_delivery_relationship(orders, hubs)
    forecast = moving_average_forecast(orders)
    resolutions = issue_resolution_summary(issues)
    output_dir.mkdir(parents=True, exist_ok=True)
    hub_results.to_csv(output_dir / "hub_delivery_return.csv", index=False)
    forecast.to_csv(output_dir / "monthly_forecast.csv", index=False)
    resolutions.to_csv(output_dir / "issue_resolution_by_type.csv", index=False)

    summary.update(
        {
            "orders_in_sample": len(orders),
            "forecast_method": "flat 3-month moving average",
            "forecast_baseline_orders": float(forecast["forecast_orders"].iloc[0]),
            "forecast_horizon_months": len(forecast),
            "forecast_caveat": "A short baseline, not a seasonal or capacity-aware forecast.",
        }
    )
    (output_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=project_root / "data")
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent / "results"
    )
    args = parser.parse_args()

    summary = analyze(args.data_dir, args.output_dir)
    print(f"Wrote analysis results to {args.output_dir}")
    print(f"Hub-level correlation: {summary['hub_correlation']:.2f}")
    print(
        f"Three-month baseline: {summary['forecast_baseline_orders']:,.0f} orders/month"
    )


if __name__ == "__main__":
    main()
