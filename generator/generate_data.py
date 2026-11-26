#!/usr/bin/env python3
"""Create a repeatable, fictional parcel-delivery dataset for the portfolio project.

Run from the repository root with:
    python generator/generate_data.py

The defaults recreate the one-year, roughly 60,000-order dataset. Smaller runs
are useful when checking changes to the generator:
    python generator/generate_data.py --target-orders 4500 --seed 731
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

FIRST_MONTH = "2025-11"
LAST_MONTH = "2026-10"
MERCHANT_COUNT = 300
DEFAULT_ORDER_COUNT = 60_000

CATEGORIES = [
    "Fashion",
    "Electronics",
    "Beauty & Cosmetics",
    "Grocery",
    "Home & Living",
    "Books & Stationery",
    "Gadgets & Accessories",
    "Food & Beverage",
]

CATEGORY_WEIGHTS = [0.22, 0.10, 0.15, 0.08, 0.10, 0.07, 0.14, 0.14]
AVERAGE_COD_BY_CATEGORY = {
    "Fashion": 1_400,
    "Electronics": 5_200,
    "Beauty & Cosmetics": 1_100,
    "Grocery": 900,
    "Home & Living": 2_600,
    "Books & Stationery": 650,
    "Gadgets & Accessories": 1_500,
    "Food & Beverage": 800,
}

HUBS = [
    ("Dhaka Central", "Dhaka", "Dhaka", 1.3, 0.04, 22),
    ("Uttara", "Dhaka", "Dhaka", 1.4, 0.04, 12),
    ("Mirpur", "Dhaka", "Dhaka", 1.5, 0.05, 12),
    ("Gazipur", "Gazipur", "Dhaka", 1.9, 0.06, 7),
    ("Narayanganj", "Narayanganj", "Dhaka", 1.8, 0.06, 6),
    ("Chattogram Port", "Chattogram", "Chattogram", 2.2, 0.07, 12),
    ("Sylhet Sadar", "Sylhet", "Sylhet", 2.8, 0.09, 5),
    ("Rajshahi Sadar", "Rajshahi", "Rajshahi", 2.9, 0.09, 5),
    ("Khulna Sadar", "Khulna", "Khulna", 3.0, 0.10, 5),
    ("Barishal Sadar", "Barishal", "Barishal", 3.6, 0.14, 4),
    ("Rangpur Sadar", "Rangpur", "Rangpur", 3.3, 0.12, 4),
    ("Cumilla", "Cumilla", "Chattogram", 2.4, 0.07, 6),
]

NAME_PREFIXES = [
    "Dhaka",
    "Bangla",
    "Padma",
    "Meghna",
    "Jamuna",
    "Shapla",
    "Nakshi",
    "Deshi",
    "Urban",
    "Prime",
    "Royal",
    "Smart",
    "Fresh",
    "Trendy",
    "Golden",
    "Nova",
    "Apex",
    "Rupa",
    "Shotti",
    "Mukto",
    "Surma",
    "Karnaphuli",
    "Teesta",
    "Madhumati",
    "Sundarban",
    "Ruposhi",
    "Alo",
    "Neel",
    "Sabuj",
    "Tarar",
]
NAME_SUFFIXES = [
    "Mart",
    "Bazar",
    "Store",
    "Collection",
    "Hub",
    "Corner",
    "House",
    "Traders",
    "Point",
    "Lifestyle",
    "Shop",
    "Zone",
]

ISSUE_TYPES = [
    "Rider Not Responding",
    "Wrong Address",
    "Customer Unreachable",
    "Parcel Damaged",
    "Delayed Delivery",
    "COD Mismatch",
    "Parcel Lost",
    "Return Dispute",
]
ISSUE_TYPE_WEIGHTS = [0.17, 0.14, 0.20, 0.08, 0.22, 0.08, 0.03, 0.08]
ISSUE_RESOLUTION_HOURS = {
    "Rider Not Responding": 6,
    "Wrong Address": 10,
    "Customer Unreachable": 8,
    "Parcel Damaged": 48,
    "Delayed Delivery": 14,
    "COD Mismatch": 36,
    "Parcel Lost": 96,
    "Return Dispute": 30,
}

SEASONAL_VOLUME = {
    "2025-11": 1.15,
    "2025-12": 1.25,
    "2026-01": 0.95,
    "2026-02": 0.92,
    "2026-03": 1.20,
    "2026-04": 0.95,
    "2026-05": 1.10,
    "2026-06": 0.98,
    "2026-07": 0.97,
    "2026-08": 1.00,
    "2026-09": 1.02,
    "2026-10": 1.08,
}


def _make_reference_tables(
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    kams = pd.DataFrame(
        {
            "kam_id": [f"K{number:02d}" for number in range(1, 9)],
            "kam_name": [
                "Rafiq Hasan",
                "Tania Akter",
                "Imran Hossain",
                "Nusrat Jahan",
                "Sabbir Ahmed",
                "Farhana Islam",
                "Mahmud Karim",
                "Sadia Rahman",
            ],
            "team": ["Key Accounts"] * 5 + ["Growth"] * 3,
        }
    )

    hubs = pd.DataFrame(
        HUBS,
        columns=[
            "hub_name",
            "district",
            "division",
            "base_days",
            "base_fail_rate",
            "volume_weight",
        ],
    )
    hubs.insert(0, "hub_id", [f"H{number:02d}" for number in range(1, len(hubs) + 1)])

    # Sampling from a sorted list keeps the output stable across Python processes.
    possible_names = sorted(
        f"{prefix} {suffix}" for prefix in NAME_PREFIXES for suffix in NAME_SUFFIXES
    )
    merchant_names = rng.choice(possible_names, size=MERCHANT_COUNT, replace=False)
    onboarding_start = pd.Timestamp("2024-01-01")
    onboarding_end = pd.Period(LAST_MONTH, freq="M").end_time.normalize()
    onboarding_span = (onboarding_end - onboarding_start).days
    onboarding_dates = onboarding_start + pd.to_timedelta(
        rng.integers(0, onboarding_span, size=MERCHANT_COUNT), unit="D"
    )

    merchants = pd.DataFrame(
        {
            "merchant_id": [
                f"M{number:04d}" for number in range(1, MERCHANT_COUNT + 1)
            ],
            "merchant_name": merchant_names,
            "category": rng.choice(CATEGORIES, size=MERCHANT_COUNT, p=CATEGORY_WEIGHTS),
            "onboarding_date": onboarding_dates,
            "kam_id": rng.choice(kams["kam_id"], size=MERCHANT_COUNT),
        }
    )
    return kams, hubs, merchants


def _merchant_monthly_volume(
    merchants: pd.DataFrame,
    rng: np.random.Generator,
    target_orders: int,
) -> tuple[np.ndarray, np.ndarray]:
    months = pd.period_range(FIRST_MONTH, LAST_MONTH, freq="M")
    size = rng.lognormal(mean=0.0, sigma=0.9, size=MERCHANT_COUNT)
    monthly_trend = rng.normal(0.0, 0.025, MERCHANT_COUNT)

    churner_count = int(MERCHANT_COUNT * 0.10)
    churner_ids = rng.choice(MERCHANT_COUNT, size=churner_count, replace=False)
    is_churner = np.zeros(MERCHANT_COUNT, dtype=bool)
    is_churner[churner_ids] = True

    remaining = np.setdiff1d(np.arange(MERCHANT_COUNT), churner_ids)
    declining_ids = rng.choice(remaining, size=25, replace=False)
    monthly_trend[declining_ids] = rng.normal(-0.06, 0.015, size=len(declining_ids))
    remaining = np.setdiff1d(remaining, declining_ids)
    growing_ids = rng.choice(remaining, size=30, replace=False)
    monthly_trend[growing_ids] = rng.normal(0.07, 0.02, size=len(growing_ids))

    expected = np.zeros((MERCHANT_COUNT, len(months)), dtype=float)
    onboarded = pd.to_datetime(merchants["onboarding_date"]).to_numpy()
    for month_number, month in enumerate(months):
        seasonal_lift = SEASONAL_VOLUME[str(month)]
        trend_factor = np.exp(monthly_trend * month_number)
        monthly_size = size * trend_factor * seasonal_lift
        active = onboarded <= month.end_time.to_datetime64()
        monthly_size = np.where(active, monthly_size, 0.0)

        if month_number >= len(months) - 3:
            decline = (0.45, 0.25, 0.10)[month_number - (len(months) - 3)]
            monthly_size = np.where(is_churner, monthly_size * decline, monthly_size)
        expected[:, month_number] = monthly_size

    expected *= target_orders / expected.sum()
    monthly_counts = rng.poisson(expected)
    total_by_merchant = monthly_counts.sum(axis=1)
    median_orders, top_tier_cutoff = np.quantile(total_by_merchant, [0.50, 0.85])
    merchants["tier"] = np.where(
        total_by_merchant >= top_tier_cutoff,
        "Platinum",
        np.where(total_by_merchant >= median_orders, "Gold", "Silver"),
    )
    merchants["onboarding_date"] = pd.to_datetime(merchants["onboarding_date"]).dt.date
    return monthly_counts, is_churner


def _make_orders(
    rng: np.random.Generator,
    merchants: pd.DataFrame,
    hubs: pd.DataFrame,
    monthly_counts: np.ndarray,
    is_churner: np.ndarray,
) -> pd.DataFrame:
    months = pd.period_range(FIRST_MONTH, LAST_MONTH, freq="M")
    hub_weights = hubs["volume_weight"].to_numpy(dtype=float)
    hub_weights /= hub_weights.sum()
    merchant_hub_choices: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(MERCHANT_COUNT):
        choice_count = int(rng.integers(2, 5))
        hub_indexes = rng.choice(
            len(hubs), size=choice_count, replace=False, p=hub_weights
        )
        merchant_hub_choices.append((hub_indexes, rng.dirichlet(np.ones(choice_count))))

    order_parts: list[pd.DataFrame] = []
    for merchant_number in range(MERCHANT_COUNT):
        for month_number, month in enumerate(months):
            count = int(monthly_counts[merchant_number, month_number])
            if count == 0:
                continue

            onboarding_date = pd.Timestamp(
                merchants.at[merchant_number, "onboarding_date"]
            )
            first_available_day = max(0, (onboarding_date - month.start_time).days)
            dates = month.start_time + pd.to_timedelta(
                rng.integers(first_available_day, month.days_in_month, size=count),
                unit="D",
            )
            selected_hubs, hub_mix = merchant_hub_choices[merchant_number]
            hub_indexes = rng.choice(selected_hubs, size=count, p=hub_mix)
            order_parts.append(
                pd.DataFrame(
                    {
                        "merchant_number": merchant_number,
                        "hub_number": hub_indexes,
                        "order_date": dates,
                    }
                )
            )

    orders = pd.concat(order_parts, ignore_index=True)
    order_count = len(orders)
    hub_numbers = orders["hub_number"].to_numpy(dtype=int)
    merchant_numbers = orders["merchant_number"].to_numpy(dtype=int)
    order_month = orders["order_date"].dt.strftime("%Y-%m")

    hub_days = hubs["base_days"].to_numpy()[hub_numbers]
    peak_month = order_month.isin(["2025-12", "2026-03", "2026-05"]).to_numpy()
    delivery_days = rng.gamma(shape=4, scale=(hub_days + peak_month * 0.5) / 4)
    delivery_days = np.clip(np.rint(delivery_days), 1, 12).astype(int)

    failure_chance = hubs["base_fail_rate"].to_numpy()[hub_numbers]
    return_chance = np.clip(0.03 + 0.035 * (delivery_days - 1), 0.02, 0.45)
    draw = rng.random(order_count)
    status = np.where(
        draw < 0.025,
        "Cancelled",
        np.where(
            draw < 0.025 + failure_chance * 0.5,
            "Failed",
            np.where(
                draw < 0.025 + failure_chance * 0.5 + return_chance * 0.35,
                "Returned",
                "Delivered",
            ),
        ),
    )

    recent_churn = (
        is_churner[merchant_numbers] & (orders["order_date"] >= "2026-06-01").to_numpy()
    )
    extra_returns = (
        recent_churn & (status == "Delivered") & (rng.random(order_count) < 0.10)
    )
    status = np.where(extra_returns, "Returned", status)

    delivery_dates = orders["order_date"] + pd.to_timedelta(delivery_days, unit="D")
    cancelled = status == "Cancelled"
    delivery_dates = delivery_dates.where(~cancelled)

    merchant_categories = merchants["category"].to_numpy()[merchant_numbers]
    average_cod = np.array(
        [AVERAGE_COD_BY_CATEGORY[category] for category in merchant_categories]
    )
    cod_amount = np.round(rng.lognormal(np.log(average_cod), 0.5) / 10) * 10
    cod_amount = np.where(rng.random(order_count) < 0.12, 0, cod_amount).astype(int)
    divisions = hubs["division"].to_numpy()[hub_numbers]
    delivery_fee = np.where(divisions == "Dhaka", 60, 110) + rng.choice(
        [0, 20, 40], size=order_count, p=[0.70, 0.20, 0.10]
    )
    cod_collected = (
        (status == "Delivered") & (cod_amount > 0) & (rng.random(order_count) < 0.97)
    ).astype(int)

    orders = pd.DataFrame(
        {
            "order_id": [f"ORD{number:06d}" for number in range(1, order_count + 1)],
            "merchant_id": merchants["merchant_id"].to_numpy()[merchant_numbers],
            "hub_id": hubs["hub_id"].to_numpy()[hub_numbers],
            "order_date": orders["order_date"].dt.date,
            "delivery_date": delivery_dates.dt.date,
            "status": status,
            "delivery_days": np.where(cancelled, np.nan, delivery_days),
            "cod_amount": cod_amount,
            "delivery_fee": delivery_fee,
            "cod_collected": cod_collected,
        }
    )
    return orders


def _make_issues(rng: np.random.Generator, orders: pd.DataFrame) -> pd.DataFrame:
    # More trouble tickets follow failed/returned parcels and longer trips.
    bad_outcome = orders["status"].isin(["Failed", "Returned"]).to_numpy()
    delivery_days = orders["delivery_days"].fillna(0).to_numpy(dtype=float)
    issue_weight = 0.5 + bad_outcome.astype(float) + 0.2 * delivery_days
    expected_rate = 8_000 / 60_000
    issue_probability = np.minimum(
        0.65, issue_weight * (expected_rate / issue_weight.mean())
    )
    has_issue = rng.random(len(orders)) < issue_probability
    affected_orders = orders.loc[has_issue].reset_index(drop=True)
    issue_count = len(affected_orders)

    issue_type = rng.choice(ISSUE_TYPES, size=issue_count, p=ISSUE_TYPE_WEIGHTS)
    opened_at = pd.to_datetime(affected_orders["order_date"]) + pd.to_timedelta(
        rng.integers(0, 4, size=issue_count), unit="D"
    )
    typical_hours = np.array([ISSUE_RESOLUTION_HOURS[value] for value in issue_type])
    resolution_hours = typical_hours * rng.lognormal(
        mean=0.0, sigma=0.5, size=issue_count
    )
    resolved_at = opened_at + pd.to_timedelta(resolution_hours, unit="h")
    is_open = rng.random(issue_count) < 0.06

    return pd.DataFrame(
        {
            "issue_id": [f"ISS{number:05d}" for number in range(1, issue_count + 1)],
            "order_id": affected_orders["order_id"],
            "issue_type": issue_type,
            "opened_at": opened_at.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.where(~is_open).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "status": np.where(is_open, "Open", "Resolved"),
        }
    )


def generate_data(
    output_dir: Path, *, seed: int = 42, target_orders: int = DEFAULT_ORDER_COUNT
) -> dict[str, int]:
    """Write the five related CSVs and return their row counts."""
    if target_orders < MERCHANT_COUNT:
        raise ValueError(f"target_orders must be at least {MERCHANT_COUNT}")

    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    kams, hubs, merchants = _make_reference_tables(rng)
    monthly_counts, is_churner = _merchant_monthly_volume(merchants, rng, target_orders)
    orders = _make_orders(rng, merchants, hubs, monthly_counts, is_churner)
    issues = _make_issues(rng, orders)

    tables = {
        "kams": kams,
        "merchants": merchants,
        "hubs": hubs[["hub_id", "hub_name", "district", "division"]],
        "orders": orders,
        "issues": issues,
    }
    row_counts: dict[str, int] = {}
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, encoding="utf-8")
        row_counts[name] = len(table)
    return row_counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="where the CSV files should be written (default: repository data/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed; the same seed recreates the same files",
    )
    parser.add_argument(
        "--target-orders",
        type=int,
        default=DEFAULT_ORDER_COUNT,
        help="expected order count before ordinary Poisson variation",
    )
    args = parser.parse_args()

    counts = generate_data(
        args.output_dir, seed=args.seed, target_orders=args.target_orders
    )
    print("Synthetic files written to", args.output_dir)
    print("  " + "  |  ".join(f"{name}: {count:,}" for name, count in counts.items()))
    status_mix = pd.read_csv(args.output_dir / "orders.csv")["status"].value_counts(
        normalize=True
    )
    print(
        "  order statuses:",
        ", ".join(f"{name} {share:.1%}" for name, share in status_mix.items()),
    )


if __name__ == "__main__":
    main()
