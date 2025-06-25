import streamlit as st
import requests

# ─────────────────────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CallMate AI",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <h1 style='text-align:center;font-size:38px;margin-bottom:4px'>📞 CallMate AI</h1>
    <h4 style='text-align:center;color:gray;margin-top:0'>
        Your real-time AI-powered call assistant
    </h4>
    <hr style='margin-top:8px;margin-bottom:18px'>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Session Keys
# ─────────────────────────────────────────────────────────────
for key in (
    "last_resp",
    "last_input",
    "consent_given",
    "consent_sent",
    "conversation",
):
    if key not in st.session_state:
        st.session_state[key] = [] if key == "conversation" else None

call_id = "demo-call-123"

# ─────────────────────────────────────────────────────────────
# Inputs (NO form, to let disabled flag recalc every rerun)
# ─────────────────────────────────────────────────────────────
st.session_state.consent_given = st.checkbox(
    "I consent to AI-assisted responses being generated and stored.",
)

text_input = st.text_input(
    "💬 Customer says:",
    value="",
    placeholder="e.g., I still haven’t received my refund…",
    max_chars=500,
)

# Live-update disabled flag
button_disabled = (not st.session_state.consent_given) or (len(text_input.strip()) == 0)

# Show validation hints
if not st.session_state.consent_given:
    st.caption("⚠️ Please tick the consent box.")
elif len(text_input.strip()) == 0:
    st.caption("⚠️ Type a customer message.")

# ─────────────────────────────────────────────────────────────
# Submit Button (disabled until valid)
# ─────────────────────────────────────────────────────────────
if st.button("🔁 Get AI Suggestion", disabled=button_disabled):
    # Button is enabled ⇒ both conditions true
    try:
        # Send consent once
        if not st.session_state.consent_sent:
            requests.post(
                "http://localhost:8000/consent",
                params={"call_id": call_id, "consent": True},
                timeout=5,
            )
            st.session_state.consent_sent = True

        with st.spinner("💡 Thinking…"):
            resp = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": call_id},
                timeout=10,
            )

        st.session_state.last_resp = resp.json()
        st.session_state.last_input = text_input
        st.session_state.conversation.append(text_input)

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend connection error: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Display AI Response (unchanged from earlier)
# ─────────────────────────────────────────────────────────────
data = st.session_state.last_resp
if data and "suggestion" in data:
    st.markdown("### 💡 Suggested Agent Reply")
    st.success(data["suggestion"])

    sentiment = data.get("sentiment", "neutral")
    color = {"positive": "green", "negative": "red"}.get(sentiment, "gray")
    emoji = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(sentiment, "😐")
    st.markdown(
        f"**{emoji} Sentiment:** "
        f"<span style='color:{color}'>{sentiment.capitalize()}</span>",
        unsafe_allow_html=True,
    )

    compliance = data.get("compliance", "clean")
    if compliance == "flagged":
        st.warning("⚠️ Compliance Alert: sensitive terms detected")
    else:
        st.markdown(
            "<span style='color:green'>✔ Compliance: clean</span>",
            unsafe_allow_html=True,
        )

    st.markdown(f"🚨 **Escalation:** {data.get('escalation', 'N/A')}")
    st.caption(f"⏱️ LLM latency: {data.get('latency_ms', 0)} ms")

    if data.get("pii_redacted"):
        st.markdown("🔒 _Sensitive information automatically masked_")

    st.divider()

    # Feedback UI
    st.markdown("### 🗣️ Was this suggestion helpful?")
    col1, col2 = st.columns(2)

    def send_feedback(helpful: bool):
        requests.post(
            "http://localhost:8000/feedback",
            json={
                "call_id": call_id,
                "text": st.session_state.last_input,
                "helpful": helpful,
            },
            timeout=5,
        )

    if col1.button("👍 Yes"):
        send_feedback(True)
        st.success("Thanks for your feedback!")
    if col2.button("👎 No"):
        send_feedback(False)
        st.warning("Thanks, we’ll improve!")

    summary = requests.get("http://localhost:8000/feedback/summary", timeout=5).json()
    st.markdown(
        f"**🧮 Feedback so far →** 👍 {summary['👍']} | 👎 {summary['👎']}",
        unsafe_allow_html=True,
    )

    st.divider()

    # Post-Call Summary
    if st.button("📑 End Call & Generate Report"):
        report = requests.get(f"http://localhost:8000/summary/{call_id}", timeout=10).json()
        st.markdown("## 📑 Post-Call Report")
        st.write(report["summary"])
        st.markdown(
            f"**Overall sentiment:** {report['sentiment_overall'].capitalize()}  \n"
            f"**Compliance:** {report['compliance_overall']}  \n"
            f"**Escalation:** {report['escalation']}"
        )
        with st.expander("🗒️ Full conversation context"):
            for line in report["utterances"]:
                st.write("•", line)

    with st.expander("🔍 Raw backend response"):
        st.json(data)
