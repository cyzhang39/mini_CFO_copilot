import json, os, random, time
STATE_FILE = "feedbacks/rlhf.json"
STYLES = ["concise", "detail"]

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {s: {"n": 0, "avg": 0.0} for s in STYLES}

def save_state(state): 
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True); json.dump(state, open(STATE_FILE,"w"))

def pick_style(eps):
    state = load_state()
    if random.random() < eps:
        return random.choice(STYLES)
    return max(STYLES, key=lambda s: state[s]["avg"])

def update_style(style, reward):
    state = load_state()
    rec = state.setdefault(style, {"n": 0, "avg": 0.0})
    rec["n"] += 1
    rec["avg"] += (reward - rec["avg"]) / rec["n"]
    save_state(state)


def log_feedback(reward, question, routed, style, answer):
    os.makedirs("feedback", exist_ok=True)
    event = {
        "time": int(time.time()),
        "question": question,
        "intent": routed["intent"],
        "months": routed.get("used_months"),
        "entity": routed.get("entity"),
        "style": style,
        "answer": answer,
        "payload": routed["payload"],
        "reward": reward,
    }
    with open("feedback/feedback.json", "a") as f:
        f.write(json.dumps(event) + "\n")
    update_style(style, reward)