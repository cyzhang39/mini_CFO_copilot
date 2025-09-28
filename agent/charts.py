from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

usd_fmt = FuncFormatter(lambda x, pos: f"${x/1_000:,.0f}k")
pct_fmt = FuncFormatter(lambda x, pos: f"{x*100:.1f}%")

def chart_revenue(payload):
    labels = ["Actual", "Budget"]
    vals = [payload.get("actual_usd", 0.0), payload.get("budget_usd", 0.0)]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(labels, vals)
    ax.set_title(f"Revenue of {payload.get('month','')}")
    ax.set_ylabel("USD")
    ax.yaxis.set_major_formatter(usd_fmt)
    fig.tight_layout()
    return fig

def chart_gross_margin(payload):
    months = payload.get("months", [])
    gm_usd = payload.get("gm_usd", [])
    gm_pct = payload.get("gm_pct", [])
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(months, gm_usd, marker="o", label="GM USD")
    ax.set_ylabel("USD"); ax.yaxis.set_major_formatter(usd_fmt)
    ax.set_xlabel("Month")
    ax2 = ax.twinx()
    ax2.plot(months, gm_pct, marker="o", linestyle="--", label="GM %")
    ax2.set_ylabel("GM %"); ax2.yaxis.set_major_formatter(pct_fmt)
    ax.set_title("Gross Margin in USD & %")
    ax.legend(loc="upper left"); ax2.legend(loc="upper right")
    fig.tight_layout()
    return fig

def chart_opex_total(payload):
    cats = payload.get("categories", [])
    vals = payload.get("values_usd", [])
    h = max(2.5, 0.35 * len(cats) + 1)
    fig, ax = plt.subplots(figsize=(6, h))
    y = np.arange(len(cats))
    ax.barh(y, vals)
    ax.set_yticks(y); ax.set_yticklabels(cats)
    ax.set_xlabel("USD"); ax.xaxis.set_major_formatter(usd_fmt)
    ax.set_title(f"Opex by category in {payload.get('month','')}")
    fig.tight_layout()
    return fig

def chart_ebitda(payload):
    months = payload.get("months", [])
    e_usd  = payload.get("ebitda_usd", [])
    e_mrg  = payload.get("ebitda_margin", [])
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(months, e_usd, marker="o", label="EBITDA USD")
    ax.set_ylabel("USD"); ax.yaxis.set_major_formatter(usd_fmt)
    ax.set_xlabel("Month")
    ax2 = ax.twinx()
    ax2.plot(months, e_mrg, marker="o", linestyle="--", label="EBITDA %")
    ax2.set_ylabel("Margin"); ax2.yaxis.set_major_formatter(pct_fmt)
    ax.set_title("EBITDA - USD & %")
    ax.legend(loc="upper left"); ax2.legend(loc="upper right")
    fig.tight_layout()
    return fig

def render_charts(intent: str, payload: dict):
    if intent == "revenue":
        return [chart_revenue(payload)]
    if intent == "gross_margin":
        return [chart_gross_margin(payload)]
    if intent == "opex_total":
        return [chart_opex_total(payload)]
    if intent == "ebitda":
        return [chart_ebitda(payload)]
    return []
