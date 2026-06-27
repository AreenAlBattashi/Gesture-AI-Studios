import json
import math
import os
import hashlib
import threading
import time
from datetime import datetime

import av
import cv2
import mediapipe as mp
import streamlit as st
from streamlit_webrtc import WebRtcMode, VideoProcessorBase, webrtc_streamer

st.set_page_config(
    page_title="Gesture AI Studios",
    layout="wide"
)

CONFIG_FILE = "config.json"
USERS_FILE = "users.json"
LOGO_PATH = "assets/gesture_logo.png"
MODEL_FILE = "hand_landmarker.task"
PRESET_FOLDER = "saved_projects"
SCREENSHOT_FOLDER = "screenshots"

GESTURES = [
    "Closed Fist",
    "One Finger",
    "Peace Sign",
    "Three Fingers",
    "Open Hand",
    "Index and Pinky",
    "Rock Sign"
]

GESTURES_MENU_OPTIONS = [
    "One Finger",
    "Peace Sign",
    "Three Fingers",
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

MIRROR_THEMES = {
    "Light": {
        "accent": (194, 167, 0),
        "white": (255, 255, 255)
    },
    "Dark": {
        "accent": (255, 229, 0),
        "white": (255, 255, 255)
    }
}

os.makedirs(PRESET_FOLDER, exist_ok=True)


def get_user_folder():

    username = st.session_state.username

    folder = os.path.join("users", username)

    screenshots = os.path.join(folder, "screenshots")
    projects = os.path.join(folder, "projects")
    config = os.path.join(folder, "config.json")

    os.makedirs(folder, exist_ok=True)
    os.makedirs(screenshots, exist_ok=True)
    os.makedirs(projects, exist_ok=True)

    return folder, screenshots, projects, config
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


def hex_to_bgr(hex_color):
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (b, g, r)
    except Exception:
        return (194, 167, 0)


def draw_animation(frame, animation, color, tick):
    height, width, _ = frame.shape

    if animation == "Glow Box":
        cv2.rectangle(frame, (20, 20), (width - 20, height - 20), color, 6)
    elif animation == "Confetti":
        for i in range(35):
            x = (i * 67 + tick * 8) % width
            y = (i * 41 + tick * 6) % height
            cv2.circle(frame, (x, y), 4, color, -1)
    elif animation == "Moving Circle":
        x = int((math.sin(tick / 10) + 1) * width / 2)
        cv2.circle(frame, (x, 120), 28, color, -1)
    elif animation == "Frame Flash":
        thickness = 8 if tick % 20 < 10 else 3
        cv2.rectangle(frame, (10, 10), (width - 10, height - 10), color, thickness)
    elif animation == "Floating Text":
        y = int(80 + 20 * math.sin(tick / 8))
        cv2.circle(frame, (width - 90, y), 22, color, -1)

    return frame


def get_rainbow_color(tick):
    r = int((math.sin(tick / 10) + 1) * 127)
    g = int((math.sin(tick / 12 + 2) + 1) * 127)
    b = int((math.sin(tick / 14 + 4) + 1) * 127)
    return (b, g, r)


def finger_states(landmarks):
    return {
        "index": landmarks[8].y < landmarks[6].y,
        "middle": landmarks[12].y < landmarks[10].y,
        "ring": landmarks[16].y < landmarks[14].y,
        "pinky": landmarks[20].y < landmarks[18].y
    }


def detect_gesture(landmarks):
    states = finger_states(landmarks)
    index = states["index"]
    middle = states["middle"]
    ring = states["ring"]
    pinky = states["pinky"]
    fingers = sum([index, middle, ring, pinky])

    if fingers == 0:
        return "Closed Fist"
    if index and not middle and not ring and not pinky:
        return "One Finger"
    if index and middle and not ring and not pinky:
        return "Peace Sign"
    if index and middle and ring and not pinky:
        return "Three Fingers"
    if index and not middle and not ring and pinky:
        return "Index and Pinky"
    if index and not middle and ring and pinky:
        return "Rock Sign"
    if index and middle and ring and pinky:
        return "Open Hand"

    return "Hand Detected"


def draw_menu(frame, theme_colors):
    accent = theme_colors["accent"]
    white = theme_colors["white"]

    cv2.rectangle(frame, (35, 70), (650, 355), (0, 0, 0), -1)
    cv2.rectangle(frame, (35, 70), (650, 355), accent, 3)
    cv2.putText(frame, "Gesture Menu", (65, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 1, accent, 2)

    lines = [
        "One Finger       : Option 1",
        "Peace Sign       : Option 2",
        "Three Fingers    : Option 3",
        "Index + Pinky    : Option 4",
        "Rock Sign        : Option 5",
        "Closed Fist      : Close Menu"
    ]

    y = 160
    for line in lines:
        cv2.putText(frame, line, (65, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, white, 2)
        y += 35


def put_wrapped_text(frame, text, position, font_scale, color, thickness=2, max_width=760):
    x, y = position
    words = text.split()
    line = ""

    for word in words:
        test_line = line + word + " "
        size = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]

        if size[0] > max_width:
            cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            y += int(35 * font_scale) + 15
            line = word + " "
        else:
            line = test_line

    if line:
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


class SmartMirrorProcessor(VideoProcessorBase):
    def __init__(self):
        self.detector = None
        self.detector_error = None

        try:
            base_options = mp.tasks.BaseOptions(model_asset_path=MODEL_FILE)
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                num_hands=1
            )
            self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        except Exception as error:
            self.detector_error = str(error)

        self.menu_open = False
        self.current_message = "Open your hand to show the menu"
        self.current_color = (194, 167, 0)
        self.current_size = 0.8
        self.current_animation = "None"
        self.gesture_history = []
        self.history_size = 8
        self.required_matches = 6
        self.last_action_time = 0
        self.cooldown = 1.3
        self.tick = 0
        self.last_time = time.time()
        self.fps = 0
        self.latest_frame = None
        self.lock = threading.Lock()

    def recv(self, frame):
        self.tick += 1
        img = cv2.flip(frame.to_ndarray(format="bgr24"), 1)
        app_settings = ensure_config_shape(load_config()).get("settings", default_settings())
        theme_colors = MIRROR_THEMES.get(app_settings.get("theme", "Light"), MIRROR_THEMES["Light"])

        if self.detector is None:
            cv2.putText(img, "MediaPipe could not start on this server.", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, theme_colors["white"], 2)
            cv2.putText(img, "Use Python 3.11 in Streamlit Cloud settings.", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_colors["white"], 2)
            with self.lock:
                self.latest_frame = img.copy()
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        now_time = time.time()
        self.fps = 1 / max(now_time - self.last_time, 0.001)
        self.last_time = now_time

        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.detector.detect(mp_image)
        raw_gesture = "None"

        if result.hand_landmarks:
            height, width, _ = img.shape
            for hand_landmarks in result.hand_landmarks:
                raw_gesture = detect_gesture(hand_landmarks)

                if app_settings.get("show_landmarks", True):
                    for landmark in hand_landmarks:
                        x = int(landmark.x * width)
                        y = int(landmark.y * height)
                        cv2.circle(img, (x, y), 4, theme_colors["accent"], -1)

        self.gesture_history.append(raw_gesture)
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)

        stable_gesture = max(set(self.gesture_history), key=self.gesture_history.count)
        if self.gesture_history.count(stable_gesture) >= self.required_matches:
            detected_gesture = stable_gesture
        else:
            detected_gesture = "Stabilizing..."

        now = time.time()
        if now - self.last_action_time > self.cooldown:
            if detected_gesture == "Open Hand" and not self.menu_open:
                if app_settings.get("open_hand_mode", "Show Menu") == "Show Menu":
                    self.menu_open = True
                    self.current_message = "Menu opened - choose an option"
                    self.current_color = theme_colors["accent"]
                    self.current_size = 0.8
                    self.current_animation = "Glow Box"
                else:
                    settings = ensure_config_shape(load_config()).get("Open Hand", default_gesture_settings("Open Hand"))
                    self.current_message = settings.get("message", "Open Hand detected")
                    self.current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
                    self.current_size = float(settings.get("size", 1.0))
                    self.current_animation = settings.get("animation", "None")
                self.last_action_time = now

            elif self.menu_open and detected_gesture in GESTURES_MENU_OPTIONS:
                settings = ensure_config_shape(load_config()).get(detected_gesture, default_gesture_settings(detected_gesture))
                self.current_message = settings.get("message", detected_gesture)
                self.current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
                self.current_size = float(settings.get("size", 1.0))
                self.current_animation = settings.get("animation", "None")
                self.menu_open = False
                self.last_action_time = now

            elif self.menu_open and detected_gesture == "Closed Fist":
                self.current_message = "Menu closed"
                self.current_color = theme_colors["white"]
                self.current_size = 0.8
                self.current_animation = "None"
                self.menu_open = False
                self.last_action_time = now

            elif not self.menu_open and detected_gesture in GESTURES:
                settings = ensure_config_shape(load_config()).get(detected_gesture, default_gesture_settings(detected_gesture))
                self.current_message = settings.get("message", detected_gesture)
                self.current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
                self.current_size = float(settings.get("size", 1.0))
                self.current_animation = settings.get("animation", "None")
                self.last_action_time = now

        display_color = self.current_color
        display_size = self.current_size

        if self.current_animation == "Pulse Text":
            display_size = self.current_size + 0.25 * abs(math.sin(self.tick / 8))
        if self.current_animation == "Rainbow Text":
            display_color = get_rainbow_color(self.tick)

        img = draw_animation(img, self.current_animation, display_color, self.tick)
        if self.menu_open:
            draw_menu(img, theme_colors)

        height, width, _ = img.shape
        put_wrapped_text(
            img,
            self.current_message,
            (30, max(60, height - 60)),
            display_size,
            display_color,
            thickness=2,
            max_width=max(260, width - 70)
        )
        cv2.putText(img, f"Detected: {detected_gesture}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_colors["white"], 2)

        if app_settings.get("show_fps", True):
            cv2.putText(img, f"FPS: {int(self.fps)}", (max(30, width - 135), 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_colors["white"], 2)

        with self.lock:
            self.latest_frame = img.copy()

        return av.VideoFrame.from_ndarray(img, format="bgr24")


def render_smart_mirror():
    st.title("Gesture AI Studios - Smart Mirror")
    st.write("Press START, allow camera access, and use your browser camera on this device.")

    if st.button("Back to Dashboard"):
        st.session_state.view = "dashboard"
        st.rerun()

    if not os.path.exists(MODEL_FILE):
        st.error("Missing hand_landmarker.task. Add it to the project root before deploying.")
        return

    ctx = webrtc_streamer(
        key="gesture-ai-smart-mirror",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=SmartMirrorProcessor,
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

    st.divider()
    if st.button("Take Screenshot"):
        if ctx.video_processor:
            with ctx.video_processor.lock:
                frame = ctx.video_processor.latest_frame

            if frame is None:
                st.warning("Start the camera first, then take a screenshot.")
            else:
                os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
                filename = f"smart_mirror_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                path = os.path.join(SCREENSHOT_FOLDER, filename)
                cv2.imwrite(path, frame)

                with open(path, "rb") as file:
                    st.download_button(
                        "Download Screenshot",
                        file,
                        file_name=filename,
                        mime="image/png"
                    )
        else:
            st.warning("Press START first.")


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

if "view" not in st.session_state:
    st.session_state.view = "dashboard"


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

if st.session_state.view == "mirror":
    render_smart_mirror()
    st.stop()

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
        st.session_state.view = "mirror"
        st.rerun()

with col_stop:
    if st.button("⏹ Stop Smart Mirror"):
        st.info("Use the STOP button inside the Smart Mirror camera panel.")

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
