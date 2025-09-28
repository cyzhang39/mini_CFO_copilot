from typing import Optional, Dict, Any, List
import pandas as pd
from agent.data import DataStore, to_usd, load_data
# from data import DataStore, to_usd, load_data


def revenue(ds, months, entity):
    month = months[0]
    a = ds.actuals[(ds.actuals["month"] == month) & (ds.actuals["account_category"] == "Revenue")]
    b = ds.budget[(ds.budget["month"] == month) & (ds.budget["account_category"] == "Revenue")]

    if entity:
        a = a[a["entity"] == entity]
        b = b[b["entity"] == entity]

    a_usd = to_usd(a, ds.fx)
    b_usd = to_usd(b, ds.fx)

    actual_total = float(a_usd["amount_usd"].sum()) if not a_usd.empty else 0.0
    budget_total = float(b_usd["amount_usd"].sum()) if not b_usd.empty else 0.0

    delta_usd = actual_total - budget_total
    pct_to_budget = (actual_total / budget_total) if budget_total not in (0, 0.0) else None

    return {
        "month": month,
        "entity": entity or "All",
        "actual_usd": actual_total,
        "budget_usd": budget_total,
        "delta_usd": delta_usd,
        "pct_to_budget": pct_to_budget,
    }


def gross_margin(ds, months, entity):

    if not months:
        # print(months)
        return {"months": [], "entity": entity or "All", "gm_usd": [], "gm_pct": []}

    a = ds.actuals[(ds.actuals["month"].isin(months)) & (ds.actuals["account_category"].isin(["Revenue", "COGS"]))]
    if entity:
        a = a[a["entity"] == entity]

    a_usd = to_usd(a, ds.fx)

    grouped = (a_usd.groupby(["month", "account_category"], as_index=False)["amount_usd"].sum())

    rev_by_month = grouped[grouped["account_category"] == "Revenue"].set_index("month")["amount_usd"].to_dict()
    cogs_by_month = grouped[grouped["account_category"] == "COGS"].set_index("month")["amount_usd"].to_dict()
    # print(rev_by_month.head())
    gm_usd = []
    gm_pct = []

    for m in months:
        rev = float(rev_by_month.get(m, 0.0))
        cogs = float(cogs_by_month.get(m, 0.0))
        gm = rev - cogs
        pct = (gm / rev) if rev not in (0, 0.0) else None

        gm_usd.append(gm)
        gm_pct.append(pct)
    # print(gm_usd)
    # print(gm_pct)
    return {
        "months": months,
        "entity": entity or "All",
        "gm_usd": gm_usd,
        "gm_pct": gm_pct,
    }

def opex_total(ds, months, entity):
    # print(months)
    month = months[0]
    a = ds.actuals[ds.actuals["month"] == month]
    a = a[a["account_category"].astype(str).str.startswith("Opex")]
    if entity:
        a = a[a["entity"] == entity]

    a_usd = to_usd(a, ds.fx)

    if a_usd.empty:
        # print()
        return {
            "month": month,
            "entity": entity or "All",
            "opex_usd": 0.0,
            "categories": [],
            "values_usd": [],
        }

    by_cat = (a_usd.groupby("account_category", as_index=False)["amount_usd"].sum().sort_values("account_category"))
    # print(by_cat)
    categories = by_cat["account_category"].tolist()
    values = by_cat["amount_usd"].astype(float).tolist()
    total_opex = float(sum(values))

    return {
        "month": month,
        "entity": entity or "All",
        "opex_usd": total_opex,
        "categories": categories,
        "values_usd": values,
    }


