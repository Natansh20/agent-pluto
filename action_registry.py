ACTION_REGISTRY = {
    "FILESYSTEM": {
        "description": "View, create, read, write files and directories",
        "risk": "MEDIUM",
        "requires_confirmation": False,
    },
    "SYSTEM_CONTROL": {
        "description": "Control system settings like volume, brightness, or open Windows settings pages",
        "risk": "LOW",
        "requires_confirmation": False,
    },
    "PROCESS": {
        "description": "Run programs or scripts or system processes",
        "risk": "MEDIUM",
        "requires_confirmation": True,
    },
    "SYSTEM_INFO": {
        "description": "Query system information like volume, brightness, battery, disk usage",
        "risk": "LOW",
        "requires_confirmation": False
    }
}
