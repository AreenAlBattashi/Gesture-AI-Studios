import json
import os
import hashlib
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Gesture AI Studios",
    layout="wide"
)

CONFIG_FILE = "config.json"
USERS_FILE = "users.json"
LOGO_PATH = "assets/gesture_logo.png"
MODEL_FILE = "hand_landmarker.task"

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


def safe_filename(name):
    safe = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in name.strip())
    return safe.strip("_")


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


def render_smart_mirror():
    st.title("Gesture AI Studios - Smart Mirror")
    st.write("Press Start Camera, allow camera access, and use this device's browser camera.")

    if st.button("Back to Dashboard"):
        st.session_state.view = "dashboard"
        st.rerun()

    mirror_config = ensure_config_shape(load_config())
    component_config = json.dumps(mirror_config).replace("</", "<\\/")
    screenshot_store_key = json.dumps(f"gesture_ai_screenshots_{st.session_state.username}")

    components.html(
        f"""
        <div class="mirror-shell" tabindex="0">
            <div class="mirror-toolbar">
                <button id="startBtn">Start Camera</button>
                <span id="status">Camera is off. Press S in the mirror to save a screenshot.</span>
            </div>
            <div class="mirror-stage">
                <video id="video" playsinline muted></video>
                <canvas id="canvas"></canvas>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
        <script>
        const config = {component_config};
        const gestures = ["Closed Fist", "One Finger", "Peace Sign", "Three Fingers", "Open Hand", "Index and Pinky", "Rock Sign"];
        const menuGestures = ["One Finger", "Peace Sign", "Three Fingers", "Index and Pinky", "Rock Sign"];
        const video = document.getElementById("video");
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");
        const statusEl = document.getElementById("status");
        const startBtn = document.getElementById("startBtn");
        const stage = document.querySelector(".mirror-stage");
        const shell = document.querySelector(".mirror-shell");
        const screenshotStoreKey = {screenshot_store_key};

        let camera = null;
        let menuOpen = false;
        let currentMessage = "Open your hand to show the menu";
        let currentColor = "#00A7C2";
        let currentSize = 1;
        let currentAnimation = "None";
        let history = [];
        let lastActionAt = 0;
        let tick = 0;
        let lastFrameAt = performance.now();
        let fps = 0;
        const wantsFullscreen = Boolean((config.settings || {{}}).fullscreen);

        function loadScreenshots() {{
            try {{
                return JSON.parse(localStorage.getItem(screenshotStoreKey) || "[]");
            }} catch {{
                return [];
            }}
        }}

        function saveScreenshot() {{
            if (!canvas.width || !canvas.height) {{
                statusEl.textContent = "Start the camera before saving a screenshot.";
                return;
            }}
            const shots = loadScreenshots();
            const now = new Date();
            const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\\..+/, "");
            shots.unshift({{
                name: `smart_mirror_${{stamp}}.png`,
                createdAt: now.toLocaleString(),
                dataUrl: canvas.toDataURL("image/png")
            }});
            localStorage.setItem(screenshotStoreKey, JSON.stringify(shots.slice(0, 25)));
            statusEl.textContent = "Screenshot saved. Return to the dashboard gallery to download or delete it.";
        }}

        function setting(name) {{
            return config[name] || {{message: `${{name}} detected!`, color: "#00A7C2", size: 1, animation: "None"}};
        }}

        function fingerStates(points) {{
            return {{
                index: points[8].y < points[6].y,
                middle: points[12].y < points[10].y,
                ring: points[16].y < points[14].y,
                pinky: points[20].y < points[18].y
            }};
        }}

        function detectGesture(points) {{
            const s = fingerStates(points);
            const count = [s.index, s.middle, s.ring, s.pinky].filter(Boolean).length;
            if (count === 0) return "Closed Fist";
            if (s.index && !s.middle && !s.ring && !s.pinky) return "One Finger";
            if (s.index && s.middle && !s.ring && !s.pinky) return "Peace Sign";
            if (s.index && s.middle && s.ring && !s.pinky) return "Three Fingers";
            if (s.index && !s.middle && !s.ring && s.pinky) return "Index and Pinky";
            if (s.index && !s.middle && s.ring && s.pinky) return "Rock Sign";
            if (s.index && s.middle && s.ring && s.pinky) return "Open Hand";
            return "Hand Detected";
        }}

        function stableGesture(raw) {{
            history.push(raw);
            if (history.length > 8) history.shift();
            const counts = history.reduce((acc, item) => {{ acc[item] = (acc[item] || 0) + 1; return acc; }}, {{}});
            const best = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0] || "None";
            return counts[best] >= 6 ? best : "Stabilizing...";
        }}

        function applyGesture(gesture) {{
            const now = performance.now();
            if (now - lastActionAt < 1300) return;

            if (gesture === "Open Hand" && !menuOpen) {{
                if ((config.settings || {{}}).open_hand_mode === "Show Menu") {{
                    menuOpen = true;
                    currentMessage = "Menu opened - choose an option";
                    currentColor = "#00A7C2";
                    currentSize = 1;
                    currentAnimation = "Glow Box";
                }} else {{
                    const s = setting("Open Hand");
                    currentMessage = s.message;
                    currentColor = s.color;
                    currentSize = Number(s.size || 1);
                    currentAnimation = s.animation || "None";
                }}
                lastActionAt = now;
            }} else if (menuOpen && menuGestures.includes(gesture)) {{
                const s = setting(gesture);
                currentMessage = s.message;
                currentColor = s.color;
                currentSize = Number(s.size || 1);
                currentAnimation = s.animation || "None";
                menuOpen = false;
                lastActionAt = now;
            }} else if (menuOpen && gesture === "Closed Fist") {{
                currentMessage = "Menu closed";
                currentColor = "#ffffff";
                currentSize = 1;
                currentAnimation = "None";
                menuOpen = false;
                lastActionAt = now;
            }} else if (!menuOpen && gestures.includes(gesture)) {{
                const s = setting(gesture);
                currentMessage = s.message;
                currentColor = s.color;
                currentSize = Number(s.size || 1);
                currentAnimation = s.animation || "None";
                lastActionAt = now;
            }}
        }}

        function drawAnimation(color) {{
            if (currentAnimation === "Glow Box") {{
                ctx.strokeStyle = color;
                ctx.lineWidth = 8;
                ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40);
            }} else if (currentAnimation === "Confetti") {{
                ctx.fillStyle = color;
                for (let i = 0; i < 35; i++) {{
                    const x = (i * 67 + tick * 8) % canvas.width;
                    const y = (i * 41 + tick * 6) % canvas.height;
                    ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
                }}
            }} else if (currentAnimation === "Moving Circle") {{
                const x = (Math.sin(tick / 10) + 1) * canvas.width / 2;
                ctx.fillStyle = color;
                ctx.beginPath(); ctx.arc(x, 120, 30, 0, Math.PI * 2); ctx.fill();
            }} else if (currentAnimation === "Frame Flash") {{
                ctx.strokeStyle = color;
                ctx.lineWidth = tick % 20 < 10 ? 10 : 4;
                ctx.strokeRect(12, 12, canvas.width - 24, canvas.height - 24);
            }} else if (currentAnimation === "Floating Text") {{
                const y = 90 + 24 * Math.sin(tick / 8);
                ctx.fillStyle = color;
                ctx.beginPath(); ctx.arc(canvas.width - 90, y, 24, 0, Math.PI * 2); ctx.fill();
            }}
        }}

        function drawText(text, color, size) {{
            const fontSize = Math.max(22, Math.min(56, 30 * size));
            ctx.font = `700 ${{fontSize}}px Arial`;
            ctx.fillStyle = color;
            ctx.lineWidth = 4;
            ctx.strokeStyle = "rgba(0,0,0,.55)";
            const words = text.split(" ");
            let line = "";
            let y = canvas.height - 60;
            const maxWidth = canvas.width - 60;
            const lines = [];
            words.forEach(word => {{
                const test = line + word + " ";
                if (ctx.measureText(test).width > maxWidth && line) {{
                    lines.push(line.trim());
                    line = word + " ";
                }} else {{
                    line = test;
                }}
            }});
            if (line) lines.push(line.trim());
            y -= (lines.length - 1) * (fontSize + 8);
            lines.forEach(row => {{
                ctx.strokeText(row, 30, y);
                ctx.fillText(row, 30, y);
                y += fontSize + 8;
            }});
        }}

        function drawMenu() {{
            ctx.fillStyle = "rgba(0,0,0,.72)";
            ctx.fillRect(35, 70, 620, 285);
            ctx.strokeStyle = "#00A7C2";
            ctx.lineWidth = 3;
            ctx.strokeRect(35, 70, 620, 285);
            ctx.fillStyle = "#00E5FF";
            ctx.font = "700 34px Arial";
            ctx.fillText("Gesture Menu", 65, 115);
            ctx.fillStyle = "white";
            ctx.font = "22px Arial";
            ["One Finger       : Option 1", "Peace Sign       : Option 2", "Three Fingers    : Option 3", "Index + Pinky    : Option 4", "Rock Sign        : Option 5", "Closed Fist      : Close Menu"].forEach((line, i) => ctx.fillText(line, 65, 160 + i * 35));
        }}

        async function enterFullscreen() {{
            if (!document.fullscreenElement) {{
                if (stage.requestFullscreen) {{
                    await stage.requestFullscreen();
                }} else if (stage.webkitRequestFullscreen) {{
                    stage.webkitRequestFullscreen();
                }} else {{
                    throw new Error("Fullscreen is not supported by this browser");
                }}
            }}
        }}

        function onResults(results) {{
            tick += 1;
            const now = performance.now();
            fps = 1000 / Math.max(now - lastFrameAt, 1);
            lastFrameAt = now;
            canvas.width = video.videoWidth || 854;
            canvas.height = video.videoHeight || 480;
            ctx.save();
            ctx.scale(-1, 1);
            ctx.drawImage(results.image, -canvas.width, 0, canvas.width, canvas.height);
            ctx.restore();

            let raw = "None";
            if (results.multiHandLandmarks && results.multiHandLandmarks.length) {{
                raw = detectGesture(results.multiHandLandmarks[0]);
                if ((config.settings || {{}}).show_landmarks !== false) {{
                    drawConnectors(ctx, results.multiHandLandmarks[0], HAND_CONNECTIONS, {{color: "#00E5FF", lineWidth: 3}});
                    drawLandmarks(ctx, results.multiHandLandmarks[0], {{color: "#ffffff", lineWidth: 1, radius: 3}});
                }}
            }}
            const detected = stableGesture(raw);
            applyGesture(detected);

            let color = currentColor;
            let size = currentSize;
            if (currentAnimation === "Pulse Text") size += 0.25 * Math.abs(Math.sin(tick / 8));
            if (currentAnimation === "Rainbow Text") color = `rgb(${{Math.round((Math.sin(tick / 10) + 1) * 127)}}, ${{Math.round((Math.sin(tick / 12 + 2) + 1) * 127)}}, ${{Math.round((Math.sin(tick / 14 + 4) + 1) * 127)}})`;

            drawAnimation(color);
            if (menuOpen) drawMenu();
            drawText(currentMessage, color, size);
            ctx.fillStyle = "white";
            ctx.font = "20px Arial";
            ctx.fillText(`Detected: ${{detected}}`, 30, 38);
            if ((config.settings || {{}}).show_fps !== false) ctx.fillText(`FPS: ${{Math.round(fps)}}`, canvas.width - 105, 38);
        }}

        startBtn.onclick = async () => {{
            statusEl.textContent = "Loading camera...";
            try {{
                if (wantsFullscreen) {{
                    try {{
                        await enterFullscreen();
                    }} catch (fullscreenError) {{
                        statusEl.textContent = `Fullscreen blocked: ${{fullscreenError.message}}`;
                    }}
                }}
                const hands = new Hands({{locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${{file}}`}});
                hands.setOptions({{maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6}});
                hands.onResults(onResults);
                camera = new Camera(video, {{onFrame: async () => await hands.send({{image: video}}), width: 854, height: 480}});
                await camera.start();
                shell.focus();
                statusEl.textContent = "Camera running. Press S to save a screenshot.";
            }} catch (error) {{
                statusEl.textContent = `Camera error: ${{error.message}}`;
            }}
        }};

        shell.addEventListener("keydown", event => {{
            if (event.key.toLowerCase() === "s") {{
                event.preventDefault();
                saveScreenshot();
            }}
        }});

        document.addEventListener("keydown", event => {{
            if (event.key.toLowerCase() === "s") {{
                event.preventDefault();
                saveScreenshot();
            }}
        }});
        </script>

        <style>
        .mirror-shell {{ font-family: Arial, sans-serif; color: #082f49; }}
        .mirror-toolbar {{ display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
        .mirror-toolbar button {{ background: #0b3c5d; color: white; border: 0; border-radius: 8px; padding: 10px 14px; font-weight: 700; cursor: pointer; }}
        .mirror-toolbar span {{ color: #0b3c5d; font-weight: 700; }}
        .mirror-stage {{ width: 100%; max-width: 980px; background: #061826; border-radius: 8px; overflow: hidden; position: relative; }}
        video {{ display: none; }}
        canvas {{ display: block; width: 100%; aspect-ratio: 16 / 9; background: #061826; }}
        .mirror-stage:fullscreen {{ width: 100vw; height: 100vh; max-width: none; border-radius: 0; }}
        .mirror-stage:fullscreen canvas {{ width: 100vw; height: 100vh; aspect-ratio: auto; object-fit: contain; }}
        .mirror-stage:-webkit-full-screen {{ width: 100vw; height: 100vh; max-width: none; border-radius: 0; }}
        .mirror-stage:-webkit-full-screen canvas {{ width: 100vw; height: 100vh; aspect-ratio: auto; object-fit: contain; }}
        </style>
        """,
        height=720,
    )
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
_, _, user_projects_folder, _ = get_user_folder()

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
    st.write(f"Welcome, **{st.session_state.username}**")

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
    if st.button("Save Settings"):
        save_config(config)
        st.success("Settings saved successfully.")

