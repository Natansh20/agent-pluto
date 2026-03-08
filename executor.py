import os
import subprocess
import sys
import shlex

from tools.filesystem_tool import filesystem_tool
from tools.system_control import system_control_tool
from tools.system_info import system_info_tool
from action_registry import ACTION_REGISTRY

# os.makedirs("python_workspace", exist_ok=True)

def execute_action(action, args, agent_state):

    if not isinstance(args, dict):
        return {"error": "Malformed tool arguments from LLM"}

    action = action.upper()
    metadata = ACTION_REGISTRY.get(action)
    result = None

    # CONFIRMATION LAYER
    if metadata and metadata.get("requires_confirmation", False):

        print(f"\nAction: {action}")
        print(f"Risk Level: {metadata.get('risk')}")
        print(f"Description: {metadata.get('description')}")

        # if it's a script, show preview
        if action == "PROCESS" and args.get("script"):
            script_path = args["script"]
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    code_preview = f.read(500)
                print("\n--- Script Preview (first 500 chars) ---")
                print(code_preview)
                print("----------------------------------------")
            except:
                print("Could not preview script.")

        confirm = input(f"\nProceed? (yes/no): ")

        if confirm.lower() != "yes":
            return {"cancelled": True}

    # ECECUTION

    if action == "FILESYSTEM":
        result = filesystem_tool(**args)

    elif action == "SYSTEM_CONTROL":
        result = system_control_tool(**args)

    elif action == "PROCESS":
        result = run_process(**args)

    elif action == "SYSTEM_INFO":
        result = system_info_tool(**args)

    else:
        result = {"error": "Unknown action"}

    agent_state["last_action"] = action
    agent_state["last_observation"] = result

    return result

# SAFE PROCESS EXECUTION
def run_process(command=None, script=None, args=None):
    VENV_PYTHON = r".\ai_agent\Scripts\python.exe" # Path to virtual environment
    # Use the virtual env if it exists
    python_exec = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    # SAFE_DIR = os.path.abspath("python_workspace")
    
    try:    
        
        if script:
            script_path = os.path.abspath(script)

            # Only allow .py files
            if not script_path.endswith(".py"):
                return {"error": "Only Python (.py) scripts are allowed"}
            
            # When using 'script', we can safely wrap the path in a list
            cmd = [python_exec, script]
            if args:
                # Ensure args is a list
                if isinstance(args, list):
                    cmd.extend([str(a) for a in args])
                else:
                    cmd.append(str(args))
            
            # Using a list with shell=False is the safest way to handle spaces
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            result = {"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}
            if completed.returncode == 0:
                print(f"\nScript Output: {completed.stdout.strip()}")
            else:
                print(f"\nScript error: {completed.stderr.strip()}")
            return result
        
        if command:
            
            print(f"\nCommand to execute:\n{args['command']}")

            if isinstance(command, str):
                # posix=False is crucial for Windows paths with backslashes
                command_list = shlex.split(command, posix=False)
                
                # If the first word is 'python', swap it for our specific executable
                if command_list[0].lower() == "python":
                    command_list[0] = python_exec
            else:
                command_list = command

            completed = subprocess.run(command_list, capture_output=True, text=True, timeout=15)
            return {"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}
        
        return {"error": "No command or script provided"}
    
    except Exception as e:
        return {"error": str(e)}

