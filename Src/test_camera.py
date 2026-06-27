import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.title("Camera Test")

webrtc_streamer(
    key="camera-test",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={
        "video": True,
        "audio": False,
    },
    async_processing=True,
)
