from __future__ import annotations

import pandas as pd

from src.build_dashboard import to_long, five_year_change, forecast


def test_to_long_handles_wide_year_table():
    frame = pd.DataFrame({
        "Region": ["Lower Mainland", "Vancouver Island"],
        "2022": [10, 5],
        "2023": [12, 7],
    })
    long = to_long(frame)
    assert set(long.columns) >= {"year", "category", "value"}
    assert len(long) == 4
    assert set(long["year"]) == {2022, 2023}


def test_to_long_handles_long_table():
    frame = pd.DataFrame({
        "Year": [2022, 2023],
        "Region": ["A", "A"],
        "Number of Fatalities": [11, 13],
    })
    long = to_long(frame)
    assert long["value"].tolist() == [11, 13]


def test_five_year_change():
    annual = [{"year": y, "value": v} for y, v in zip(range(2018, 2024), [100, 102, 104, 106, 108, 110])]
    assert five_year_change(annual) == 10.0


def test_forecast_returns_three_future_years():
    annual = [{"year": y, "value": 100 + 2 * (y - 2014)} for y in range(2014, 2024)]
    result = forecast(annual)
    assert len(result) == 3
    assert result[0]["year"] == 2024
    assert result[0]["value"] > annual[-1]["value"]
