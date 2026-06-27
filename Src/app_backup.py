import json
import os
import subprocess
import sys
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Gesture AI Studios",
    page_icon="🖐️",
    layout="wide"
)

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
    "Frame Flash",
    "Floating Text",
    "Rainbow Text"
]

OPEN_HAND_MODES = [
    "Show Menu",
    "Normal Gesture Action"
]

THEMES = {
    "Gesture Blue": {
        "primary": "#0B3C5D",
        "accent": "#00A7C2",
        "background": "#EAF6FA"
    },
    "Dark Tech": {
        "primary": "#061826",
        "accent": "#00E5FF",
        "background": "#DFF8FF"
    },
    "Event Purple": {
        "primary": "#3D1766",
        "accent": "#B35CFF",
        "background": "#F3E8FF"
    }
}


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


def default_gesture_settings(gesture):
    return {
        "message": f"{gesture} detected!",
        "color": "#00A7C2",
        "size": 1.0,
        "animation": "None"
    }


def default_settings():
    return {
        "open_hand_mode": "Show Menu",
        "fullscreen": False,
        "show_fps": True,
        "show_landmarks": True,
        "theme": "Gesture Blue"
    }


def ensure_config_shape(config):
    if "settings" not in config or not isinstance(config.get("settings"), dict):
        config["settings"] = default_settings()

    for key, value in default_settings().items():
        if key not in config["settings"]:
            config["settings"][key] = value

    for gesture in GESTURES:
        if gesture not in config or not isinstance(config.get(gesture), dict):
            config[gesture] = default_gesture_settings(gesture)

        defaults = default_gesture_settings(gesture)
        for key, value in defaults.items():
            if key not in config[gesture]:
                config[gesture][key] = value

    return config


def reset_defaults():
    config = {"settings": default_settings()}
    for gesture in GESTURES:
        config[gesture] = default_gesture_settings(gesture)
    save_config(config)
    return config


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

    .status-box {
        background-color: #ffffff;
        padding: 16px;
        border-left: 5px solid #00A7C2;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

config = ensure_config_shape(load_config())

if "mirror_process" not in st.session_state:
    st.session_state.mirror_process = None

col_logo, col_title = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=170)
    else:
        st.warning("Logo not found. Add it as assets/gesture_logo.png")

with col_title:
    st.title("Gesture AI Studios")
    st.write("A no-code AI smart mirror platform for customizable gesture-based experiences.")

