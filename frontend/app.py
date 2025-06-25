import streamlit as st
import requests, tempfile, av
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
from pydub import AudioSegment

# ─────────────────────────────────────────────────────────────
# FFmpeg path for pydub (change if your path differs)
# ─────────────────────────────────────────────────────────────
AudioSegment.converter = (
    r"C:\\Users\\rajat\\Downloads\\Compressed\\ffmpeg-7.1.1-essentials_build"
    r"\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"
)

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

# Audio buffer setup
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = bytearray()

CALL_ID = "demo-call-123"

# ─────────────────────────────────────────────────────────────
# Consent Checkbox
# ─────────────────────────────────────────────────────────────
st.session_state.consent_given = st.checkbox(
    "I consent to AI‑assisted responses being generated and stored."
)

# ------------------------------------------------------------------
# Conversation history bubbles
# ------------------------------------------------------------------
if st.session_state.conversation:
    st.markdown("### 🗒️ Conversation so far")
    for i, line in enumerate(st.session_state.conversation, 1):
        st.markdown(
            f"<div style='background:#F2F6FF;padding:8px;border-radius:10px;margin-bottom:4px'><b>User {i}:</b> {line}</div>",
            unsafe_allow_html=True,
        )
    st.divider()

# ------------------------------------------------------------------
# 🎙️ Voice Mode
# ------------------------------------------------------------------
st.markdown("### 🎙️ Voice Mode (optional)")

class AudioProcessor:
    def recv(self, frame: av.AudioFrame):
        audio_bytes = frame.to_ndarray().tobytes()
        if audio_bytes:
            st.session_state.audio_buffer.extend(audio_bytes)
            print("🔊 Audio frame received —", len(audio_bytes), "bytes")
        return frame

webrtc_streamer(
    key="voice-mode",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"video": False, "audio": True},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_receiver_size=1024,
    audio_frame_callback=AudioProcessor().recv,
)

st.caption(f"🎛️ Bytes captured: {len(st.session_state.audio_buffer)}")

# ------------------------------------------------------------------
# Transcribe button
# ------------------------------------------------------------------
if st.button("🎤 Transcribe Audio"):
    if len(st.session_state.audio_buffer) == 0:
        st.warning("🎙️ No audio yet — click ▶️, speak for 2‑3 s, then try again.")
    else:
        with st.spinner("Transcribing…"):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(st.session_state.audio_buffer)
                wav_path = tmp.name

            st.session_state.audio_buffer = bytearray()

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as src:
                audio = recognizer.record(src)
                try:
                    transcript = recognizer.recognize_google(audio)
                    st.session_state.voice_transcript = transcript
                    st.success(f"🗣️ You said: {transcript}")
                except sr.UnknownValueError:
                    st.error("Couldn’t understand the audio.")
                except sr.RequestError as e:
                    st.error(f"Speech‑to‑text error: {e}")

# ------------------------------------------------------------------
# Text input (prefilled with transcript)
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Submit to backend
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Display backend response
# ------------------------------------------------------------------
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
        st.markdown("🔒 _Sensitive data masked_")

    st.divider()

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
    st.markdown(f"**🧮 Feedback so far →** 👍 {summary['👍']} | 👎 {summary['👎']}", unsafe_allow_html=True)

    st.divider()

    if st.button("📑 End Call & Generate Report"):
        rep = requests.get(f"http://localhost:8000/summary/{CALL_ID}", timeout=10).json()
        st.markdown("## 📑 Post-Call Report")
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
