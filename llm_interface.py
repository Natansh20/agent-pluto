import subprocess
import json
import re


# ---------- Robust JSON extraction ----------
def extract_json(text: str):
    """
    Extract JSON from LLM output.
    Handles:
    - extra text
    - missing outer braces
    - escaped underscores
    """
    text = text.strip()
    text = text.replace(r"\_", "_")

    # Try direct JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group()
        json_str = (
            json_str
            .replace(": None", ": null")
            .replace(": True", ": true")
            .replace(": False", ": false")
        )
        return json.loads(json_str)

    raise ValueError(f"Could not parse JSON from LLM output:\n{text}")

def normalize_llm_output(parsed: dict):
    """
    Force LLM output into agent schema.
    """
    # If model used tool name as type
    if parsed.get("type") in ["FILESYSTEM", "SYSTEM_CONTROL", "PROCESS", "SYSTEM_INFO"]:
        return {
            "type": "TOOL_CALL",
            "action": parsed["type"],
            "args": parsed.get("args", {})
        }
    
    # Already valid
    if parsed.get("type") == "TOOL_CALL":
        return parsed

    # Infer SYSTEM_CONTROL
    if "operation" in parsed and "target" in parsed:
        return {
            "type": "TOOL_CALL",
            "action": "SYSTEM_CONTROL",
            "args": parsed
        }

    # Infer FILESYSTEM
    if "operation" in parsed and "path" in parsed:
        return {
            "type": "TOOL_CALL",
            "action": "FILESYSTEM",
            "args": parsed
        }

    # Infer PROCESS
    if "command" in parsed or "script" in parsed:
        return {
            "type": "TOOL_CALL",
            "action": "PROCESS",
            "args": parsed
        }

    # Infer SYSTEM_INFO
    if "query" in parsed:
        return {
            "type": "TOOL_CALL",
            "action": "SYSTEM_INFO",
            "args": parsed
        }

    # Fallback
    return {
        "type": "RESPONSE",
        "content": parsed.get("content","I couldn't understand that request.")
    }


# ---------- Agentic LLM interface ----------
def query_llm(user_input: str, agent_state: dict, directive: str = None):
    """
    Agent reasoning step. Directive is an optional override message
    injected at the top of the prompt to break loops.
    
    Decides whether to:
    - call a tool
    - respond to the user
    """

    directive_block = ""
    if directive:
        directive_block = f"""
        ================================================
        !! IMPORTANT DIRECTIVE (follow this NOW) !!
        {directive}
        ================================================
        """

    prompt = f"""
    You are an AI SYSTEM AGENT running on Windows.

    You can either:
    1. CALL A TOOL
    2. RESPOND TO THE USER

    {directive_block}

    ------------------------------------------------
    AVAILABLE TOOLS

    FILESYSTEM:
    - operation: view | create | write | read
    - path: file or directory path
    - content: optional (for write/create)

    SYSTEM_CONTROL:
    - operation: increase | decrease | set | open
    - target: volume | brightness | settings | display | sound | network | bluetooth | privacy
    - value: optional integer

    PROCESS:
    - command: shell command to run
    - script: python script path to run
    - args: optional list of arguments

    SYSTEM_INFO:
    - query: volume | brightness | battery | disk

    ------------------------------------------------
    CURRENT STATE

    Current working directory:
    {agent_state['cwd']}

    Last tool observation:
    {agent_state['last_observation']}

    Conversation history:
    {agent_state['conversation']}

    Active goal (task not yet completed):
    {agent_state['active_goal']}

    ------------------------------------------------
    USER REQUEST
    "{user_input}"

    ------------------------------------------------
    RULES

    - Decide the NEXT BEST STEP.
    - Call ONE tool at a time if needed.
    - Continue calling tools until the Active goal is fully complete.
    - If no tool is needed, respond to the user.
    - Be concise. Do NOT explain reasoning.

    SYSTEM DATA RULE:
    You do NOT have access to real system data.
    All system information must be retrieved via SYSTEM_INFO.

    MULTI-STEP TASK RULES
    - Tasks may require multiple tool calls.
    - Tool calls may depend on previous results.
    - Do not stop after a partial step.
    - Verify a script exists with FILESYSTEM view before running it.
    - If missing, create it first.

    FILE CREATION RULE
    If a file was successfully created or written and the tool result contains:
    "created" or "written",
    you MUST assume the file now exists and proceed to the next step.
    Do NOT repeatedly read or rewrite the same file unless the tool result contains an error or the file content is incorrect.

    CODING WORKFLOW

    For tasks that require writing AND running Python code:

    STEP 1 — FILESYSTEM create: write the script ONCE.
    STEP 2 — PROCESS script: run the script immediately after creation.
    STEP 3 — RESPONSE: report the output to the user.

    Never repeat STEP 1 if it already succeeded.

    CODE RULES
    - Preserve correct syntax and indentation.
    - Python uses 4 spaces indentation.
    - Include required imports.
    - Code must run without syntax errors.
    - Scripts must accept sys.argv for arguments.
    - While running a script, also pass the required cli arguments via PROCESS args if needed. For example, python_script.py arg1

    PATH RULES
    - Prefer forward slashes (/)
    - Wrap paths containing spaces in double quotes.  

    ------------------------------------------------
    RESPONSE FORMAT

    TOOL CALL:
    {{
    "type": "TOOL_CALL",
    "action": "<ONE_OF: FILESYSTEM | SYSTEM_CONTROL | PROCESS | SYSTEM_INFO>",
    "args": {{
        "operation": "...",
        "path": "...",
        "content": "...",
        "target": "...",
        "value": 10
    }}
    }}

    USER RESPONSE:
    {{
    "type": "RESPONSE",
    "content": "text shown to the user"
    }}

    EXAMPLE TOOL CALL:

    {{
    "type": "TOOL_CALL",
    "action": "FILESYSTEM",
    "args": {{
        "operation": "create",
        "path": "python_workspace/example.py",
        "content": "import sys\n\nif len(sys.argv) > 1:\n    print(sys.argv[1])"
    }}
    }}

    ------------------------------------------------

    CRITICAL

    - Output ONLY valid JSON.
    - Follow the RESPONSE FORMAT exactly.
    - Use double quotes for all strings.
    - Do NOT escape underscores.
    - Do NOT end lines with backslashes.
    - Choose exactly ONE action from:
        FILESYSTEM
        SYSTEM_CONTROL
        PROCESS
        SYSTEM_INFO
    - Do NOT combine actions.

    """

    result = subprocess.run(
        ["ollama", "run", "qwen2.5-7b-8k", "--format", "json"],
        input=prompt,
        text=True,
        encoding="utf-8",
        capture_output=True
    )

    raw_output = result.stdout.strip()

    try:
        parsed = extract_json(raw_output)
        normalized = normalize_llm_output(parsed)
    
        # print(f"\n[LLM Parsed Output]\n{json.dumps(parsed, indent=2)}")
        # print(f"\n[LLM Normalized Output]\n{json.dumps(normalized, indent=2)}")
        return normalized
        # return parsed
    
    except Exception as e:
        print("\n[LLM RAW OUTPUT]")
        print(raw_output)
        raise e
    