import streamlit as st
import requests

# ──────────────────────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CallMate AI",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <h1 style='text-align: center; font-size: 40px;'>📞 CallMate AI</h1>
    <h4 style='text-align: center; color: gray;'>Your real-time AI-powered call assistant</h4>
    <hr>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# User input
# ──────────────────────────────────────────────────────────────
text_input = st.text_input(
    "💬 Customer says:",
    placeholder="e.g., I still haven’t received my refund…",
)
call_id = "demo-call-123"

# Initialise session keys
for key in ("last_resp", "last_input", "consent_given", "consent_sent"):
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith("consent") else None

# Consent checkbox
st.session_state.consent_given = st.checkbox(
    "I consent to AI-assisted responses being generated and stored."
)

if not st.session_state.consent_given:
    st.info("Please give consent to enable AI suggestions.")

# ──────────────────────────────────────────────────────────────
# Get AI suggestion (only if consent given)
# ──────────────────────────────────────────────────────────────
if (
    st.button("🔁 Get AI Suggestion")
    and text_input
    and st.session_state.consent_given
):
    with st.spinner("💡 Thinking…"):
        try:
            # Send consent once per session
            if not st.session_state.consent_sent:
                requests.post(
                    "http://localhost:8000/consent",
                    params={"call_id": call_id, "consent": True},
                    timeout=5,
                )
                st.session_state.consent_sent = True

            # Get suggestion
            resp = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": call_id},
                timeout=10,
            )
            st.session_state.last_resp = resp.json()
            st.session_state.last_input = text_input
        except Exception as e:
            st.error(f"❌ Backend error: {e}")
            st.stop()

# ──────────────────────────────────────────────────────────────
# Display suggestion & feedback UI
# ──────────────────────────────────────────────────────────────
data = st.session_state.last_resp
if data and "suggestion" in data:
    # Debug panel (raw JSON)
    with st.expander("🔍 Raw backend response"):
        st.json(data)

    # Suggested reply
    st.markdown("### 💡 Suggested Agent Reply")
    st.success(data["suggestion"])

    # Sentiment badge
    sentiment = data.get("sentiment", "neutral")
    color = {"positive": "green", "negative": "red"}.get(sentiment, "gray")
    emoji = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(sentiment, "😐")
    st.markdown(
        f"**{emoji} Sentiment:** "
        f"<span style='color:{color}'>{sentiment.capitalize()}</span>",
        unsafe_allow_html=True,
    )

    # Compliance badge
    if data.get("compliance") == "flagged":
        st.warning("⚠️ Compliance Alert: sensitive terms detected")
    else:
        st.markdown("<span style='color:green'>✔ Compliance: clean</span>", unsafe_allow_html=True)

    # Latency
    st.caption(f"⏱️ LLM latency: {data.get('latency_ms', 0)} ms")

    # PII badge
    if data.get("pii_redacted"):
        st.markdown("🔒 _Sensitive information automatically masked_")

    st.markdown("---")

    # ──────────────────────────────────────────
    # Feedback buttons
    # ──────────────────────────────────────────
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

    with col1:
        if st.button("👍 Yes", key="yes"):
            send_feedback(True)
            st.success("Thanks for your feedback!")

    with col2:
        if st.button("👎 No", key="no"):
            send_feedback(False)
            st.warning("Thanks, we’ll improve!")

    # Feedback summary
    summary = requests.get(
        "http://localhost:8000/feedback/summary", timeout=5
    ).json()
    st.markdown(
        f"<hr><b>🧮 Feedback so far →</b> "
        f"👍 {summary['👍']}  |  👎 {summary['👎']}",
        unsafe_allow_html=True,
    )
