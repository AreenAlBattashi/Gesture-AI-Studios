import streamlit as st
import json
import subprocess
import sys
import os

st.set_page_config(page_title="Gesture AI Studios", layout="wide")

CONFIG_FILE = "config.json"
LOGO_PATH = "assets/gesture_logo.png"

GESTURES = [
    "Closed Fist",
    "One Finger",
    "Peace Sign",
    "Three Fingers",
    "Open Hand",
    "Index and Pinky",
    "Rock Sign"
]

ANIMATIONS = [
    "None",
    "Glow Box",
    "Confetti",
    "Moving Circle",
    "Pulse Text",
    "Frame Flash"
]

OPEN_HAND_MODES = [
    "Show Menu",
    "Normal Gesture Action"
]

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fcfd 0%, #e9f6fa 100%);
        color: #082f49;
    }

    section[data-testid="stSidebar"] {
        background-color: #e3f2f7;
    }

    h1, h2, h3 {
        color: #082f49;
    }

    .stButton > button {
        background-color: #0b3c5d;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #5bb9cc;
        color: white;
    }

    .app-card {
        background-color: white;
        padding: 22px;
        border-radius: 18px;
        box-shadow: 0px 4px 16px rgba(8, 47, 73, 0.12);
        margin-bottom: 18px;
    }

    .small-text {
        color: #335c67;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def default_settings(gesture):
    return {
        "message": f"{gesture} detected!",
        "color": "#00A7C2",
        "size": 1.0,
        "animation": "None"
    }

config = load_config()

if "mirror_process" not in st.session_state:
    st.session_state.mirror_process = None

col1, col2 = st.columns([1, 4])

with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
    else:
        st.warning("Logo not found. Add it to assets/gesture_logo.png")

with col2:
    st.title("Gesture AI Studios")
    st.write(
        "Customize gestures, actions, colors, animations, and smart mirror behavior."
    )

st.markdown(
    """
    <div class="app-card">
        <h3>Project Dashboard</h3>
        <p class="small-text">
        Gesture AI Studios lets administrators create interactive smart mirror experiences.
        Configure each gesture, save your settings, then run the live camera experience.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Administrator Panel")

settings = config.get("settings", {})
current_mode = settings.get("open_hand_mode", "Show Menu")

if current_mode not in OPEN_HAND_MODES:
    current_mode = "Show Menu"

open_hand_mode = st.sidebar.selectbox(
    "Open Hand Behavior",
    OPEN_HAND_MODES,
    index=OPEN_HAND_MODES.index(current_mode)
)

config["settings"] = {
    "open_hand_mode": open_hand_mode
}

for gesture in GESTURES:
    if gesture not in config or not isinstance(config.get(gesture), dict):
        config[gesture] = default_settings(gesture)

    st.sidebar.subheader(gesture)

    config[gesture]["message"] = st.sidebar.text_input(
        f"{gesture} message",
        config[gesture].get("message", f"{gesture} detected!"),
        key=f"{gesture}_message"
    )

    config[gesture]["color"] = st.sidebar.color_picker(
        f"{gesture} color",
        config[gesture].get("color", "#00A7C2"),
        key=f"{gesture}_color"
    )

    config[gesture]["size"] = st.sidebar.slider(
        f"{gesture} text size",
        0.5,
        2.0,
        float(config[gesture].get("size", 1.0)),
        key=f"{gesture}_size"
    )

    animation = config[gesture].get("animation", "None")
    if animation not in ANIMATIONS:
        animation = "None"

    config[gesture]["animation"] = st.sidebar.selectbox(
        f"{gesture} animation",
        ANIMATIONS,
        index=ANIMATIONS.index(animation),
        key=f"{gesture}_animation"
    )

col_a, col_b = st.columns(2)

with col_a:
    if st.button("Save All Settings"):
        save_config(config)
        st.success("Settings saved successfully!")

with col_b:
    if st.button("Run Smart Mirror"):
        save_config(config)

        if st.session_state.mirror_process is None:
            st.session_state.mirror_process = subprocess.Popen(
                [sys.executable, "src/smart_mirror.py"]
            )
            st.success("Smart Mirror started!")
        else:
            st.info("Smart Mirror is already running.")

if st.button("Stop Smart Mirror"):
    if st.session_state.mirror_process:
        st.session_state.mirror_process.terminate()
        st.session_state.mirror_process = None
        st.success("Smart Mirror stopped!")
    else:
        st.info("Smart Mirror is not currently running.")

st.subheader("Current Setup")

st.markdown(
    f"""
    <div class="app-card">
        <b>Open Hand Behavior:</b> {config['settings']['open_hand_mode']}
    </div>
    """,
    unsafe_allow_html=True
)

for gesture in GESTURES:
    st.markdown(
        f"""
        <div class="app-card">
            <h4>{gesture}</h4>
            <p><b>Message:</b> {config[gesture]['message']}</p>
            <p><b>Color:</b> {config[gesture]['color']}</p>
            <p><b>Text Size:</b> {config[gesture]['size']}</p>
            <p><b>Animation:</b> {config[gesture]['animation']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )