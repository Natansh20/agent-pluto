# Local AI Windows Agent

A locally running AI agent that interprets natural language instructions and performs actions on a Windows system using structured tools.

The agent uses a reasoning loop powered by a local LLM (via Ollama) to decide which tool to call next until the user's goal is completed.

---

## Features

### Natural Language Task Execution
The agent accepts natural language instructions and decides whether to:

- Call a system tool
- Execute a script
- Read or write files
- Retrieve system information
- Respond to the user

Example:
```
Write a Python script that checks if a number is prime and run it with input 13
```

The agent will generate the script, save it to disk, run it, and return the output.

---

## Supported Tools

The agent interacts with the system through four structured tools.

### FILESYSTEM

Used for interacting with files and directories.

Supported operations:

- `view` – list directory contents
- `read` – read file contents
- `create` – create a new file
- `write` – write or overwrite file contents

Example tool call:

```json
{
  "type": "TOOL_CALL",
  "action": "FILESYSTEM",
  "args": {
    "operation": "create",
    "path": "python_workspace/example.py",
    "content": "print('hello')"
  }
}
```
### PROCESS
Runs programs or scripts on the system.

Supported options:

- Run Python scripts
- Run shell commands
- Pass command line arguments

Example:

```json
{
  "type": "TOOL_CALL",
  "action": "PROCESS",
  "args": {
    "script": "python_workspace/script.py",
    "args": ["10"]
  }
}
```

Scripts are previewed before execution and require confirmation.

---

### SYSTEM_CONTROL

Controls certain Windows system settings.

Supported targets:

- volume
- brightness
- settings
- display
- sound
- network
- bluetooth
- privacy

Example:

```json
{
  "type": "TOOL_CALL",
  "action": "SYSTEM_CONTROL",
  "args": {
    "operation": "increase",
    "target": "volume",
    "value": 10
  }
}
```
### SYSTEM_INFO

Retrieves system information.

Supported queries:
- disk usage
- battery status
- volume level
- screen brightness

Example:
```json
{
  "type": "TOOL_CALL",
  "action": "SYSTEM_INFO",
  "args": {
    "query": "battery"
  }
}
```

### Agent Workflow
The agent operates in a loop:
1. Receive user input
2. Send task and context to the LLM
3. LLM decides the next action
4. Execute the selected tool
5. Store the result as an observation
6. Repeat until the task is complete

### Architecture

#### `main.py`
Controls the main reasoning loop.

Responsibilities:
- Receive user input
- Maintain agent state
- Call the LLM for the next action
- Execute tools
- Track conversation history
- Stop execution after a step limit

#### `llm_interface.py`
Handles interaction with the language model.

Functions include:

- Prompt construction
- JSON extraction from model output
- Tool call normalization
- Input rephrasing for clarity

The system runs models locally using Ollama.

#### `executor.py`
Executes tool calls returned by the LLM.

Responsibilities:

- Route tool calls to the correct tool
- Run scripts and commands
- Show script previews before execution
- Ask for confirmation when running processes

#### `agent_state.py`
Stores the internal state of the agent.

Example structure:
```python
{
  "cwd": current working directory,
  "last_action": last executed tool,
  "last_observation": tool result,
  "conversation": interaction history,
  "active_goal": current task
}
```

### Safety Measures

The system includes several safeguards:

- Script preview before execution
- User confirmation for running processes
- Step limit to prevent infinite loops
- Controlled set of tools available to the agent

### Example Interaction
User:
```code
Write a Python script that checks whether a number is prime and run it with input 13
```
Agent actions:

1. Create Python script
2. Write code to file
3. Execute script
4. Return output
