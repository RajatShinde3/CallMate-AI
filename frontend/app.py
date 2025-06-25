import streamlit as st
import requests

# Streamlit page setup
st.set_page_config(page_title="CallMate AI", page_icon="📞", layout="centered")
st.title("📞 CallMate AI – Real-Time Call Assistant")

st.markdown("Enter customer message below to simulate real-time AI suggestion:")

# Simulated transcript input
text_input = st.text_input("Customer says:", placeholder="e.g., I'm not happy with the delivery...")
call_id = "demo-call-123"

if st.button("🔁 Get Suggestion") and text_input:
    with st.spinner("Analyzing..."):
        try:
            resp = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": call_id},
                timeout=10,
            )
            data = resp.json()

            # Debug view
            st.write("📦 Raw Response:", data)

            if "suggestion" in data:
                # 🎯 Suggestion display
                st.markdown("### 💡 Suggested Response")
                st.success(data["suggestion"])

                # 😄 Sentiment indicator
                sentiment = data.get("sentiment", "neutral")
                if sentiment == "positive":
                    st.markdown("**😊 Sentiment:** <span style='color:green'>Positive</span>", unsafe_allow_html=True)
                elif sentiment == "negative":
                    st.markdown("**😠 Sentiment:** <span style='color:red'>Negative</span>", unsafe_allow_html=True)
                else:
                    st.markdown("**😐 Sentiment:** <span style='color:gray'>Neutral</span>", unsafe_allow_html=True)

                # 👍 👎 Feedback buttons
                st.markdown("### 🗣️ Was this suggestion helpful?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Yes"):
                        st.success("Feedback recorded. Thanks!")
                with col2:
                    if st.button("👎 No"):
                        st.warning("We'll use your feedback to improve.")
            else:
                st.error("❌ Suggestion not found in response.")
        except Exception as e:
            st.error(f"Backend error: {e}")
