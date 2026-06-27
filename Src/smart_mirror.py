import cv2
import json
import math
import os
import time
from datetime import datetime

import mediapipe as mp

CONFIG_FILE = "config.json"
SCREENSHOT_DIR = "screenshots"

GESTURES_MENU_OPTIONS = [
    "One Finger",
    "Peace Sign",
    "Three Fingers",
    "Index and Pinky",
    "Rock Sign"
]

THEMES = {
    "Gesture Blue": {
        "primary": (93, 60, 11),
        "accent": (194, 167, 0),
        "white": (255, 255, 255)
    },
    "Dark Tech": {
        "primary": (38, 24, 6),
        "accent": (255, 229, 0),
        "white": (255, 255, 255)
    },
    "Event Purple": {
        "primary": (102, 23, 61),
        "accent": (255, 92, 179),
        "white": (255, 255, 255)
    }
}

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1
)

detector = HandLandmarker.create_from_options(options)


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {}


def hex_to_bgr(hex_color):
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (b, g, r)
    except Exception:
        return (194, 167, 0)


def get_settings(gesture):
    config = load_config()
    return config.get(gesture, {
        "message": f"{gesture} detected!",
        "color": "#00A7C2",
        "size": 1.0,
        "animation": "None"
    })


def get_app_settings():
    config = load_config()
    return config.get("settings", {
        "open_hand_mode": "Show Menu",
        "fullscreen": False,
        "show_fps": True,
        "show_landmarks": True,
        "theme": "Gesture Blue"
    })


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

def get_user_storage():
    username = st.session_state.username

    user_folder = os.path.join("users", username)
    screenshots_folder = os.path.join(user_folder, "screenshots")
    projects_folder = os.path.join(user_folder, "projects")
    config_file = os.path.join(user_folder, "config.json")

    os.makedirs(user_folder, exist_ok=True)
    os.makedirs(screenshots_folder, exist_ok=True)
    os.makedirs(projects_folder, exist_ok=True)

    return config_file, screenshots_folder, projects_folder

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


os.makedirs(SCREENSHOT_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

window_name = "Gesture AI Studios - Smart Mirror"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

settings = get_app_settings()
if settings.get("fullscreen", False):
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

menu_open = False
current_message = "Open your hand to show the menu"
current_color = (194, 167, 0)
current_size = 0.8
current_animation = "None"

gesture_history = []
history_size = 8
required_matches = 6

last_action_time = 0
cooldown = 1.3
tick = 0

last_time = time.time()
fps = 0

while True:
    tick += 1
    app_settings = get_app_settings()
    theme_colors = THEMES.get(app_settings.get("theme", "Gesture Blue"), THEMES["Gesture Blue"])

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    now_time = time.time()
    fps = 1 / max(now_time - last_time, 0.001)
    last_time = now_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    result = detector.detect(mp_image)

    raw_gesture = "None"

    if result.hand_landmarks:
        height, width, _ = frame.shape

        for hand_landmarks in result.hand_landmarks:
            raw_gesture = detect_gesture(hand_landmarks)

            if app_settings.get("show_landmarks", True):
                for landmark in hand_landmarks:
                    x = int(landmark.x * width)
                    y = int(landmark.y * height)
                    cv2.circle(frame, (x, y), 4, theme_colors["accent"], -1)

    gesture_history.append(raw_gesture)

    if len(gesture_history) > history_size:
        gesture_history.pop(0)

    stable_gesture = max(set(gesture_history), key=gesture_history.count)

    if gesture_history.count(stable_gesture) >= required_matches:
        detected_gesture = stable_gesture
    else:
        detected_gesture = "Stabilizing..."

    now = time.time()

    if now - last_action_time > cooldown:
        if detected_gesture == "Open Hand" and not menu_open:
            if app_settings.get("open_hand_mode", "Show Menu") == "Show Menu":
                menu_open = True
                current_message = "Menu opened - choose an option"
                current_color = theme_colors["accent"]
                current_size = 0.8
                current_animation = "Glow Box"
            else:
                settings = get_settings("Open Hand")
                current_message = settings.get("message", "Open Hand detected")
                current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
                current_size = float(settings.get("size", 1.0))
                current_animation = settings.get("animation", "None")

            last_action_time = now

        elif menu_open and detected_gesture in GESTURES_MENU_OPTIONS:
            settings = get_settings(detected_gesture)
            current_message = settings.get("message", detected_gesture)
            current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
            current_size = float(settings.get("size", 1.0))
            current_animation = settings.get("animation", "None")
            menu_open = False
            last_action_time = now

        elif menu_open and detected_gesture == "Closed Fist":
            current_message = "Menu closed"
            current_color = theme_colors["white"]
            current_size = 0.8
            current_animation = "None"
            menu_open = False
            last_action_time = now

        elif not menu_open and detected_gesture in [
            "Closed Fist",
            "One Finger",
            "Peace Sign",
            "Three Fingers",
            "Index and Pinky",
            "Rock Sign"
        ]:
            settings = get_settings(detected_gesture)
            current_message = settings.get("message", detected_gesture)
            current_color = hex_to_bgr(settings.get("color", "#00A7C2"))
            current_size = float(settings.get("size", 1.0))
            current_animation = settings.get("animation", "None")
            last_action_time = now

    display_color = current_color
    display_size = current_size

    if current_animation == "Pulse Text":
        display_size = current_size + 0.25 * abs(math.sin(tick / 8))

    if current_animation == "Rainbow Text":
        display_color = get_rainbow_color(tick)

    frame = draw_animation(frame, current_animation, display_color, tick)

    if menu_open:
        draw_menu(frame, theme_colors)

    put_wrapped_text(
        frame,
        current_message,
        (30, 420),
        display_size,
        display_color,
        thickness=2,
        max_width=780
    )

    cv2.putText(frame, f"Detected: {detected_gesture}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_colors["white"], 2)

    if app_settings.get("show_fps", True):
        cv2.putText(frame, f"FPS: {int(fps)}", (720, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_colors["white"], 2)

    cv2.putText(frame, "Q: Quit | S: Screenshot | F: Fullscreen | ESC: Window",
                (30, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.55, theme_colors["white"], 1)

    cv2.imshow(window_name, frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == ord("s"):
        filename = f"smart_mirror_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(os.path.join(SCREENSHOT_DIR, filename), frame)

    if key == ord("f"):
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if key == 27:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

cap.release()
cv2.destroyAllWindows()