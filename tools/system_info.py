import shutil
import psutil
import os
import wmi

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# Volume Helper

def get_current_volume_percent():
    # Get default audio endpoint
    speakers = AudioUtilities.GetDeviceEnumerator()

    # Get the default speakers (0 = eRender, 1 = eMultimedia)
    interface = speakers.GetDefaultAudioEndpoint(0,1)

    volume_object = interface.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(volume_object, POINTER(IAudioEndpointVolume))
    return int(volume.GetMasterVolumeLevelScalar() * 100)

# Brightness Helper

def get_current_brightness():
    c = wmi.WMI(namespace='wmi')
    brightness = c.WmiMonitorBrightness()[0]
    return brightness.CurrentBrightness

# Main Tool

def system_info_tool(query):

    # -------------------------
    # Disk Usage
    # -------------------------
    if query == "disk":
        total, used, free = shutil.disk_usage(os.getcwd())
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free
        }

    # -------------------------
    # Battery
    # -------------------------
    if query == "battery":
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": battery.percent,
                "plugged_in": battery.power_plugged
            }
        return {"error": "Battery information not available"}

    # -------------------------
    # Volume
    # -------------------------
    if query == "volume":
        try:
            return {
                "current_volume_percent": get_current_volume_percent()
            }
        except Exception as e:
            return {"error": f"Volume query failed: {str(e)}"}

    # -------------------------
    # Brightness
    # -------------------------
    if query == "brightness":
        try:
            return {
                "current_brightness_percent": get_current_brightness()
            }
        except Exception as e:
            return {"error": f"Brightness query failed: {str(e)}"}

    # -------------------------
    # Memory Usage
    # -------------------------
    if query == "memory":
        mem = psutil.virtual_memory()
        return {
            "total_bytes": mem.total,
            "used_bytes": mem.used,
            "available_bytes": mem.available,
            "percent_used": mem.percent
        }

    # -------------------------
    # CPU Usage
    # -------------------------
    if query == "cpu":
        return {"cpu_percent": psutil.cpu_percent(interval=1)}

    return {"error": f"Unsupported system info query: {query}"}