import streamlit as st
import requests, queue, tempfile, av, uuid
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
from pydub import AudioSegment
import os
import pandas as pd
import altair as alt

# ─────────────────────────────────────────────────────────────
# FFmpeg Path Configuration (Required by pydub)
# ─────────────────────────────────────────────────────────────
AudioSegment.converter = (
    r"C:\\Users\\rajat\\Downloads\\Compressed\\ffmpeg-7.1.1-essentials_build"
    r"\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"
)

# ─────────────────────────────────────────────────────────────
# Streamlit Page Configuration
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
# Initialize Session State
# ─────────────────────────────────────────────────────────────
for key in (
    "last_resp",
    "last_input",
    "consent_given",
    "consent_sent",
    "conversation",
    "voice_transcript",
    "latency_list",
):
    if key not in st.session_state:
        st.session_state[key] = (
            [] if key in ("conversation", "latency_list") else None
        )

# queue for live audio
if "audio_q" not in st.session_state:
    st.session_state.audio_q = queue.Queue()
audio_q: queue.Queue = st.session_state.audio_q

CALL_ID = "demo-" + uuid.uuid4().hex[:8]  # unique per session

# ────────────────── Tabs (must be defined before use) ───────────────────────
tab_main, tab_dash = st.tabs(["Assistant", "Dashboard"])

# ─────────────────────────────────────────────────────────────
# Consent
# ─────────────────────────────────────────────────────────────
st.session_state.consent_given = st.checkbox(
    "I consent to AI‑assisted responses being generated and stored."
)

# ─────────────────────────────────────────────────────────────
# Voice Input (WebRTC)
# ─────────────────────────────────────────────────────────────
st.markdown("### 🎙️ Voice Mode (optional)")

class AudioProcessor:
    def recv(self, frame: av.AudioFrame):
        pcm = frame.to_ndarray()
        st.session_state.audio_format = {
            "sample_rate": frame.sample_rate,
            "channels": frame.layout.channels,
            "sample_width": 2  # 16-bit PCM
        }
        audio_q.put(pcm.tobytes())
        # print("🔊 audio frame received — queue size:", audio_q.qsize())
        return frame

webrtc_streamer(
    key="voice-mode",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"video": False, "audio": True},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_receiver_size=1024,
    audio_frame_callback=AudioProcessor().recv,
)

st.caption(f"🎧 Frames in queue: {audio_q.qsize()}")

# ─────────────────────────────────────────────────────────────
# File Upload Option
# ─────────────────────────────────────────────────────────────
st.markdown("### 🎙️ Voice Mode via File Upload")
uploaded_file = st.file_uploader("📄 Upload a .wav file to transcribe", type=["wav"])

if uploaded_file is not None:
    with st.spinner("🧠 Transcribing..."):
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
# Transcribe from WebRTC
# ─────────────────────────────────────────────────────────────
if st.button("🎤 Transcribe Audio"):
    if audio_q.qsize() == 0:
        st.warning("🎵 No audio yet — click ▶️, speak for 2–3 seconds, then try again.")
    else:
        with st.spinner("Transcribing..."):
            raw_bytes = b"".join(list(audio_q.queue))
            audio_q.queue.clear()

            if len(raw_bytes) < 10000:
                st.warning("🔊 Audio too short or unclear. Try again.")
            else:
                fmt = st.session_state.get("audio_format", {"sample_rate": 48000, "channels": 2, "sample_width": 2})

                audio_seg = AudioSegment(
                    data=raw_bytes,
                    sample_width=fmt["sample_width"],
                    frame_rate=fmt["sample_rate"],
                    channels=fmt["channels"],
                ).set_frame_rate(16000).set_channels(1).set_sample_width(2)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    audio_seg.export(tmp_wav.name, format="wav")
                    wav_path = tmp_wav.name

                # st.audio(wav_path, format="audio/wav")

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

# ─────────────────────────────────────────────────────────────
# Input + Suggestion Logic
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

