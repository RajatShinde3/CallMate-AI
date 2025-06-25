import streamlit as st
import requests, queue, tempfile, av, uuid
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
from pydub import AudioSegment
import os

# ────────────────────────── FFmpeg path ──────────────────────────
AudioSegment.converter = (
    r"C:\\Users\\rajat\\Downloads\\Compressed\\ffmpeg-7.1.1-essentials_build"
    r"\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"
)

# ────────────────────────── Page config ──────────────────────────
st.set_page_config(page_title="CallMate AI", page_icon="📞", layout="centered")

st.markdown("""
    <h1 style='text-align:center;font-size:38px;margin-bottom:4px'>📞 CallMate AI</h1>
    <h4 style='text-align:center;color:gray;margin-top:0'>Your real‑time AI‑powered call assistant</h4>
    <hr style='margin-top:8px;margin-bottom:18px'>
""", unsafe_allow_html=True)

# ───────────────────── Session‑state initialisation ─────────────────────
for k in ("last_resp", "last_input", "consent_given", "consent_sent", "conversation", "voice_transcript"):
    if k not in st.session_state:
        st.session_state[k] = [] if k == "conversation" else None

if "audio_q" not in st.session_state:
    st.session_state.audio_q = queue.Queue()
audio_q: queue.Queue = st.session_state.audio_q

CALL_ID = "demo-" + uuid.uuid4().hex[:8]

# ────────────────────────── Consent checkbox ──────────────────────────
st.session_state.consent_given = st.checkbox(
    "I consent to AI‑assisted responses being generated and stored."
)

# ────────────────────────── Voice Mode ──────────────────────────
st.markdown("### 🎙️ Voice Mode (optional)")

class AudioProcessor:
    def recv(self, frame: av.AudioFrame):
        pcm = frame.to_ndarray()
        st.session_state.audio_format = {
            "sample_rate": frame.sample_rate,
            "channels": frame.layout.channels,
            "sample_width": 2  # 16-bit PCM = 2 bytes
        }
        audio_q.put(pcm.tobytes())
        print(f"🔊 audio frame received — shape: {pcm.shape}, queue size: {audio_q.qsize()}")
        return frame

webrtc_streamer(
    key="voice-mode",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"video": False, "audio": True},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_receiver_size=1024,
    audio_frame_callback=AudioProcessor().recv,
)

st.caption(f"🎛️ frames in queue: {audio_q.qsize()}")

# ────────────────────────── Transcribe button ──────────────────────────
if st.button("🎤 Transcribe Audio"):
    if audio_q.qsize() == 0:
        st.warning("🎙️ No audio yet — click ▶️, speak 2‑3 s, then retry.")
    else:
        with st.spinner("Transcribing…"):
            raw_bytes = b"".join(list(audio_q.queue))
            audio_q.queue.clear()

            if len(raw_bytes) < 10000:
                st.warning("🎤 Audio too short or unclear. Try again.")
            else:
                fmt = st.session_state.get("audio_format", {
                    "sample_rate": 48000,
                    "channels": 2,
                    "sample_width": 2
                })

                audio_seg = AudioSegment(
                    data=raw_bytes,
                    sample_width=fmt["sample_width"],
                    frame_rate=fmt["sample_rate"],
                    channels=fmt["channels"],
                ).set_frame_rate(16000).set_channels(1).set_sample_width(2)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    audio_seg.export(tmp_wav.name, format="wav")
                    wav_path = tmp_wav.name

                st.audio(wav_path, format="audio/wav")

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as src:
                    audio_data = recognizer.record(src)
                    try:
                        text = recognizer.recognize_google(audio_data)
                        st.session_state.voice_transcript = text
                        st.success(f"🗣️ You said: {text}")
                    except sr.UnknownValueError:
                        st.error("Couldn’t understand the audio.")
                    except sr.RequestError as e:
                        st.error(f"Speech‑to‑text error: {e}")

# ────────────────────────── Text input box ──────────────────────────
text_input = st.text_input(
    "💬 Customer says:",
    value=st.session_state.voice_transcript or "",
    placeholder="e.g., I still haven’t received my refund…",
)

disabled_btn = (not st.session_state.consent_given) or (len(text_input.strip()) == 0)

if not st.session_state.consent_given:
    st.caption("⚠️ Tick the consent box to enable suggestions.")
elif len(text_input.strip()) == 0:
    st.caption("⚠️ Type or speak a message.")

# ────────────────────────── Send to backend ──────────────────────────
if st.button("🔁 Get AI Suggestion", disabled=disabled_btn):
    try:
        if not st.session_state.consent_sent:
            requests.post(
                "http://localhost:8000/consent",
                params={"call_id": CALL_ID, "consent": True},
                timeout=5,
            )
            st.session_state.consent_sent = True

        with st.spinner("💡 Thinking…"):
            r = requests.post(
                "http://localhost:8000/suggest",
                json={"text": text_input, "call_id": CALL_ID},
                timeout=15,
            )
        st.session_state.last_resp = r.json()
        st.session_state.last_input = text_input
        st.session_state.conversation.append(text_input)
        st.session_state.voice_transcript = ""
    except requests.exceptions.RequestException as e:
        st.error(f"Backend error: {e}")

# ────────────────────────── Display response ──────────────────────────
data = st.session_state.last_resp
if data and "suggestion" in data:
    st.markdown("### 💡 Suggested Reply")
    st.success(data["suggestion"])
