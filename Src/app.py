import json
import os
import subprocess
import sys
import hashlib
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Gesture AI Studios",
    layout="wide"
)

CONFIG_FILE = "config.json"
USERS_FILE = "users.json"
LOGO_PATH = "assets/gesture_logo.png"
PRESET_FOLDER = "saved_projects"

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
    "Light": {
        "primary": "#0B3C5D",
        "accent": "#00A7C2",
        "background": "#EAF6FA"
    },
    "Dark": {
        "primary": "#061826",
        "accent": "#00E5FF",
        "background": "#0B1720"
    }
}

os.makedirs(PRESET_FOLDER, exist_ok=True)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f, indent=4)

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def sign_up(username, password):
    users = load_users()

    if username in users:
        return False, "Username already exists."

    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_users(users)
    return True, "Account created successfully. Please log in."


def login(username, password):
    users = load_users()

    if username not in users:
        return False

    return users[username]["password"] == hash_password(password)


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
        "theme": "Light"
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


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "mirror_process" not in st.session_state:
    st.session_state.mirror_process = None


if not st.session_state.logged_in:
    col_logo, col_title = st.columns([1, 4])

    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=170)

    with col_title:
        st.title("Gesture AI Studios")
        st.write("Sign in to customize and launch your AI-powered smart mirror experience.")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if login(login_username, login_password):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid username or password.Try again>")

    with tab2:
        st.subheader("Create Account")
        signup_username = st.text_input("Choose username", key="signup_username")
        signup_password = st.text_input("Choose password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")

        if st.button("Create Account"):
            if not signup_username or not signup_password:
                st.error("Please enter a username and password.")
            elif signup_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = sign_up(signup_username, signup_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.stop()


config = ensure_config_shape(load_config())

col_logo, col_title = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=170)
    else:
        st.warning("Logo not found. Add it as assets/gesture_logo.png")

with col_title:
    st.title("Gesture AI Studios")
    st.write(f"Welcome, **{st.session_state.username}** 👋")

if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

st.markdown(
    """
    <div class="app-card">
        <h3>Admin Dashboard</h3>
        <p>
        Customize gesture actions, save project configurations, and launch the Smart Mirror experience.<br>
        Developed by Areen Ahmed Nasser Albattashi
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Project Controls")

theme_name = st.sidebar.selectbox(
    "Theme",
    list(THEMES.keys()),
    index=list(THEMES.keys()).index(config["settings"].get("theme", "Light"))
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

st.divider()
st.subheader("💾 Saved Project Configurations")

project_name = st.text_input("Configuration Name", "My Event Setup")

col_project_save, col_project_load = st.columns(2)

with col_project_save:
    if st.button("Save Configuration As"):
        safe_name = project_name.strip().replace(" ", "_")

        if not safe_name:
            st.error("Please enter a valid configuration name.")
        else:
            preset_path = os.path.join(PRESET_FOLDER, safe_name + ".json")
            save_config(config)

            with open(preset_path, "w") as file:
                json.dump(config, file, indent=4)

            st.success(f"Configuration saved as {safe_name}")

with col_project_load:
    saved_files = [
        file for file in os.listdir(PRESET_FOLDER)
        if file.endswith(".json")
    ]

    if saved_files:
        selected_preset = st.selectbox("Load Saved Configuration", saved_files)

        if st.button("Load Configuration"):
            preset_path = os.path.join(PRESET_FOLDER, selected_preset)

            with open(preset_path, "r") as file:
                loaded_config = json.load(file)

            save_config(loaded_config)
            st.success("Configuration loaded.")
            st.rerun()
    else:
        st.info("No saved configurations yet.")

st.divider()
st.subheader("📸 Smart Mirror Gallery")

SCREENSHOT_FOLDER = "screenshots"

if not os.path.exists(SCREENSHOT_FOLDER):
    os.makedirs(SCREENSHOT_FOLDER)

images = sorted(
    [
        img for img in os.listdir(SCREENSHOT_FOLDER)
        if img.lower().endswith((".png", ".jpg", ".jpeg"))
    ],
    reverse=True
)

if images:
    selected_image = st.selectbox("Choose Screenshot", images)
    image_path = os.path.join(SCREENSHOT_FOLDER, selected_image)

    st.image(image_path, use_container_width=True)

    col_download, col_delete, col_refresh = st.columns(3)

    with col_download:
        with open(image_path, "rb") as file:
            st.download_button(
                "⬇ Download",
                file,
                file_name=selected_image,
                mime="image/png"
            )

    with col_delete:
        if st.button("🗑 Delete Screenshot"):
            os.remove(image_path)
            st.success("Screenshot deleted.")
            st.rerun()

    with col_refresh:
        if st.button("🔄 Refresh Gallery"):
            st.rerun()
else:
    st.info("No screenshots found. Open Smart Mirror and press S to save one.")

st.divider()
st.subheader("Current Project Setup")

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