def ebitda(ds, months, entity):
    if not months:
        return {"months": [], "entity": entity or "All", "ebitda_usd": [], "ebitda_margin": []}

    a = ds.actuals[ds.actuals["month"].isin(months)]
    mask_rev_cogs = a["account_category"].isin(["Revenue", "COGS"])
    a = a[mask_rev_cogs]
    # print(a.head())
    if entity:
        a = a[a["entity"] == entity]
    a_usd = to_usd(a, ds.fx)

    grouped = (a_usd.groupby(["month", "account_category"], as_index=False)["amount_usd"].sum())
    # print(grouped)
    rev_by_m = grouped[grouped["account_category"] == "Revenue"].set_index("month")["amount_usd"].to_dict()
    # print(rev_by_m)
    cogs_by_m = grouped[grouped["account_category"] == "COGS"].set_index("month")["amount_usd"].to_dict()
    # print(cogs_by_m)
    e_vals = []
    e_margin = []

    for m in months:
        opex_info = opex_total(ds, months=[m], entity=entity)
        opex = float(opex_info["opex_usd"])

        rev = float(rev_by_m.get(m, 0.0))
        cogs = float(cogs_by_m.get(m, 0.0))
        ebitda = rev - cogs - opex
        margin = (ebitda / rev) if rev not in (0, 0.0) else None

        e_vals.append(ebitda)
        e_margin.append(margin)
    # print(e_vals)
    # print(e_margin)
    return {
        "months": months,
        "entity": entity or "All",
        "ebitda_usd": e_vals,
        "ebitda_margin": e_margin,
    }


def cash_runway(ds, months, entity):

    if not months:
        return {
            "month": None,
            "months": [],
            "entity": entity or "All",
            "cash_usd": 0.0,
            "avg_burn_usd": 0.0,
            "runway_months": None,
        }

    last = months[-1]

    cash_df = ds.cash[ds.cash["month"] == last]
    if entity:
        cash_df = cash_df[cash_df["entity"] == entity]
    cash_usd = float(cash_df["cash_usd"].sum()) if not cash_df.empty else 0.0

    a = ds.actuals[ds.actuals["month"].isin(months)]
    if entity:
        a = a[a["entity"] == entity]

    mask_rev = a["account_category"] == "Revenue"
    mask_cogs = a["account_category"] == "COGS"
    mask_opex = a["account_category"].astype(str).str.startswith("Opex")
    a = a[mask_rev | mask_cogs | mask_opex]

    grouped = a.groupby(["month", "account_category"], as_index=False)["amount"].sum()
    # print(grouped)
    rev_by_m = grouped[grouped["account_category"] == "Revenue"].set_index("month")["amount"].to_dict()
    cogs_by_m = grouped[grouped["account_category"] == "COGS"].set_index("month")["amount"].to_dict()
    opex_rows = grouped[grouped["account_category"].astype(str).str.startswith("Opex")]
    opex_by_m = opex_rows.groupby("month")["amount"].sum().to_dict()

    burns = []
    for m in months:
        rev = float(rev_by_m.get(m, 0.0))
        cogs = float(cogs_by_m.get(m, 0.0))
        opex = float(opex_by_m.get(m, 0.0))
        burn = (cogs + opex) - rev
        burns.append(burn if burn > 0 else 0.0)
    # print(burns)
    avg_burn = float(pd.Series(burns).mean()) if burns else 0.0
    # print(avg_burn)
    runway = (cash_usd / avg_burn) if avg_burn > 0 else None
    # print(runway)

    return {
        "month": last,
        "months": months,
        "entity": entity or "All",
        "cash_usd": cash_usd,
        "avg_burn_usd": avg_burn,
        "runway_months": runway,
    }


# actuals = pd.DataFrame([
#         {"month": "2025-06", "entity": "A", "account_category": "Opex:Marketing", "amount": 100.0, "currency": "EUR"},
#         {"month": "2025-06", "entity": "A", "account_category": "Opex:R&D", "amount":  50.0, "currency": "USD"},
#         {"month": "2025-06", "entity": "B", "account_category": "Opex:G&A", "amount":  30.0, "currency": "USD"},
#         {"month": "2025-06", "entity": "A", "account_category": "Revenue",  "amount": 999.0, "currency": "USD"},
#         {"month": "2025-06", "entity": "B", "account_category": "COGS", "amount": 999.0, "currency": "USD"},
#         {"month": "2025-05", "entity": "A", "account_category": "Opex:Marketing", "amount": 777.0, "currency": "USD"},
#     ])

# ds = load_data("fixtures/")
# print(revenue(ds, ["2023-01"], None))
# print(cash_runway(ds, ["2023-01", "2023-02", "2023-03"], None))