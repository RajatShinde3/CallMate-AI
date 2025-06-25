import streamlit as st
import requests
import queue, av
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr

# ─────────────────────────────────────────────────────────────
# Streamlit Page Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="CallMate AI", page_icon="📞", layout="centered")

st.markdown(
    """
    <h1 style='text-align:center;font-size:38px;margin-bottom:4px'>📞 CallMate AI</h1>
    <h4 style='text-align:center;color:gray;margin-top:0'>Your real‑time AI‑powered call assistant</h4>
    <hr style='margin-top:8px;margin-bottom:18px'>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Initialise Session State
# ─────────────────────────────────────────────────────────────
for k in (
    "last_resp", "last_input", "consent_given", "consent_sent",
    "conversation", "voice_transcript",
):
    if k not in st.session_state:
        st.session_state[k] = [] if k == "conversation" else None

# Persistent audio frame queue
if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []

CALL_ID = "demo-call-123"

# ─────────────────────────────────────────────────────────────
# Consent Checkbox
# ─────────────────────────────────────────────────────────────
st.session_state.consent_given = st.checkbox(
    "I consent to AI‑assisted responses being generated and stored."
)

# ─────────────────────────────────────────────────────────────
# Conversation history
# ─────────────────────────────────────────────────────────────
if st.session_state.conversation:
    st.markdown("### 🗒️ Conversation so far")
    for i, line in enumerate(st.session_state.conversation, 1):
        st.markdown(
            f"<div style='background:#F2F6FF;padding:8px;border-radius:10px;margin-bottom:4px'><b>User {i}:</b> {line}</div>",
            unsafe_allow_html=True,
        )
    st.divider()

# ─────────────────────────────────────────────────────────────
# 🎧 Voice Mode
# ─────────────────────────────────────────────────────────────
# st.markdown("### 🎧 Voice Mode (optional)")

# class AudioProcessor:
#     def recv(self, frame: av.AudioFrame):
#         # Convert audio frame to PCM (numpy array) and save relevant metadata
#         pcm = frame.to_ndarray()
#         st.session_state.audio_frames.append({
#             "pcm": pcm.tobytes(),
#             "rate": frame.sample_rate,
#             "width": 2  # 2 bytes = 16-bit audio
#         })
#         print(f"🔊 Audio frame received — {len(pcm.tobytes())} bytes")
#         return frame

# webrtc_streamer(
#     key="voice-mode",
#     mode=WebRtcMode.SENDONLY,
#     media_stream_constraints={"video": False, "audio": True},
#     rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
#     audio_receiver_size=1024,
#     audio_frame_callback=AudioProcessor().recv,
# )
# print("✅ WebRTC setup complete. Waiting for audio frames...")

st.caption(f"🎹 frames in queue: {len(st.session_state.audio_frames)}")

st.markdown("### 🎧 Voice Mode via File Upload")

uploaded_file = st.file_uploader("📤 Upload a .wav file to transcribe", type=["wav"])

if uploaded_file is not None:
    with st.spinner("🧠 Transcribing…"):
        recognizer = sr.Recognizer()
        with sr.AudioFile(uploaded_file) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            st.session_state.voice_transcript = text
            st.success(f"🗣️ You said: {text}")
        except sr.UnknownValueError:
            st.error("❌ Couldn’t understand the audio.")
        except sr.RequestError as e:
            st.error(f"❌ STT service error: {e}")

# ─────────────────────────────────────────────────────────────
# Transcribe
# ─────────────────────────────────────────────────────────────
if st.button("🎤 Transcribe Audio"):
    if len(st.session_state.audio_frames) == 0:
        st.warning("🎧 No audio yet — click ▶️, speak for 2–3 seconds, then try again.")
    else:
        with st.spinner("Transcribing…"):
            frame_data = st.session_state.audio_frames[-1]  # Use the last captured audio
            st.session_state.audio_frames = []  # Clear queue

            recognizer = sr.Recognizer()
            audio_data = sr.AudioData(frame_data["pcm"], frame_data["rate"], frame_data["width"])

            try:
                text = recognizer.recognize_google(audio_data)
                st.session_state.voice_transcript = text
                st.success(f"🗣️ You said: {text}")
            except sr.UnknownValueError:
                st.error("Couldn’t understand the audio.")
            except sr.RequestError as e:
                st.error(f"STT error: {e}")


# ─────────────────────────────────────────────────────────────
# Input box
# ─────────────────────────────────────────────────────────────
prefill = st.session_state.voice_transcript or ""
text_input = st.text_input(
    "💬 Customer says:",
    value=prefill,
    placeholder="e.g., I still haven’t received my refund…",
    max_chars=500,
)

btn_disabled = (not st.session_state.consent_given) or (len(text_input.strip()) == 0)
if not st.session_state.consent_given:
    st.caption("⚠️ Tick the consent box to enable suggestions.")
elif len(text_input.strip()) == 0:
    st.caption("⚠️ Type or speak a message.")

# ─────────────────────────────────────────────────────────────
# AI Suggestion
# ─────────────────────────────────────────────────────────────
if st.button("🔁 Get AI Suggestion", disabled=btn_disabled):
    try:
        if not st.session_state.consent_sent:
            requests.post(
                "http://localhost:8000/consent",
                params={"call_id": CALL_ID, "consent": True},
                timeout=5,
            )
            st.session_state.consent_sent = True

        with st.spinner("💡 Thinking…"):
            resp = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": CALL_ID},
                timeout=15,
            )

        st.session_state.last_resp = resp.json()
        st.session_state.last_input = text_input
        st.session_state.conversation.append(text_input)
        st.session_state.voice_transcript = ""

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend error: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Response UI
# ─────────────────────────────────────────────────────────────
data = st.session_state.last_resp
if data and "suggestion" in data:
    st.markdown("### 💡 Suggested Agent Reply")
    st.success(data["suggestion"])

    sent = data.get("sentiment", "neutral")
    col = {"positive": "green", "negative": "red"}.get(sent, "gray")
    emo = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(sent, "😐")
    st.markdown(f"**{emo} Sentiment:** <span style='color:{col}'>{sent.capitalize()}</span>", unsafe_allow_html=True)

    if "confidence" in data:
        c = data["confidence"]
        st.caption(f"🔍 Confidence → Sentiment {int(c['sentiment']*100)}% | Knowledge {int(c['knowledge']*100)}% | Compliance {int(c['compliance']*100)}%")

    if data.get("compliance") == "flagged":
        st.warning("⚠️ Compliance Alert: sensitive terms detected")
    else:
        st.markdown("<span style='color:green'>✔ Compliance: clean</span>", unsafe_allow_html=True)

    st.markdown(f"🚨 **Escalation:** {data.get('escalation','N/A')}")
    st.caption(f"⏱️ LLM latency: {data.get('latency_ms', 0)} ms")

    if data.get("pii_redacted"):
        st.markdown("🔐 _Sensitive data masked_")

    st.divider()

    # Feedback
    st.markdown("### 🗣️ Was this suggestion helpful?")
    c1, c2 = st.columns(2)

    def send_feedback(helpful: bool):
        requests.post(
            "http://localhost:8000/feedback",
            json={"call_id": CALL_ID, "text": st.session_state.last_input, "helpful": helpful},
            timeout=5,
        )

    if c1.button("👍 Yes"):
        send_feedback(True)
        st.success("Thanks for your feedback!")
    if c2.button("👎 No"):
        send_feedback(False)
        st.warning("Thanks, we’ll improve!")

    summary = requests.get("http://localhost:8000/feedback/summary", timeout=5).json()
    st.markdown(f"**🧶 Feedback so far →** 👍 {summary['👍']} | 👎 {summary['👎']}", unsafe_allow_html=True)

    st.divider()

    if st.button("📁 End Call & Generate Report"):
        rep = requests.get(f"http://localhost:8000/summary/{CALL_ID}", timeout=10).json()
        st.markdown("## 📁 Post-Call Report")
        st.write(rep["summary"])
        st.markdown(
            f"**Overall sentiment:** {rep['sentiment_overall'].capitalize()}   \n"
            f"**Compliance:** {rep['compliance_overall']}   \n"
            f"**Escalation:** {rep['escalation']}"
        )
        with st.expander("🗒️ Full conversation context"):
            for line in rep["utterances"]:
                st.write("•", line)

    with st.expander("🔍 Raw backend response"):
        st.json(data)
