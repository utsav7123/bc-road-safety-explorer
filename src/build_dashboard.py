from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data" / "dashboard.json"

REGION_COORDS = {
    "Lower Mainland": [49.22, -122.73],
    "Vancouver Island": [49.55, -125.55],
    "Southern Interior": [50.25, -119.35],
    "North Central": [54.15, -123.20],
}

METRICS = {
    "fatalities_road_user": {
        "title": "Fatalities by road user type",
        "source": "RoadSafetyBC",
        "refresh": "Annual",
        "caveat": "Fatalities are deaths within 30 days of a motor vehicle collision on a public highway. Published exclusions apply.",
    },
    "fatalities_region": {
        "title": "Fatalities by police traffic region",
        "source": "RoadSafetyBC",
        "refresh": "Annual",
        "caveat": "Regional values are aggregate police traffic region totals and are not exact crash locations.",
    },
    "serious_injuries_region": {
        "title": "Serious injuries by police traffic region",
        "source": "RoadSafetyBC",
        "refresh": "Annual",
        "caveat": "This source includes police-attended crashes where the officer assesses more than 24 hours of hospitalization.",
    },
    "fatalities_speeding": {
        "title": "Fatalities with speeding involvement",
        "source": "RoadSafetyBC",
        "refresh": "Annual",
        "caveat": "Speeding involvement is based on contributing-factor reporting in the source data.",
    },
}


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def read_source(name: str) -> pd.DataFrame:
    path = RAW / f"{name}.csv"
    frame = pd.read_csv(path, encoding_errors="replace")
    frame.columns = [clean_text(c) for c in frame.columns]
    frame = frame.dropna(how="all")
    return frame


def to_long(frame: pd.DataFrame) -> pd.DataFrame:
    year_columns = [c for c in frame.columns if re.fullmatch(r"(19|20)\d{2}", clean_text(c))]
    if year_columns:
        category_cols = [c for c in frame.columns if c not in year_columns]
        category_col = category_cols[0]
        long = frame.melt(id_vars=[category_col], value_vars=year_columns, var_name="year", value_name="value")
        long = long.rename(columns={category_col: "category"})
    else:
        year_col = next((c for c in frame.columns if "year" in c.lower()), None)
        if year_col is None:
            raise ValueError(f"Could not identify a year field from columns: {list(frame.columns)}")
        value_candidates = [
            c for c in frame.columns
            if c != year_col and ("count" in c.lower() or "number" in c.lower() or "fatal" in c.lower() or "injur" in c.lower())
        ]
        value_col = value_candidates[-1] if value_candidates else frame.columns[-1]
        category_candidates = [c for c in frame.columns if c not in {year_col, value_col}]
        category_col = category_candidates[0] if category_candidates else None
        long = pd.DataFrame({
            "year": frame[year_col],
            "value": frame[value_col],
            "category": frame[category_col] if category_col else "Total",
        })

    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = pd.to_numeric(
        long["value"].astype(str).str.replace(",", "", regex=False).str.replace("<", "", regex=False),
        errors="coerce",
    )
    long["category"] = long["category"].map(clean_text)
    long = long.dropna(subset=["year", "value"])
    long = long[(long["year"] >= 1990) & (long["year"] <= 2100)]
    long["year"] = long["year"].astype(int)
    return long


def aggregate_year(long: pd.DataFrame) -> list[dict]:
    annual = long.groupby("year", as_index=False)["value"].sum().sort_values("year")
    return [{"year": int(r.year), "value": int(round(r.value))} for r in annual.itertuples()]


def forecast(annual: list[dict], years: int = 3) -> list[dict]:
    if len(annual) < 5:
        return []
    recent = annual[-10:]
    x = np.array([r["year"] for r in recent]).reshape(-1, 1)
    y = np.array([r["value"] for r in recent])
    model = LinearRegression().fit(x, y)
    start = recent[-1]["year"] + 1
    result = []
    for year in range(start, start + years):
        value = max(0, float(model.predict([[year]])[0]))
        result.append({"year": year, "value": round(value, 1)})
    return result


def latest_breakdown(long: pd.DataFrame) -> dict:
    latest_year = int(long["year"].max())
    rows = (
        long[long["year"] == latest_year]
        .groupby("category", as_index=False)["value"].sum()
        .sort_values("value", ascending=False)
    )
    return {
        "year": latest_year,
        "items": [{"category": r.category, "value": int(round(r.value))} for r in rows.itertuples()],
    }


def five_year_change(annual: list[dict]) -> float | None:
    if len(annual) < 6:
        return None
    latest = annual[-1]["value"]
    prior = annual[-6]["value"]
    if prior == 0:
        return None
    return round((latest - prior) / prior * 100, 1)


def region_points(fatal: pd.DataFrame, serious: pd.DataFrame) -> list[dict]:
    latest = min(int(fatal["year"].max()), int(serious["year"].max()))
    f = fatal[fatal["year"] == latest].groupby("category")["value"].sum()
    s = serious[serious["year"] == latest].groupby("category")["value"].sum()
    points = []
    for region, coords in REGION_COORDS.items():
        fmatch = next((float(v) for k, v in f.items() if region.lower() in k.lower()), 0)
        smatch = next((float(v) for k, v in s.items() if region.lower() in k.lower()), 0)
        points.append({
            "region": region,
            "lat": coords[0],
            "lon": coords[1],
            "fatalities": int(round(fmatch)),
            "serious_injuries": int(round(smatch)),
            "year": latest,
        })
    return points


def build() -> dict:
    long = {name: to_long(read_source(name)) for name in METRICS}
    annual = {name: aggregate_year(data) for name, data in long.items()}
    latest_year = max(r[-1]["year"] for r in annual.values() if r)
    road_users = latest_breakdown(long["fatalities_road_user"])
    vulnerable_names = ("pedestrian", "cyclist", "bicycle", "motorcycl")
    vulnerable = [
        item for item in road_users["items"]
        if any(term in item["category"].lower() for term in vulnerable_names)
    ]

    kpis = []
    for key in ("fatalities_region", "serious_injuries_region", "fatalities_speeding"):
        series = annual[key]
        latest = series[-1]
        kpis.append({
            "key": key,
            "label": METRICS[key]["title"],
            "year": latest["year"],
            "value": latest["value"],
            "five_year_change": five_year_change(series),
            **{k: METRICS[key][k] for k in ("source", "refresh", "caveat")},
        })

    return {
        "generated_from": "Government of British Columbia / RoadSafetyBC public aggregate datasets",
        "latest_year_seen": latest_year,
        "kpis": kpis,
        "annual": annual,
        "road_users": road_users,
        "vulnerable_road_users": vulnerable,
        "region_points": region_points(long["fatalities_region"], long["serious_injuries_region"]),
        "forecast": forecast(annual["fatalities_region"]),
        "forecast_note": "Simple linear trend projection using the most recent 10 annual observations. This is a portfolio baseline, not an official ICBC or RoadSafetyBC forecast.",
        "metric_dictionary": METRICS,
    }


def main() -> None:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote dashboard data for latest year {payload['latest_year_seen']} to {OUT}")


if __name__ == "__main__":
    main()
