import streamlit as st, requests

st.set_page_config(page_title="CallMate AI", page_icon="📞")
st.title("📞 CallMate AI – Demo v0.1")

text_input = st.text_input("Say something (simulate transcript)")
call_id = "demo-call-123"

if st.button("Send to backend") and text_input:
    resp = requests.post(
        "http://localhost:8000/suggest",
        json={"text": text_input, "call_id": call_id},
        timeout=5,
    )
    if resp.ok:
        data = resp.json()
        st.success(f"💡 Suggestion: {data['suggestion']}")
        st.info(f"😃 Sentiment: {data['sentiment']}")
    else:
        st.error("Backend error")