if st.button("🔁 Get AI Suggestion", disabled=btn_disabled):
    try:
        if not st.session_state.consent_sent:
            requests.post("http://localhost:8000/consent", params={"call_id": CALL_ID, "consent": True}, timeout=5)
            st.session_state.consent_sent = True

        with st.spinner("💡 Thinking..."):
            resp = requests.post("http://localhost:8000/suggest", json={"text": text_input, "call_id": CALL_ID}, timeout=15)

        data = resp.json()

        st.session_state.last_resp = resp.json()
        sanitized_text = data.get("redacted_text", text_input)
        st.session_state.last_input = sanitized_text
        st.session_state.conversation.append(sanitized_text)
        st.session_state.voice_transcript = ""

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend error: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Output Response UI
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

    st.markdown("### 🗣️ Was this suggestion helpful?")
    c1, c2 = st.columns(2)

    def send_feedback(helpful: bool):
        requests.post("http://localhost:8000/feedback", json={"call_id": CALL_ID, "text": st.session_state.last_input, "helpful": helpful}, timeout=5)

    if c1.button("👍 Yes"):
        send_feedback(True)
        st.success("Thanks for your feedback!")
    if c2.button("👎 No"):
        send_feedback(False)
        st.warning("Thanks, we’ll improve!")

    summary = requests.get("http://localhost:8000/feedback/summary", timeout=5).json()
    st.markdown(f"**🧦 Feedback so far →** 👍 {summary['👍']} | 👎 {summary['👎']}", unsafe_allow_html=True)

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
        with st.expander("📒 Full conversation context"):
            for line in rep["utterances"]:
                st.write("•", line)

    with st.expander("🔍 Raw backend response"):
        st.json(data)
        
# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 – Assistant
# ─────────────────────────────────────────────────────────────────────────────
with tab_main:

    # 1️⃣ Consent checkbox
    st.session_state.consent_given = st.checkbox(
        "I consent to AI-assisted responses being generated and stored."
    )

    # 2️⃣ Voice input (WebRTC)
    st.markdown("### 🎙️ Voice Mode (optional)")
    class AudioProcessor:
        def recv(self, frame: av.AudioFrame):
            audio_q.put(frame.to_ndarray().tobytes())
            st.session_state.audio_format = {
                "sample_rate": frame.sample_rate,
                "channels": frame.layout.channels,
                "sample_width": 2,
            }
            return frame

    webrtc_streamer(
        key="voice-mode",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"video": False, "audio": True},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        audio_receiver_size=1024,
        audio_frame_callback=AudioProcessor().recv,
    )
    st.caption(f"🎧 Frames in queue: {audio_q.qsize()}")

    # 3️⃣ Upload .wav
    st.markdown("### 🎙️ Voice Mode via File Upload")
    uploaded_file = st.file_uploader(
        "📄 Upload a .wav file to transcribe", type=["wav"]
    )
    if uploaded_file:
        with st.spinner("🧠 Transcribing…"):
            rec = sr.Recognizer()
            with sr.AudioFile(uploaded_file) as src:
                audio_data = rec.record(src)
            try:
                text = rec.recognize_google(audio_data)
                st.session_state.voice_transcript = text
                st.success(f"🗣️ You said: {text}")
            except sr.UnknownValueError:
                st.error("Couldn’t understand the audio.")
            except sr.RequestError as e:
                st.error(f"STT service error: {e}")

    # 4️⃣ Transcribe from live mic
    if st.button("🎤 Transcribe Audio"):
        if audio_q.qsize() == 0:
            st.warning("🎵 No audio yet — click ▶️, speak 2-3 s, then try again.")
        else:
            with st.spinner("Transcribing…"):
                raw_bytes = b"".join(list(audio_q.queue))
                audio_q.queue.clear()
                if len(raw_bytes) < 10000:
                    st.warning("🔊 Audio too short or unclear. Try again.")
                else:
                    fmt = st.session_state.get(
                        "audio_format",
                        {"sample_rate": 48000, "channels": 2, "sample_width": 2},
                    )
                    audio_seg = (
                        AudioSegment(
                            data=raw_bytes,
                            sample_width=fmt["sample_width"],
                            frame_rate=fmt["sample_rate"],
                            channels=fmt["channels"],
                        )
                        .set_frame_rate(16000)
                        .set_channels(1)
                        .set_sample_width(2)
                    )
                    with tempfile.NamedTemporaryFile(
                        suffix=".wav", delete=False
                    ) as tmp_wav:
                        audio_seg.export(tmp_wav.name, format="wav")
                        wav_path = tmp_wav.name
                    rec = sr.Recognizer()
                    with sr.AudioFile(wav_path) as src:
                        audio = rec.record(src)
                        try:
                            text = rec.recognize_google(audio)
                            st.session_state.voice_transcript = text
                            st.success(f"🗣️ You said: {text}")
                        except sr.UnknownValueError:
                            st.error("Couldn’t understand the audio.")
                        except sr.RequestError as e:
                            st.error(f"Speech-to-text error: {e}")

    # 5️⃣ Manual text box / AI suggestion
    text_prefill = st.session_state.voice_transcript or ""
    text_input = st.text_input(
        "💬 Customer says:",
        value=text_prefill,
        placeholder="e.g., I still haven’t received my refund…",
        max_chars=500,
    )

    disabled_btn = (
        not st.session_state.consent_given or len(text_input.strip()) == 0
    )
    if not st.session_state.consent_given:
        st.caption("⚠️ Tick the consent box to enable suggestions.")
    elif len(text_input.strip()) == 0:
        st.caption("⚠️ Type or speak a message.")

    if st.button("🔁 Get AI Suggestion", disabled=disabled_btn):
        try:
            # send consent first time
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
            data = resp.json()
            st.session_state.last_resp = data
            sanitized = data.get("redacted_text", text_input)
            st.session_state.last_input = sanitized
            st.session_state.conversation.append(sanitized)
            st.session_state.voice_transcript = ""
            # store latency for dashboard avg
            if "latency_ms" in data:
                st.session_state.latency_list.append(data["latency_ms"])

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Backend error: {e}")
            st.stop()

    # 6️⃣ Show AI reply and feedback
    data = st.session_state.last_resp
    if data and "suggestion" in data:
        st.markdown("### 💡 Suggested Agent Reply")
        st.success(data["suggestion"])

        # meta info
        sent = data.get("sentiment", "neutral")
        color = {"positive": "green", "negative": "red"}.get(sent, "gray")
        emoji = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(sent, "😐")
        st.markdown(
            f"**{emoji} Sentiment:** "
            f"<span style='color:{color}'>{sent.capitalize()}</span>",
            unsafe_allow_html=True,
        )

        if data.get("compliance") == "flagged":
            st.warning("⚠️ Compliance Alert: sensitive terms detected")
        else:
            st.markdown(
                "<span style='color:green'>✔ Compliance: clean</span>",
                unsafe_allow_html=True,
            )

        st.caption(f"⏱️ Latency: {data.get('latency_ms', 0)} ms")
        if data.get("pii_redacted"):
            st.markdown("🔐 _Sensitive data masked_")

        st.markdown("### 🗣️ Was this suggestion helpful?")
        fb1, fb2 = st.columns(2)

        def send_fb(helpful: bool):
            requests.post(
                "http://localhost:8000/feedback",
                json={
                    "call_id": CALL_ID,
                    "text": st.session_state.last_input,
                    "helpful": helpful,
                },
                timeout=5,
            )

        if fb1.button("👍 Yes"):
            send_fb(True)
            st.success("Thanks!")
        if fb2.button("👎 No"):
            send_fb(False)
            st.warning("We'll improve!")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 – Dashboard