with col_run:
    if st.button("Run Smart Mirror"):
        save_config(config)
        st.session_state.view = "mirror"
        st.rerun()

with col_stop:
    if st.button("Stop Smart Mirror"):
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
st.subheader("Saved Project Configurations")

project_name = st.text_input("Configuration Name", "My Event Setup")

col_project_save, col_project_load = st.columns(2)

with col_project_save:
    if st.button("Save Configuration As"):
        safe_name = safe_filename(project_name)

        if not safe_name:
            st.error("Please enter a valid configuration name.")
        else:
            preset_path = os.path.join(user_projects_folder, safe_name + ".json")
            save_config(config)

            with open(preset_path, "w") as file:
                json.dump(config, file, indent=4)

            st.success(f"Configuration saved as {safe_name}")

with col_project_load:
    saved_files = [
        file for file in os.listdir(user_projects_folder)
        if file.endswith(".json")
    ]

    if saved_files:
        selected_preset = st.selectbox("Load Saved Configuration", saved_files)

        if st.button("Load Configuration"):
            preset_path = os.path.join(user_projects_folder, selected_preset)

            with open(preset_path, "r") as file:
                loaded_config = json.load(file)

            save_config(loaded_config)
            st.success("Configuration loaded.")
            st.rerun()
    else:
        st.info("No saved configurations yet.")

