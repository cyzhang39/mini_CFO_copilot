from __future__ import annotations
import os, json, requests

def answer_text(intent, payload, question):
    api_url = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
    api_token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    # print(api_url)
    # print(api_token)
    # print(model)
    if not api_token:
        raise RuntimeError("HF_TOKEN not set")

    system = (
        "You are a finance assistant. Reply with one short plain-text sentence "
        "using ONLY the provided JSON payload. Do not invent numbers or months. If evident, provide exact timeline in the answer."
        "No markdown, no code fences. Avoid exaggerated words."
    )
    print(payload)
    user = (
        "Write one concise answer to the user's question using only this data.\n"
        f"question: {question}\n"
        f"intent: {json.dumps(intent)}\n"
        f"payload: {json.dumps(payload, ensure_ascii=False)}\n"
    )

    r = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "max_tokens": 518,
        },
        # timeout=60,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").strip()
    return text
