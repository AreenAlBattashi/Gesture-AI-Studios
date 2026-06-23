import cv2
import json
import mediapipe as mp

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
cap = cv2.VideoCapture(0)

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def count_fingers(landmarks):
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    fingers_up = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if landmarks[tip].y < landmarks[pip].y:
            fingers_up += 1

    return fingers_up

def gesture_name(fingers):
    if fingers >= 4:
        return "Open Hand"
    elif fingers == 3:
        return "Three Fingers"
    elif fingers == 2:
        return "Two Fingers"
    elif fingers == 1:
        return "One Finger"
    else:
        return "Hand Detected"

while True:
    config = load_config()
    selected_gesture = config["gesture"]
    custom_message = config["message"]

    success, frame = cap.read()

    if not success:
        print("Camera not working")
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    result = detector.detect(mp_image)

    message = "No hand detected"
    color = (255, 255, 255)

    if result.hand_landmarks:
        h, w, _ = frame.shape

        for hand_landmarks in result.hand_landmarks:
            for landmark in hand_landmarks:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            fingers = count_fingers(hand_landmarks)
            detected_gesture = gesture_name(fingers)

            if detected_gesture == selected_gesture:
                message = custom_message
                color = (0, 255, 0)
            else:
                message = f"Detected: {detected_gesture}"
                color = (0, 255, 255)

    cv2.putText(
        frame,
        message,
        (30, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        3
    )

    cv2.imshow("Gesture AI Studios - Smart Mirror", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()