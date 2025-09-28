from dataclasses import dataclass
from typing import Optional, Tuple
import os
import pandas as pd
from pandas.api.types import is_numeric_dtype
from dateutil import parser


@dataclass
class DataStore:
    actuals: pd.DataFrame
    budget: pd.DataFrame
    cash: pd.DataFrame
    fx: pd.DataFrame
    

def load_data(pth):
    xlsx_path = os.path.join(pth, "data.xlsx")
    xl = pd.ExcelFile(xlsx_path)
    actuals = load_actuals_budget(xl.parse("actuals"))
    # print("acutals loaded")
    budget = load_actuals_budget(xl.parse("budget"))
    
    cash = load_cash(xl.parse("cash"))
    fx = load_fx(xl.parse("fx"))
    # print("data laoded")
    return DataStore(actuals=actuals, budget=budget, fx=fx, cash=cash)


def to_usd(df, fx, *, month="month", currency="currency", amount="amount", rate= "rate_to_usd", amount_usd="amount_usd"):
    if df.empty:
        df[amount_usd] = df.get(amount, pd.Series(dtype="float64"))
        return df

    temp_fx = fx[[month, currency, rate]].copy()

    merged = df.merge(temp_fx, on=[month, currency], how="left")

    if not is_numeric_dtype(merged[rate]):
        # print(1)
        merged[rate] = pd.to_numeric(merged[rate], errors="coerce")
    if not is_numeric_dtype(merged[amount]):
        # print(2)
        merged[amount] = pd.to_numeric(merged[amount], errors="coerce")

    merged[amount_usd] = merged[amount] * merged[rate]

    return merged.drop(columns=[rate])



def load_actuals_budget(pth):

    df = load_csv(
        pth,
        required=["month", "entity", "account_category", "amount", "currency"],
    )


    # for col in ["entity", "account_category", "currency"]:
    #     df[col] = df[col].astype(str).str.strip()

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # df = df.dropna(subset=["month", "entity", "account_category", "amount"])

    return df.reset_index(drop=True)


def load_fx(path):
    df = load_csv(path, required=["month", "currency", "rate_to_usd"])
    df["rate_to_usd"] = pd.to_numeric(df["rate_to_usd"], errors="coerce")
    return df


def load_cash(path):
    df = load_csv(path, required=["month", "entity", "cash_usd"])
    df["cash_usd"] = pd.to_numeric(df["cash_usd"], errors="coerce")
    return df


def load_csv(path, required):
    df = path.copy()
    # missing = [c for c in required if c not in df.columns]
    # if missing:
    #     raise ValueError(f"{os.path.basename(str(path))} missing columns: {missing}")

    return df
