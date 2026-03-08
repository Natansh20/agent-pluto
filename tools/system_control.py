import subprocess
import wmi
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


SETTINGS_MAP = {
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "network": "ms-settings:network",
    "bluetooth": "ms-settings:bluetooth",
    "privacy": "ms-settings:privacy"
}


# -------------------------
# VOLUME HELPERS
# -------------------------

def get_volume_interface():
    device_enumerator = AudioUtilities.GetDeviceEnumerator()

    # 0 = eRender, 1 = eMultimedia (default speakers)
    default_device = device_enumerator.GetDefaultAudioEndpoint(0, 1)

    interface = default_device.Activate(
        IAudioEndpointVolume._iid_,
        CLSCTX_ALL,
        None
    )

    return cast(interface, POINTER(IAudioEndpointVolume))


def get_current_volume_percent():
    volume = get_volume_interface()
    return int(volume.GetMasterVolumeLevelScalar() * 100)


def set_volume_percent(percent):
    try:
        percent = max(0, min(100, percent))
        volume = get_volume_interface()
        volume.SetMasterVolumeLevelScalar(percent / 100, None)
        return {"volume successfully set to": percent, "status": "success"}
    except Exception as e:
        return {"error": f"Failed to set volume: {str(e)}", "status": "error"}


# -------------------------
# BRIGHTNESS HELPERS
# -------------------------

def get_current_brightness():
    c = wmi.WMI(namespace='wmi')
    brightness = c.WmiMonitorBrightness()[0]
    return brightness.CurrentBrightness


def set_brightness_percent(level):
    try:
        level = max(0, min(100, level))
        c = wmi.WMI(namespace='wmi')
        
        # Check if a monitor is actually found
        monitors = c.WmiMonitorBrightnessMethods()
        if not monitors:
            return {"error": "No WMI-compatible monitor found (Common on Desktops)"}
        
        # The second argument (0) is the timeout in seconds
        monitors[0].WmiSetBrightness(level, 0)
        return {"brightness_set_to": level, "status": "success"}
    except Exception as e:
        return {"error": f"Failed to set brightness: {str(e)}", "status": "error"}


# -------------------------
# MAIN TOOL FUNCTION
# -------------------------

def system_control_tool(operation, target, value=None):

    # OPEN SETTINGS
    if operation == "open":
        if target in SETTINGS_MAP:
            subprocess.run(["start", SETTINGS_MAP[target]], shell=True)
            return {"opened": target}

        if target == "settings":
            subprocess.run(["start", "ms-settings:"], shell=True)
            return {"opened": "settings"}

    # VOLUME CONTROL
    if target == "volume" or target == "sound":
        current = get_current_volume_percent()

        if operation == "set":
            return set_volume_percent(value)

        if operation == "increase":
            return set_volume_percent(current + (value or 4))

        if operation == "decrease":
            return set_volume_percent(current - (value or 4))

    # BRIGHTNESS CONTROL
    if target == "brightness":
        current = get_current_brightness()

        if operation == "set":
            return set_brightness_percent(value)

        if operation == "increase":
            return set_brightness_percent(current + (value or 10))

        if operation == "decrease":
            return set_brightness_percent(current - (value or 10))

    return {"error": "Unsupported system control operation"}

if __name__ == "__main__":
    # Example usage
    # print(system_control_tool("set", "volume", 20))
    print(system_control_tool("set", "brightness", 80))