st.markdown(
    """
    <div class="app-card">
        <h3>Admin Dashboard</h3>
        <p class="small-text">
        Customize how gestures behave, choose visual effects, save your configuration,
        and launch the Smart Mirror experience.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Project Controls")

theme_name = st.sidebar.selectbox(
    "Theme",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(config["settings"].get("theme", "Gesture Blue"))
)
config["settings"]["theme"] = theme_name

open_hand_mode = st.sidebar.selectbox(
    "Open Hand Behavior",
    OPEN_HAND_MODES,
    index=OPEN_HAND_MODES.index(config["settings"].get("open_hand_mode", "Show Menu"))
)
config["settings"]["open_hand_mode"] = open_hand_mode

config["settings"]["fullscreen"] = st.sidebar.checkbox(
    "Launch Smart Mirror in Fullscreen",
    value=bool(config["settings"].get("fullscreen", False))
)

config["settings"]["show_fps"] = st.sidebar.checkbox(
    "Show FPS Counter",
    value=bool(config["settings"].get("show_fps", True))
)

config["settings"]["show_landmarks"] = st.sidebar.checkbox(
    "Show Hand Landmarks",
    value=bool(config["settings"].get("show_landmarks", True))
)

st.sidebar.divider()
st.sidebar.header("Gesture Customization")

for gesture in GESTURES:
    with st.sidebar.expander(gesture, expanded=False):
        config[gesture]["message"] = st.text_input(
            "Message",
            value=config[gesture].get("message", f"{gesture} detected!"),
            key=f"{gesture}_message"
        )

        config[gesture]["color"] = st.color_picker(
            "Text / Effect Color",
            value=config[gesture].get("color", "#00A7C2"),
            key=f"{gesture}_color"
        )

        config[gesture]["size"] = st.slider(
            "Text Size",
            min_value=0.5,
            max_value=2.5,
            value=float(config[gesture].get("size", 1.0)),
            step=0.1,
            key=f"{gesture}_size"
        )

        current_animation = config[gesture].get("animation", "None")
        if current_animation not in ANIMATIONS:
            current_animation = "None"

        config[gesture]["animation"] = st.selectbox(
            "Animation",
            ANIMATIONS,
            index=ANIMATIONS.index(current_animation),
            key=f"{gesture}_animation"
        )

st.sidebar.divider()

col_save, col_run, col_stop = st.columns(3)

with col_save:
    if st.button("💾 Save Settings"):
        save_config(config)
        st.success("Settings saved successfully.")

with col_run:
    if st.button("▶ Run Smart Mirror"):
        save_config(config)

        if st.session_state.mirror_process is None:
            st.session_state.mirror_process = subprocess.Popen(
                [sys.executable, "src/smart_mirror.py"]
            )
            st.success("Smart Mirror started.")
        else:
            st.info("Smart Mirror is already running.")

with col_stop:
    if st.button("⏹ Stop Smart Mirror"):
        if st.session_state.mirror_process is not None:
            st.session_state.mirror_process.terminate()
            st.session_state.mirror_process = None
            st.success("Smart Mirror stopped.")
        else:
            st.info("Smart Mirror is not running.")

col_reset, col_export = st.columns(2)

with col_reset:
    if st.button("Reset Defaults"):
        config = reset_defaults()
        st.success("Default settings restored. Refresh the page to view updates.")

with col_export:
    export_name = f"gesture_ai_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button(
        label="Export Configuration",
        data=json.dumps(config, indent=4),
        file_name=export_name,
        mime="application/json"
    )

st.subheader("Current Project Setup")

theme = THEMES[config["settings"]["theme"]]

st.markdown(
    f"""
    <div class="status-box">
        <b>Theme:</b> {config["settings"]["theme"]}<br>
        <b>Open Hand Behavior:</b> {config["settings"]["open_hand_mode"]}<br>
        <b>Fullscreen:</b> {config["settings"]["fullscreen"]}<br>
        <b>Show FPS:</b> {config["settings"]["show_fps"]}<br>
        <b>Show Landmarks:</b> {config["settings"]["show_landmarks"]}
    </div>
    """,
    unsafe_allow_html=True
)

for gesture in GESTURES:
    st.markdown(
        f"""
        <div class="app-card">
            <h4>{gesture}</h4>
            <p><b>Message:</b> {config[gesture]["message"]}</p>
            <p><b>Color:</b> {config[gesture]["color"]}</p>
            <p><b>Text Size:</b> {config[gesture]["size"]}</p>
            <p><b>Animation:</b> {config[gesture]["animation"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.info("Tip: In Smart Mirror mode, press Q to quit, S to save a screenshot, F for fullscreen, and ESC to exit fullscreen.")

PRESET_FOLDER = "saved_projects"

if not os.path.exists(PRESET_FOLDER):
    os.makedirs(PRESET_FOLDER)

st.divider()
st.subheader("💾 Saved Project Configurations")

project_name = st.text_input("Configuration name", "My Event Setup")

col1, col2 = st.columns(2)

with col1:
    if st.button("Save Configuration As"):
        safe_name = project_name.strip().replace(" ", "_")
        preset_path = os.path.join(PRESET_FOLDER, safe_name + ".json")

        save_config(config)

        with open(preset_path, "w") as file:
            json.dump(config, file, indent=4)

        st.success(f"Configuration saved as {safe_name}")

with col2:
    saved_files = [
        file for file in os.listdir(PRESET_FOLDER)
        if file.endswith(".json")
    ]

    if saved_files:
        selected_preset = st.selectbox("Load saved configuration", saved_files)

        if st.button("Load Configuration"):
            preset_path = os.path.join(PRESET_FOLDER, selected_preset)

            with open(preset_path, "r") as file:
                loaded_config = json.load(file)

            save_config(loaded_config)

            st.success("Configuration loaded. Refresh the page to view changes.")
            st.rerun()
    else:
        st.info("No saved configurations yet.")
st.divider()
st.subheader("📸 Smart Mirror Gallery")

SCREENSHOT_FOLDER = "screenshots"

if not os.path.exists(SCREENSHOT_FOLDER):
    os.makedirs(SCREENSHOT_FOLDER)

images = [
    img for img in os.listdir(SCREENSHOT_FOLDER)
    if img.lower().endswith((".png", ".jpg", ".jpeg"))
]

if images:

    images = sorted(images, reverse=True)

    selected_image = st.selectbox(
        "Choose a Screenshot",
        images
    )

    image_path = os.path.join(
        SCREENSHOT_FOLDER,
        selected_image
    )

    st.image(
        image_path,
        caption=selected_image,
        use_container_width=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        with open(image_path, "rb") as file:
            st.download_button(
                "⬇ Download",
                file,
                file_name=selected_image,
                mime="image/png"
            )

    with col2:
        if st.button("🗑 Delete Screenshot"):

            os.remove(image_path)

            st.success("Screenshot deleted successfully.")

            st.rerun()

    with col3:
        if st.button("🔄 Refresh Gallery"):
            st.rerun()

else:
    st.info("No screenshots available.")