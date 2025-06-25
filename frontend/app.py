import streamlit as st
import requests

# ──────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="CallMate AI", page_icon="📞", layout="centered")
st.title("📞 CallMate AI – Real-Time Call Assistant")
st.markdown("Enter a customer message to simulate a live call:")

# ──────────────────────────────────────────────────────────────
# User input
# ──────────────────────────────────────────────────────────────
text_input = st.text_input(
    "Customer says:",
    placeholder="e.g., I'm not happy with the delivery…",
)
call_id = "demo-call-123"

# Initialise session keys so Streamlit doesn’t error on first run
for key in ("last_resp", "last_input"):
    if key not in st.session_state:
        st.session_state[key] = None

# ──────────────────────────────────────────────────────────────
# Fetch suggestion only when the button is pressed
# ──────────────────────────────────────────────────────────────
if st.button("🔁 Get Suggestion") and text_input:
    with st.spinner("Analyzing…"):
        try:
            resp = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": call_id},
                timeout=10,
            )
            st.session_state.last_resp = resp.json()
            st.session_state.last_input = text_input
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

# ──────────────────────────────────────────────────────────────
# Display suggestion & feedback UI if we have a stored response
# ──────────────────────────────────────────────────────────────
data = st.session_state.last_resp
if data and "suggestion" in data:

    # Debug panel (raw JSON)
    st.write("📦 Raw Response:", data)

    # Suggested reply
    st.markdown("### 💡 Suggested Response")
    st.success(data["suggestion"])

    # Sentiment badge
    sentiment = data.get("sentiment", "neutral")
    color = {"positive": "green", "negative": "red"}.get(sentiment, "gray")
    st.markdown(
        f"**😐 Sentiment:** "
        f"<span style='color:{color}'>{sentiment.capitalize()}</span>",
        unsafe_allow_html=True,
    )

    # PII badge
    if data.get("pii_redacted"):
        st.markdown("🔒 _Sensitive data automatically masked_")

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
        if st.button("👍 Yes"):
            send_feedback(True)
            st.success("Thanks for your feedback!")

    with col2:
        if st.button("👎 No"):
            send_feedback(False)
            st.warning("Thanks, we’ll improve.")

    # Running totals
    summary = requests.get(
        "http://localhost:8000/feedback/summary", timeout=5
    ).json()
    st.markdown(
        f"**Feedback so far →** "
        f"👍 **{summary['👍']}**  |  👎 **{summary['👎']}**"
    )
