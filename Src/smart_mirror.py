import cv2
import json
import time
import math
import mediapipe as mp

CONFIG_FILE = "config.json"

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
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)

def get_open_hand_mode():
    config = load_config()
    return config.get("settings", {}).get("open_hand_mode", "Show Menu")

def get_settings(gesture):
    config = load_config()
    return config.get(gesture, {
        "message": f"{gesture} detected!",
        "color": "#00FF00",
        "size": 1.0,
        "animation": "None"
    })

def draw_animation(frame, animation, color, tick):
    h, w, _ = frame.shape

    if animation == "Glow Box":
        cv2.rectangle(frame, (20, 20), (w - 20, h - 20), color, 6)

    elif animation == "Confetti":
        for i in range(25):
            x = (i * 67 + tick * 8) % w
            y = (i * 41 + tick * 6) % h
            cv2.circle(frame, (x, y), 4, color, -1)

    elif animation == "Moving Circle":
        x = int((math.sin(tick / 10) + 1) * w / 2)
        cv2.circle(frame, (x, 120), 25, color, -1)

    elif animation == "Frame Flash":
        thickness = 8 if tick % 20 < 10 else 3
        cv2.rectangle(frame, (10, 10), (w - 10, h - 10), color, thickness)

    return frame

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

def draw_menu(frame):
    cv2.rectangle(frame, (35, 70), (620, 345), (0, 0, 0), -1)

    cv2.putText(frame, "Gesture Menu", (65, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.putText(frame, "One Finger      : Option 1", (65, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.putText(frame, "Peace Sign      : Option 2", (65, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.putText(frame, "Three Fingers   : Option 3", (65, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.putText(frame, "Index + Pinky   : Option 4", (65, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.putText(frame, "Closed Fist     : Close Menu", (65, 320),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

menu_open = False
current_message = "Open your hand to show menu"
current_color = (0, 255, 0)
current_size = 0.8
current_animation = "None"

gesture_history = []
history_size = 8
required_matches = 6

last_action_time = 0
cooldown = 1.5
tick = 0

while True:
    tick += 1

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    result = detector.detect(mp_image)

    raw_gesture = "None"

    if result.hand_landmarks:
        h, w, _ = frame.shape

        for hand_landmarks in result.hand_landmarks:
            raw_gesture = detect_gesture(hand_landmarks)

            for landmark in hand_landmarks:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

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
            mode = get_open_hand_mode()

            if mode == "Show Menu":
                menu_open = True
                current_message = "Menu opened - choose an option"
                current_color = (0, 255, 255)
                current_size = 0.8
                current_animation = "Glow Box"
            else:
                settings = get_settings("Open Hand")
                current_message = settings.get("message", "Open Hand detected")
                current_color = hex_to_bgr(settings.get("color", "#00FF00"))
                current_size = float(settings.get("size", 1.0))
                current_animation = settings.get("animation", "None")

            last_action_time = now

        elif menu_open and detected_gesture in [
            "One Finger",
            "Peace Sign",
            "Three Fingers",
            "Index and Pinky",
            "Rock Sign"
        ]:
            settings = get_settings(detected_gesture)
            current_message = settings.get("message", detected_gesture)
            current_color = hex_to_bgr(settings.get("color", "#00FF00"))
            current_size = float(settings.get("size", 1.0))
            current_animation = settings.get("animation", "None")
            menu_open = False
            last_action_time = now

        elif menu_open and detected_gesture == "Closed Fist":
            current_message = "Menu closed"
            current_color = (255, 255, 255)
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
            current_color = hex_to_bgr(settings.get("color", "#00FF00"))
            current_size = float(settings.get("size", 1.0))
            current_animation = settings.get("animation", "None")
            last_action_time = now

    if current_animation == "Pulse Text":
        display_size = current_size + 0.25 * abs(math.sin(tick / 8))
    else:
        display_size = current_size

    frame = draw_animation(frame, current_animation, current_color, tick)

    if menu_open:
        draw_menu(frame)

    cv2.putText(frame, current_message, (30, 430),
                cv2.FONT_HERSHEY_SIMPLEX, display_size, current_color, 2)

    cv2.putText(frame, f"Detected: {detected_gesture}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Gesture AI Studios - Smart Mirror", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()