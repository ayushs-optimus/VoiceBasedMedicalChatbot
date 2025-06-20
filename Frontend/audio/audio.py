import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import numpy as np
import requests

# WebRTC client config
RTC_CONFIGURATION = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
)

# Audio recorder callback
class AudioProcessor:
    def __init__(self):
        self.buffer = []

    def recv(self, frame: av.AudioFrame):
        pcm = frame.to_ndarray().flatten().astype(np.int16)
        self.buffer.append(pcm.tobytes())
        return frame

st.title("🎙️ Voice-based RAG Chatbot")

# Start/Stop buttons
st.subheader("Microphone Input")
ctx = webrtc_streamer(
    key="mic",
    mode=WebRtcMode.SENDONLY,
    client_settings=RTC_CONFIGURATION,
    audio_receiver_size=1024,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
    processor_factory=AudioProcessor,
)

# When recording stops
if ctx.state.playing:
    st.info("Recording...")
else:
    if ctx.audio_receiver:
        processor: AudioProcessor = ctx.processor
        audio_bytes = b"".join(processor.buffer)
        st.success("Recording stopped.")

        # Save locally (optional)
        with open("audio_input.raw", "wb") as f:
            f.write(audio_bytes)

        # 🔁 Send audio to backend (example POST)
        st.write("Sending audio to backend...")
        response = requests.post("http://localhost:8000/voice-query", data=audio_bytes)
        
        if response.ok:
            st.audio(response.content, format="audio/wav")
        else:
            st.error("Failed to get audio response from backend.")
