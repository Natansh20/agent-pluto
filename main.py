from agent_state import init_agent_state
from llm_interface import query_llm
from executor import execute_action
from ui import get_user_input
import json

MAX_STEPS = 10

# Maps each action to a function that extracts a human-readable result summary
# from last_observation. Returns None if the result doesn't indicate completion.
def summarize_result(obs_action: str, last_obs: dict) -> str | None:
    """
    Given the last action and its observation, return a completion summary
    string if the action succeeded, or None if it failed / is not terminal
    """
    if obs_action == "PROCESS":
        returncode = last_obs.get("returncode", -1)
        if returncode == 0:
            stdout = last_obs.get("stdout", "").strip()
            return f"Script output: {stdout}" if stdout else "Script ran with no output."
        return None
    
    if obs_action == "FILESYSTEM":
        op = last_obs.get("operation")
        status = last_obs.get("status")
        if status != "success":
            return None
        if op == "read":
            content = last_obs.get("content", "").strip()
            return f"File contents: \n{content}"
        if op in ("create", "write"):
            return None # not terminal, file still needs to be run
        if op == "view":
            content = last_obs.get("content", "").strip()
            return f"Directory listing: \n{content}"
        
    if obs_action == "SYSTEM_INFO":
        info = {k: v for k,v in last_obs.items() if k!= "action"}
        if info:
            summary = ", ".join(f"{k}: {v}" for k,v in info.items())
            return f"System info retrieved - {summary}"
        
    if obs_action == "SYSTEM_CONTROL":
        status = last_obs.get("status")
        message = last_obs.get("message", "")
        if status == "success":
            return f"System control succeeded. {message}".strip()
    
    return None

def main():
    state = init_agent_state()
    steps = 0
    last_written_file = None
    write_count = {}
    last_run_failed = False

    while steps < MAX_STEPS:

        # Get new task
        if state["active_goal"] is None:
            user_input = get_user_input()
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            # user_input = get_rephrased_input(user_input)
            state["conversation"].append({"user": user_input})
            state["active_goal"] = user_input
            steps = 0  # reset steps for new task
            last_written_file = None
            write_count = {}
            last_run_failed = False

        # Reasoning Loop
        if steps >= MAX_STEPS:
            print("Reached max reasoning steps. Clearing goal.")
            state["active_goal"] = None
            continue
        
        # Build directive based on last_observation
        directive = None
        last_obs = state.get("last_observation", {})
        # print(f"\n[Last Observation] {last_obs}\n")

        if isinstance(last_obs, dict):
            op = last_obs.get("args").get("operation")
            path = last_obs.get("args").get("path")
            status = last_obs.get("status")
            obs_action = last_obs.get("action") # "FILESYSTEM" or "PROCESS"

            # print(f"Extracted from last_obs - op: {op}, path: {path}, status: {status}, obs_action: {obs_action}")

            if (obs_action == "FILESYSTEM" and status in ("success", "exists") and op in ("create", "write") and path):
                last_written_file = path
                write_count[path] = write_count.get(path, 0) + 1

                if not last_run_failed:
                    directive = (
                        f"The file '{path}' was successfully written. "
                        f"Do NOT rewrite it. Your NEXT step MUST be to run it using "
                        f"PROCESS with script='{path}'."
                    )
                else:
                    last_run_failed = False
                    directive = (
                        f"The file '{path}' has been rewritten to fix the error. "
                        f"Now run it using PROCESS with script='{path}'."
                    )
            # PROCESS: script failed -> fix and retry
            elif obs_action == "PROCESS" and (status == "error" or last_obs.get("returncode", 0) != 0):
                last_run_failed = True
                error_detail = last_obs.get("stderr") or last_obs.get("error", "unknown error")
                directive = (
                    f"The script failed with this error:\n{error_detail}\n"
                    f"Fix the code in '{last_written_file}' using FILESYSTEM write, then run it again."
                ) 

            # All other actions: check for completion
            else:
                completion_summary = summarize_result(obs_action, last_obs)
                if completion_summary:
                    last_run_failed = False
                    directive = (
                        f"The action completed successfully.\n"
                        f"{completion_summary}\n"
                        f"The task is complete. Respond to the user with the result."
                        f"Do NOT call any more tools"
                    )
        # if directive:
        #     print(f"\n[Directive Injected] {directive}")
            
        llm_output = query_llm(state["active_goal"], state, directive = directive)

        if llm_output["type"] == "TOOL_CALL":
            action = llm_output["action"]
            args = llm_output["args"]

            # Loop Guard: Prevent rewriting the same file repeatedly
            if (
                action == "FILESYSTEM"
                and args.get("operation") in ("create", "write")
                and args.get("path") == last_written_file
                and not last_run_failed                       # <-- key condition
                and write_count.get(last_written_file, 0) >= 1
            ):
                print(
                    f"\n[Loop Guard] LLM tried to rewrite '{last_written_file}' "
                    f"but last run did not fail. Forcing PROCESS step instead."
                )
                llm_output = {
                    "type": "TOOL_CALL",
                    "action": "PROCESS",
                    "args": {"script": last_written_file, "args": []}
                }
                action = llm_output["action"]
                args = llm_output["args"]

            steps += 1
            result = execute_action(action, args, state)
            print(f"\n[Tool Result] {result}\n")

            # Tag the observation with the action so we can detect PROCESS failures
            if isinstance(result, dict):
                result["action"] = action
                result["args"] = args
            state["last_observation"] = result


            # print(f"\n[Tool Result] {result}\n")

            # state["conversation"].append({
            #     "tool": llm_output["action"],
            #     "args": llm_output["args"],
            #     "result": result
            # })

            state["conversation"].append({
                "role": "tool",
                "name": action,
                "content": json.dumps(result)
            })

            # print(f"\n[Updated State] State: {state}\n")
            continue

        if llm_output["type"] == "RESPONSE":

            # If there is still an active goal and no tool was used, this is likely premature termination
            if state["active_goal"] is not None and state["last_observation"] is None:
                print("\n Model attempted to respond before completing task. Forcing continuation.")
                continue
            print("\nAgent Response: " + llm_output["content"])
            state["conversation"].append({"assistant": llm_output["content"]})
            state["active_goal"] = None # This breaks the reasoning loop
            state["last_observation"] = None # Clear observation for next task
            last_written_file = None
            write_count = {}
            last_run_failed = False
            continue

        print("Unknown agent output:", llm_output)
        print("Attempting recovery")
        continue

    else:
        print("Agent stopped after reaching step limit.")

if __name__ == "__main__":
    main()
