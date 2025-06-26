import streamlit as st
import requests, queue, tempfile, av, uuid, os
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
from pydub import AudioSegment
import pandas as pd
import altair as alt

# ─────────────────────────────────────────────────────────────
# 1️⃣ FFmpeg Path Configuration (Required by pydub)
# ─────────────────────────────────────────────────────────────
AudioSegment.converter = (
    r"C:\\Users\\rajat\\Downloads\\Compressed\\ffmpeg-7.1.1-essentials_build"
    r"\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"
)

# ─────────────────────────────────────────────────────────────
# 2️⃣ Streamlit Page Configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="CallMate AI", page_icon="📞", layout="centered")

st.markdown(
    """
    <style>
    body { font-family: 'Segoe UI', sans-serif; }
    .st-emotion-cache-1v0mbdj { padding: 2rem 1rem !important; }
    h1, h2, h3, h4, h5 { font-family: 'Segoe UI Semibold', sans-serif; }
    .metric { text-align: center !important; }
    </style>
    <h1 style='text-align:center;font-size:42px;margin-bottom:8px;color:#2E86C1;'>📞 CallMate AI</h1>
    <h4 style='text-align:center;color:#7F8C8D;margin-top:0'>Your real‑time AI‑powered call assistant</h4>
    <hr style='margin-top:10px;margin-bottom:25px;border:1px solid #D0D3D4;'>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# 3️⃣ Initialize Session State
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
        st.session_state[key] = [] if key in ("conversation", "latency_list") else None

if "audio_q" not in st.session_state:
    st.session_state.audio_q = queue.Queue()
audio_q: queue.Queue = st.session_state.audio_q

CALL_ID = "demo-" + uuid.uuid4().hex[:8]

# ─────────────────────────────────────────────────────────────
# 4️⃣ Tabs (must be defined before use)
# ─────────────────────────────────────────────────────────────
tab_main, tab_dash = st.tabs(["💬 Assistant", "📊 Dashboard"])

# ─────────────────────────────────────────────────────────────
# 5️⃣ TAB 1 – Assistant
# ─────────────────────────────────────────────────────────────
with tab_main:
    st.markdown("### 🔐 Consent", unsafe_allow_html=True)
    st.session_state.consent_given = st.checkbox(
        "I consent to AI-assisted responses being generated and stored."
    )

    st.markdown("---")

    st.markdown("### 🎙️ Voice Mode (Real-time)")
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

    st.markdown("---")
    st.markdown("### 📂 Upload Audio File (.wav)")
    uploaded_file = st.file_uploader("Upload and transcribe:", type=["wav"])
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

    if st.button("🎤 Transcribe Audio"):
        if audio_q.qsize() == 0:
            st.warning("🎵 No audio yet — click ▶️, speak for 2–3 seconds, then try again.")
        else:
            with st.spinner("Transcribing…"):
                raw_bytes = b"".join(list(audio_q.queue))
                audio_q.queue.clear()
                if len(raw_bytes) < 10000:
                    st.warning("🔊 Audio too short or unclear. Try again.")
                else:
                    fmt = st.session_state.get("audio_format", {"sample_rate": 48000, "channels": 2, "sample_width": 2})
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
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
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

    st.markdown("---")

    st.markdown("### 🧾 Customer Statement & AI Suggestion")
    text_input = st.text_input("💬 Customer says:", value=st.session_state.voice_transcript or "", max_chars=500, placeholder="e.g., I still haven’t received my refund…")

    if not st.session_state.consent_given:
        st.warning("⚠️ Please tick the consent box to continue.")

    if st.button("🔁 Get AI Suggestion", disabled=(not st.session_state.consent_given or len(text_input.strip()) == 0)):
        try:
            if not st.session_state.consent_sent:
                requests.post("http://localhost:8000/consent", params={"call_id": CALL_ID, "consent": True}, timeout=5)
                st.session_state.consent_sent = True
            with st.spinner("💡 Thinking…"):
                resp = requests.post("http://localhost:8000/suggest", json={"text": text_input, "call_id": CALL_ID}, timeout=15)
            data = resp.json()
            st.session_state.last_resp = data
            sanitized = data.get("redacted_text", text_input)
            st.session_state.last_input = sanitized
            st.session_state.conversation.append(sanitized)
            st.session_state.voice_transcript = ""
            if "latency_ms" in data:
                st.session_state.latency_list.append(data["latency_ms"])
        except Exception as e:
            st.error(f"❌ Error: {e}")

    # 🧠 Output Response
    data = st.session_state.last_resp
    if data and "suggestion" in data:
        st.success("💡 " + data["suggestion"])
        sent = data.get("sentiment", "neutral")
        col = {"positive": "green", "negative": "red"}.get(sent, "gray")
        emo = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(sent, "😐")
        st.markdown(f"**{emo} Sentiment:** <span style='color:{col}'>{sent.capitalize()}</span>", unsafe_allow_html=True)
        if data.get("compliance") == "flagged":
            st.warning("⚠️ Compliance Alert: sensitive terms detected")
        else:
            st.markdown("<span style='color:green'>✔ Compliance: clean</span>", unsafe_allow_html=True)
        st.caption(f"⏱️ Latency: {data.get('latency_ms', 0)} ms")
        if data.get("pii_redacted"):
            st.markdown("🔐 _Sensitive data masked_")

        # Feedback
        st.markdown("### 🗣️ Was this suggestion helpful?")
        fb1, fb2 = st.columns(2)
        def send_fb(helpful: bool):
            requests.post("http://localhost:8000/feedback", json={"call_id": CALL_ID, "text": st.session_state.last_input, "helpful": helpful}, timeout=5)
        if fb1.button("👍 Yes"):
            send_fb(True)
            st.success("Thanks!")
        if fb2.button("👎 No"):
            send_fb(False)
            st.warning("We’ll improve!")

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
            with st.expander("🧾 Full JSON Report View"):
                st.json(rep)

# ─────────────────────────────────────────────────────────────
# 6️⃣ TAB 2 – Dashboard – Polished, Enhanced, and Visualized
# ─────────────────────────────────────────────────────────────
with tab_dash:
    st.markdown("## 📊 CallMate AI – Live Dashboard")
    st.caption("Real-time insights & agent performance analytics")

    try:
        # Feedback summary from backend
        summary = requests.get("http://localhost:8000/feedback/summary", timeout=5).json()
        total_fb = summary.get("👍", 0) + summary.get("👎", 0)
        helpful_pct = summary.get("👍", 0) / total_fb * 100 if total_fb else 0
        avg_latency = (
            sum(st.session_state.latency_list) / len(st.session_state.latency_list)
            if st.session_state.latency_list else 0
        )
        esc = requests.get(f"http://localhost:8000/summary/{CALL_ID}", timeout=5).json()
        voice_quality = esc.get("voice_quality", 88)

        # 🔹 KPI Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("👍 Helpful", summary.get("👍", 0), help="Positive feedback")
        m2.metric("👎 Unhelpful", summary.get("👎", 0), help="Negative feedback")
        m3.metric("📊 Total Feedback", total_fb)

        m4, m5, m6 = st.columns(3)
        m4.metric("⚠️ Escalation", esc.get("escalation", "N/A"))
        m5.metric("⏱️ Avg Latency (ms)", int(avg_latency))
        m6.metric("🎙️ Voice Quality", f"{voice_quality}%", help="Based on audio clarity/signal")

        # 🔸 Helpful Ratio
        st.subheader("🧮 Helpful Feedback Ratio")
        st.progress(helpful_pct / 100)
        st.caption(f"{helpful_pct:.1f}% of all feedback is marked as helpful")

        # 🔸 Escalation Notice
        if esc.get("escalation") == "Recommended":
            st.warning("⚠️ Escalation recommended for this session")
        else:
            st.success("✅ No escalation needed")

        # 🔸 Feedback History + Graph
        feedback_data = requests.get("http://localhost:8000/feedback/history", timeout=5).json()

        if isinstance(feedback_data, list) and any("timestamp" in f for f in feedback_data):
            # Filter out entries without timestamp
            clean_data = [f for f in feedback_data if "timestamp" in f]
            feedback_df = pd.DataFrame(clean_data)
            feedback_df["timestamp"] = pd.to_datetime(feedback_df["timestamp"])
            feedback_df["feedback"] = feedback_df["helpful"].map({True: "👍", False: "👎"})

            import plotly.express as px
            fig = px.scatter(
                feedback_df,
                x="timestamp",
                y="feedback",
                title="🕒 Feedback Timeline",
                color="feedback",
                color_discrete_map={"👍": "#2ECC71", "👎": "#E74C3C"},
                height=400,
            )
            fig.update_layout(yaxis_title="Feedback")
            st.plotly_chart(fig, use_container_width=True)

            # 🔸 Feedback Table & Export
            st.subheader("📄 Feedback Log")
            st.dataframe(feedback_df[["timestamp", "text", "feedback"]], use_container_width=True)

            csv = feedback_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Feedback as CSV",
                csv,
                "callmate_feedback.csv",
                "text/csv",
                help="Export feedback for auditing/reporting"
            )
        else:
            st.info("ℹ️ No timestamped feedback yet. Try interacting with the Assistant tab.")

    except Exception as err:
        st.error("🚨 Dashboard Error")
        st.exception(err)
