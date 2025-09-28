# tests/test_data_loading.py
import os
import pandas as pd
import pytest

from agent.data import load_data, to_usd

FIXTURES_DIR = "fixtures"

EXPECTED_ACTUALS_BUDGET_COLS = {"month", "entity", "account_category", "amount", "currency"}
EXPECTED_FX_COLS = {"month", "currency", "rate_to_usd"}
EXPECTED_CASH_COLS = {"month", "entity", "cash_usd"}


def test_load_data_and_columns():
    xlsx_path = os.path.join(FIXTURES_DIR, "data.xlsx")
    csv_files = [os.path.join(FIXTURES_DIR, f) for f in ["actuals.csv", "budget.csv", "fx.csv", "cash.csv"]]

    if not (os.path.exists(xlsx_path) or all(os.path.exists(f) for f in csv_files)):
        pytest.skip("No data.xlsx or CSV fixtures available")

    ds = load_data(FIXTURES_DIR)

    assert set(ds.actuals.columns) >= EXPECTED_ACTUALS_BUDGET_COLS
    assert set(ds.budget.columns)  >= EXPECTED_ACTUALS_BUDGET_COLS
    assert set(ds.fx.columns)      >= EXPECTED_FX_COLS
    assert set(ds.cash.columns)    >= EXPECTED_CASH_COLS

    assert pd.api.types.is_numeric_dtype(ds.actuals["amount"])
    assert pd.api.types.is_numeric_dtype(ds.budget["amount"])
    assert pd.api.types.is_numeric_dtype(ds.fx["rate_to_usd"])
    assert pd.api.types.is_numeric_dtype(ds.cash["cash_usd"])


def test_to_usd_uses_fx_rate():
    ds = load_data(FIXTURES_DIR)

    assert len(ds.fx) > 0, "FX table is empty in fixtures"
    fx_row = ds.fx.iloc[0]
    m = fx_row["month"]
    ccy = fx_row["currency"]
    rate = float(fx_row["rate_to_usd"])

    df = pd.DataFrame(
        [{
            "month": m,
            "entity": "TestCo",
            "account_category": "Revenue",
            "amount": 100.0,
            "currency": ccy,
        }]
    )

    out = to_usd(df, ds.fx)
    assert "amount_usd" in out.columns
    assert float(out.loc[0, "amount_usd"]) == pytest.approx(100.0 * rate, rel=1e-9, abs=1e-9)


def test_to_usd_empty_df():
    ds = load_data(FIXTURES_DIR)

    empty_actuals = pd.DataFrame(columns=list(EXPECTED_ACTUALS_BUDGET_COLS))

    out = to_usd(empty_actuals, ds.fx)
    assert "amount_usd" in out.columns
    assert len(out) == 0
