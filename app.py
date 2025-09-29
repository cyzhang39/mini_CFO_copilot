import streamlit as st
from dotenv import load_dotenv

from agent.data import load_data
from agent.interpreter import interpret
from agent.router import route
from agent.answer import answer_text
from agent.charts import render_charts
from agent.export import build_pdf
from agent.rlhf import log_feedback

load_dotenv(override=False)
st.set_page_config(page_title="CFO Copilot", layout="wide")

FIXTURES_DIR = "fixtures"

@st.cache_resource(show_spinner=False)
def get_datastore():
    return load_data(FIXTURES_DIR)

st.title("Mini CFO Copilot (https://github.com/cyzhang39/mini_CFO_copilot.git)")
st.caption("Type a question. Sample questions:")
st.caption("What was June 2025 revenue vs budget in USD?")
st.caption("Show Gross Margin % trend for the last 3 months.")
st.caption("Break down Opex by category for June.")
st.caption("What is our cash runway right now?")

try:
    ds = get_datastore()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

question = st.text_input("Your question")

if question.strip():
    # print(question.strip())
    try:
        interp = interpret(question)    
        routed = route(interp, ds)      

        if "error" in routed:
            st.error(f"Router error: {routed['error']} (intent={routed.get('intent')})")
        else:
            intent = routed["intent"]
            payload = routed["payload"]
            answer = answer_text(intent, payload, question)
            st.subheader("Answer")
            st.text(answer)
            # print(intent)
            # print(payload)
            
            c1, c2 = st.columns(2)
            with c1:
                good = st.button("Helpful")
            with c2:
                bad = st.button("Not helpful")
            if good:
                log_feedback(1)
            if bad:
                log_feedback(-1)
            charts = render_charts(intent, payload)

            pdf_bytes, file_name = build_pdf(intent, payload, question, answer, charts)
            st.download_button(
                "Export PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
            )
            if charts:
                st.subheader("Chart")
                for fig in charts:
                    st.pyplot(fig, clear_figure=True)

    except Exception as e:
        st.error(f"Error: {e}")
