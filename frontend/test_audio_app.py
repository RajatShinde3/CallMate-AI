# test_webrtc_audio.py
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av

if "frames" not in st.session_state:
    st.session_state.frames = 0

class AudioProcessor:
    def recv(self, frame: av.AudioFrame):
        st.session_state.frames += 1
        print(f"🔊 Audio frame received — {frame.samples * frame.layout.channels * 2} bytes")
        return frame

webrtc_streamer(
    key="audio-only",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"video": False, "audio": True},
    audio_receiver_size=1024,
    audio_frame_callback=AudioProcessor().recv,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
)

st.write(f"🎧 Audio frames received: {st.session_state.frames}")
