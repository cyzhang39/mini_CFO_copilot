from io import BytesIO
from typing import List, Tuple
import datetime as dt
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def label_month(payload):
    ms = payload.get("months") or []
    if ms:
        return ms[0] if len(ms) == 1 else f"{ms[0]}_{ms[-1]}"
    return payload.get("month") or "period"


def build_pdf(intent, payload, question, answer, figs):
    # print(intent)
    # print(payload)
    # print(question)
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "CFO Copilot Report",
            "",
            f"Intent: {intent}",
            f"Months: {label_month(payload)}",
            f"Generated: {ts}",
            "",
            "Question:",
            textwrap.fill(question or "", width=100),
            "",
            "Answer:",
            textwrap.fill(answer or "", width=100),
        ]
        y = 0.9
        for ln in lines:
            ax.text(0.07, y, ln, fontsize=11, va="top")
            y -= 0.04 if ln else 0.02

        pdf.savefig(fig)
        plt.close(fig)

        if figs:
            pdf.savefig(figs[0])

    filename = f"report_{intent}_{label_month(payload)}.pdf"
    return buf.getvalue(), filename
