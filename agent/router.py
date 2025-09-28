from typing import Dict, Any

from agent.data import DataStore, load_data
# from agent import metrics
# from data import DataStore, load_data
import agent.metrics as metrics

ROUTES = {
    "revenue": metrics.revenue,
    "gross_margin": metrics.gross_margin,
    "opex_total": metrics.opex_total,
    "ebitda": metrics.ebitda,
    "cash_runway": metrics.cash_runway,
}


def route(interp, ds):

    intent = interp.get("intent")
    months = interp.get("months") or []
    entity = (interp.get("filters") or {}).get("entity")
    # print(entity)
    fn = ROUTES.get(intent)
    if fn is None:
        return {
            "error": "unknown_intent",
            "intent": intent,
            "used_months": months,
            "entity": entity,
        }

    payload = fn(ds, months, entity)

    return {
        "intent": intent,
        "used_months": months,
        "entity": entity if entity is not None else payload.get("entity", "All"),
        "payload": payload,
    }


# ds = load_data("fixtures/")
# interp = {
#     "intent": "revenue",
#     "months": ["2023-01"]
# }
# print(route(interp, ds))