st.divider()
st.subheader("Smart Mirror Gallery")

gallery_store_key = json.dumps(f"gesture_ai_screenshots_{st.session_state.username}")

components.html(
    f"""
    <div class="gallery-shell">
        <div class="gallery-actions">
            <button id="refreshGallery">Refresh</button>
            <button id="deleteAllGallery">Delete All</button>
            <span id="galleryStatus"></span>
        </div>
        <div id="galleryGrid" class="gallery-grid"></div>
    </div>

    <script>
    const galleryStoreKey = {gallery_store_key};
    const galleryGrid = document.getElementById("galleryGrid");
    const galleryStatus = document.getElementById("galleryStatus");

    function loadShots() {{
        try {{
            return JSON.parse(localStorage.getItem(galleryStoreKey) || "[]");
        }} catch {{
            return [];
        }}
    }}

    function saveShots(shots) {{
        localStorage.setItem(galleryStoreKey, JSON.stringify(shots));
    }}

    function downloadShot(shot) {{
        const link = document.createElement("a");
        link.download = shot.name || "smart_mirror.png";
        link.href = shot.dataUrl;
        link.click();
    }}

    function renderGallery() {{
        const shots = loadShots();
        galleryGrid.innerHTML = "";
        galleryStatus.textContent = shots.length ? `${{shots.length}} screenshot(s) in your account on this browser.` : "No screenshots found in your account yet.";

        shots.forEach((shot, index) => {{
            const card = document.createElement("div");
            card.className = "shot-card";

            const img = document.createElement("img");
            img.src = shot.dataUrl;
            img.alt = shot.name || "Smart Mirror screenshot";

            const meta = document.createElement("div");
            meta.className = "shot-meta";
            meta.textContent = `${{shot.name || "Screenshot"}} · ${{shot.createdAt || ""}}`;

            const row = document.createElement("div");
            row.className = "shot-actions";

            const download = document.createElement("button");
            download.textContent = "Download";
            download.onclick = () => downloadShot(shot);

            const remove = document.createElement("button");
            remove.textContent = "Delete";
            remove.onclick = () => {{
                const updated = loadShots();
                updated.splice(index, 1);
                saveShots(updated);
                renderGallery();
            }};

            row.append(download, remove);
            card.append(img, meta, row);
            galleryGrid.appendChild(card);
        }});
    }}

    document.getElementById("refreshGallery").onclick = renderGallery;
    document.getElementById("deleteAllGallery").onclick = () => {{
        if (confirm("Delete all screenshots for this account on this browser?")) {{
            saveShots([]);
            renderGallery();
        }}
    }};

    renderGallery();
    </script>

    <style>
    .gallery-shell {{ font-family: Arial, sans-serif; color: #082f49; }}
    .gallery-actions {{ display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
    .gallery-actions button, .shot-actions button {{ background: #0b3c5d; color: white; border: 0; border-radius: 8px; padding: 9px 12px; font-weight: 700; cursor: pointer; }}
    .gallery-actions button:hover, .shot-actions button:hover {{ background: #5bb9cc; }}
    #deleteAllGallery, .shot-actions button:last-child {{ background: #8b1e2d; }}
    .gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
    .shot-card {{ border: 1px solid #d7e6ec; border-radius: 8px; padding: 10px; background: #fff; }}
    .shot-card img {{ width: 100%; border-radius: 6px; background: #061826; display: block; }}
    .shot-meta {{ font-size: 12px; color: #456; margin: 8px 0; word-break: break-word; }}
    .shot-actions {{ display: flex; gap: 8px; }}
    </style>
    """,
    height=620,
)

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

st.info("Tip: In Smart Mirror mode, press Start Camera and allow browser camera access.")