# ─────────────────────────────────────────────────────────────────────────────
with tab_dash:
    st.markdown("## 📊 CallMate AI – Live Dashboard")
    st.caption("Aggregated metrics for the current session")

    try:
        # Feedback counts
        summary = requests.get(
            "http://localhost:8000/feedback/summary", timeout=5
        ).json()
        total_fb = summary.get("👍", 0) + summary.get("👎", 0)
        helpful_pct = (
            summary.get("👍", 0) / total_fb * 100 if total_fb else 0
        )

        # Latency average
        if st.session_state.latency_list:
            avg_latency = sum(st.session_state.latency_list) / len(
                st.session_state.latency_list
            )
        else:
            avg_latency = 0

        # Escalation (last call only)
        esc = requests.get(
            f"http://localhost:8000/summary/{CALL_ID}", timeout=5
        ).json()

        # Metrics grid
        m1, m2, m3 = st.columns(3)
        m1.metric("👍 Helpful", summary.get("👍", 0))
        m2.metric("👎 Unhelpful", summary.get("👎", 0))
        m3.metric("📊 Total FB", total_fb)

        m4, m5 = st.columns(2)
        m4.metric("⚠️ Escalation", esc.get("escalation", "N/A"))
        m5.metric("⏱️ Avg Latency (ms)", int(avg_latency))

        # Helpful ratio bar
        st.subheader("🧮 Feedback Ratio")
        st.progress(helpful_pct / 100)
        st.caption(f"{helpful_pct:.1f}% of feedback is 👍 helpful")

        # Optional: escalate banner
        if esc.get("escalation") == "Recommended":
            st.warning("⚠️ Escalation recommended for this session")
        else:
            st.success("✅ No escalation needed")

    except Exception as err:
        st.error("Dashboard error")
        st.exception(err)
