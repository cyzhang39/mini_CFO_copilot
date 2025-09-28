import os
import pytest
import pandas as pd

from agent.data import load_data, to_usd
from agent.metrics import revenue, gross_margin, opex_total, ebitda, cash_runway

FIXTURES_DIR = "fixtures"

TEST_MONTH   = "2023-01"
TEST_MONTHS3 = ["2023-01", "2023-02", "2023-03"]

DS = load_data(FIXTURES_DIR)

def test_revenue():
    res = revenue(DS, months=[TEST_MONTH], entity=None)

    assert res["month"] == TEST_MONTH
    for k in ["actual_usd", "budget_usd", "delta_usd"]:
        assert isinstance(res[k], (int, float))

    assert res["delta_usd"] == res["actual_usd"] - res["budget_usd"]

    if res["budget_usd"] == 0:
        assert res["pct_to_budget"] is None
    else:
        assert isinstance(res["pct_to_budget"], float)
        assert res["pct_to_budget"] == res["actual_usd"] / res["budget_usd"]

def test_gross_margin():

    res = gross_margin(DS, months=TEST_MONTHS3, entity=None)

    assert res["months"] == TEST_MONTHS3
    assert len(res["gm_usd"]) == len(TEST_MONTHS3)
    assert len(res["gm_pct"]) == len(TEST_MONTHS3)

    a = DS.actuals[(DS.actuals["month"].isin(TEST_MONTHS3)) & (DS.actuals["account_category"] == "Revenue")]
    a_usd = to_usd(a, DS.fx)
    rev_by_m = a_usd.groupby("month", as_index=True)["amount_usd"].sum().to_dict()

    for m, gm_usd, gm_pct in zip(res["months"], res["gm_usd"], res["gm_pct"]):
        rev = float(rev_by_m.get(m, 0.0))
        if rev > 0:
            assert gm_pct is not None
            assert gm_pct == gm_usd / rev
        else:
            assert gm_pct is None

def test_opex_total():
    res = opex_total(DS, months=[TEST_MONTH], entity=None)

    assert res["month"] == TEST_MONTH
    cats = res["categories"]
    vals = res["values_usd"]

    assert isinstance(res["opex_usd"], (int, float))
    assert isinstance(cats, list) and isinstance(vals, list)
    assert len(cats) == len(vals)

    for c in cats:
        assert isinstance(c, str)
        assert c.startswith("Opex")

    assert res["opex_usd"] == sum(vals)

def test_ebitda():
    res = ebitda(DS, months=TEST_MONTHS3, entity=None)
    assert res["months"] == TEST_MONTHS3
    assert len(res["ebitda_usd"]) == len(TEST_MONTHS3)
    assert len(res["ebitda_margin"]) == len(TEST_MONTHS3)

    a = DS.actuals[DS.actuals["month"].isin(TEST_MONTHS3)]
    rev_usd = to_usd(a[a["account_category"] == "Revenue"], DS.fx).groupby("month")["amount_usd"].sum().to_dict()
    cogs_usd = to_usd(a[a["account_category"] == "COGS"], DS.fx).groupby("month")["amount_usd"].sum().to_dict()
    opex_rows = a[a["account_category"].astype(str).str.startswith("Opex")]
    opex_usd = to_usd(opex_rows, DS.fx).groupby("month")["amount_usd"].sum().to_dict()

    for m, e_usd, e_margin in zip(res["months"], res["ebitda_usd"], res["ebitda_margin"]):
        rev = float(rev_usd.get(m, 0.0))
        cogs = float(cogs_usd.get(m, 0.0))
        opex = float(opex_usd.get(m, 0.0))
        expected_e = rev - cogs - opex

        assert e_usd == expected_e
        if rev > 0:
            assert e_margin is not None
            assert e_margin == expected_e / rev
        else:
            assert e_margin is None

def test_cash_runway():
    res = cash_runway(DS, months=TEST_MONTHS3, entity=None)

    assert res["month"] == TEST_MONTHS3[-1]
    assert res["months"] == TEST_MONTHS3

    a = DS.actuals[DS.actuals["month"].isin(TEST_MONTHS3)]
    mask_rev = a["account_category"] == "Revenue"
    mask_cogs = a["account_category"] == "COGS"
    mask_opex = a["account_category"].astype(str).str.startswith("Opex")
    a = a[mask_rev | mask_cogs | mask_opex]

    grp = a.groupby(["month", "account_category"], as_index=False)["amount"].sum()
    rev_by_m = grp[grp["account_category"] == "Revenue"].set_index("month")["amount"].to_dict()
    cogs_by_m = grp[grp["account_category"] == "COGS"].set_index("month")["amount"].to_dict()
    opex_rows = grp[grp["account_category"].astype(str).str.startswith("Opex")]
    opex_by_m = opex_rows.groupby("month")["amount"].sum().to_dict()

    burns = []
    for m in TEST_MONTHS3:
        rev = float(rev_by_m.get(m, 0.0))
        cogs = float(cogs_by_m.get(m, 0.0))
        opex = float(opex_by_m.get(m, 0.0))
        burn = (cogs + opex) - rev
        burns.append(burn if burn > 0 else 0.0)

    expected_avg_burn = float(pd.Series(burns).mean()) if burns else 0.0

    cash_usd = float(DS.cash.loc[DS.cash["month"] == TEST_MONTHS3[-1], "cash_usd"].sum()) if not DS.cash.empty else 0.0

    assert res["avg_burn_usd"] == expected_avg_burn
    assert res["cash_usd"] == cash_usd

    if expected_avg_burn > 0:
        assert res["runway_months"] == cash_usd / expected_avg_burn
    else:
        assert res["runway_months"] is None