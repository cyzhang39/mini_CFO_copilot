import os
import json
import requests
import re
from typing import Dict, Any, List, Optional

def interpret(question):

    use_llm = os.getenv("USE_LLM") == "true"
    if use_llm:
        result = llm_interp(question)
        if result is not None:
            return validate(result)

    result = basic_interp(question)
    return validate(result)



ALLOWED_INTENTS = {"revenue", "gross_margin", "opex_total", "ebitda", "cash_runway"}

LLM_SYSTEM_PROMPT = """You are a planner that outputs only strict JSON with no extra text."""

PROMPT = """Classify intent and extract months from the user's question. Don't forcefully choose an intent if there is none.

- Allowed intents (exact strings): ["revenue", "gross_margin", "opex_total", "ebitda", "cash_runway"]
- if no exact month(s), cash_runway should be last three months, every other intents are current month.
- "months" MUST be a JSON array of strings in YYYY-MM format, ordered as the user implies.
- If the user uses natural language dates (e.g., "June 2025", "Q2 2025", "last three months"), convert them to explicit YYYY-MM values.
- Optional: include filters.entity if the user specifies a single entity.
- Output JSON only. No prose.

Examples:
Q: "What was June 2025 revenue vs budget in USD?"
A: {"intent":"revenue","months":["2025-06"]}

Q: "Show Gross Margin % trend for the last 3 months."
A: {"intent":"gross_margin","months":["2025-07","2025-08","2025-09"]}

Q: "Break down Opex by category for June."
A: {"intent":"opex_total","months":["2025-06"]}

Q: "What is our cash runway right now?"
A: {"intent":"cash_runway","months":["2025-07","2025-08","2025-09"]}

Q: "What was June 2025 revenue vs budget in USD for ParentCo?"
A: {"intent":"revenue","months":["2025-06"], "filters": {"entity": "ParentCo"}}

"""

def llm_interp(question):

    api_url = os.getenv("HF_API_URL")
    api_token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    # print(api_url)
    # print(api_token)
    # print(model)
    if not api_token:
        return None

    messages = [
        {"role": "system", "content": LLM_SYSTEM_PROMPT},
        {"role": "user", "content": f"{PROMPT}\nQ: {question}"},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 518,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=600)
    # print(resp)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    obj = get_json(text)
    # 
    return obj



def get_json(text):
    # print(text)
    if not text:
        return None
    
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "```").strip()
    # print(cleaned)
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned.strip("`").strip()
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        return None
    return json.loads(m.group(0))



def basic_interp(question):

    months = get_months(question)
    if not months:
        raise ValueError(
            "Interpreter requires explicit months in YYYY-MM (e.g., 2025-06). "
            "Enable LLM mode to parse natural-language dates."
        )
    q = question.lower()
    # print(q)
    if "ebitda" in q:
        intent = "ebitda"
    elif "gross margin" in q or re.search(r"\bgm\b", q):
        intent = "gross_margin"
    elif "opex" in q or "operating expense" in q or "operating expenses" in q:
        intent = "opex_total"
    elif "runway" in q or "burn" in q:
        intent = "cash_runway"
    else:
        intent = "revenue"

    entity = get_entity(q)

    out = {"intent": intent, "months": months}
    # print(out)
    if entity is not None:
        out["filters"] = {"entity": entity}
    return out


def get_months(text):
    return re.findall(r"\b\d{4}-\d{2}\b", text)

def get_entity(text_lower):
    m = re.search(r"entity\s*[:=]\s*([A-Za-z0-9 _\-\.&]+)", text_lower)
    if m:
        return m.group(1).strip()
    return None


def validate(d):
    
    if not isinstance(d, dict):
        # print(type(d))
        raise ValueError("Interpreter must return JSON")

    intent = d.get("intent")
    if intent not in ALLOWED_INTENTS:
        # print(intent)
        raise ValueError(f"Invalid intent: {intent}. Allowed: {ALLOWED_INTENTS}")

    months = d.get("months")
    if not isinstance(months, list) or not months:
        # print(d)
        raise ValueError("`months` must be a non-empty list of YYYY-MM strings.")
    for m in months:
        if not isinstance(m, str) or not re.fullmatch(r"\d{4}-\d{2}", m):
            # print(type(m))
            raise ValueError(f"Invalid month format: {m}. Use YYYY-MM.")

    filters = d.get("filters")
    if filters is not None:
        if not isinstance(filters, dict):
            raise ValueError("`filters`, if present, must be an object.")
        filt_clean = {}
        if "entity" in filters and isinstance(filters["entity"], str):
            filt_clean["entity"] = filters["entity"]
        d["filters"] = filt_clean if filt_clean else None
        if d["filters"] is None:
            d.pop("filters", None)

    return {"intent": intent, "months": months, **({"filters": d["filters"]} if "filters" in d else {})}
