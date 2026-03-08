import os

def init_agent_state():
    return {
        "cwd": os.getcwd(),
        "last_action": None,
        "last_observation": None,
        "conversation": [],
        "active_goal": None
    }
