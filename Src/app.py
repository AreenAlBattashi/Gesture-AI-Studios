import streamlit as st
import json
import subprocess
import sys

st.set_page_config(page_title="Gesture AI Studios", layout="wide")

CONFIG_FILE = "config.json"

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
        "color": "#00FF00",
        "size": 1.0,
        "animation": "None"
    }

st.title("Gesture AI Studios")
st.write("Customize gestures, actions, colors, animations, and smart mirror behavior.")
st.write("Developed by: Areen Ahmed Nasser Albattashi")
config = load_config()

st.sidebar.header("Administrator Panel")

settings = config.get("settings", {})
open_hand_mode = st.sidebar.selectbox(
    "Open Hand Behavior",
    OPEN_HAND_MODES,
    index=OPEN_HAND_MODES.index(settings.get("open_hand_mode", "Show Menu"))
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
        config[gesture].get("color", "#00FF00"),
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

if st.sidebar.button("Save All Settings"):
    save_config(config)
    st.sidebar.success("Settings saved!")

if st.sidebar.button("Run Smart Mirror"):
    save_config(config)
    subprocess.Popen([sys.executable, "src/smart_mirror.py"])
    st.sidebar.success("Smart Mirror started!")

st.subheader("Current Setup")

st.write(f"**Open Hand Behavior:** {config['settings']['open_hand_mode']}")

for gesture in GESTURES:
    st.write(
        f"**{gesture}** → {config[gesture]['message']} | "
        f"Color: {config[gesture]['color']} | "
        f"Size: {config[gesture]['size']} | "
        f"Animation: {config[gesture]['animation']}"
    )