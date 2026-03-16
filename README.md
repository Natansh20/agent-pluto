# Pluto — Local AI Windows Agent

A locally running AI agent that interprets natural language instructions and performs actions on a Windows system using structured tools. The agent uses a reasoning loop powered by a local or cloud LLM to decide which tool to call next until the user's goal is completed.

---


## Requirements

- Windows 10 or 11
- Python 3.12+
- For **Local mode**: [Ollama](https://ollama.com) installed and running
- For **Online mode**: A free [Gemini API key](https://aistudio.google.com/app/apikey)

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/pluto-agent.git
cd pluto-agent
```

### 2. Create a virtual environment
```bash
python -m venv ai_agent
ai_agent\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your mode

#### Local mode (Ollama)

Install Ollama from [https://ollama.com](https://ollama.com), then pull the model:
```bash
ollama pull qwen2.5:7b
```

Make sure Ollama is running before launching Pluto. No further configuration needed.

#### Online mode (Gemini)

Get a free API key from [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

---

## Running the App
```bash
python agent_ui.py
```

On launch, a mode picker will appear. Select **Local** (Ollama / qwen2.5) or **Online** (Gemini). The mode cannot be changed without restarting the app.

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

### FILESYSTEM
Interacts with files and directories.

| Operation | Description |
|-----------|-------------|
| `view` | List directory contents |
| `read` | Read file contents |
| `create` | Create a new file |
| `write` | Write or overwrite a file |

### PROCESS
Runs programs or scripts on the system. Scripts are previewed before execution and require user confirmation.

| Option | Description |
|--------|-------------|
| `script` | Run a Python script |
| `command` | Run a shell command |
| `args` | Optional CLI arguments |

### SYSTEM_CONTROL
Controls Windows system settings.

Supported targets: `volume`, `brightness`, `settings`, `display`, `sound`, `network`, `bluetooth`, `privacy`

### SYSTEM_INFO
Retrieves system information.

Supported queries: `disk`, `battery`, `volume`, `brightness`

---

## Architecture

| File | Responsibility |
|------|---------------|
| `agent_ui.py` | Tkinter UI, mode picker, subprocess communication |
| `main.py` | Main reasoning loop, tool dispatch, conversation state |
| `llm_interface.py` | Prompt construction, LLM routing (local / online), JSON parsing |
| `executor.py` | Tool execution, script preview, confirmation prompts |
| `agent_state.py` | Agent state initialisation |
| `action_registry.py` | Registry of available tools and their metadata |

---

## Safety Measures

- Script preview before execution
- User confirmation required to run any process
- Step limit prevents infinite reasoning loops
- Restricted, well-defined tool set

---

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

## Example Interaction

**User:**
```
Write a Python script that checks whether a number is prime and run it with input 13
```

**Agent actions:**
1. Create Python script
2. Write code to file
3. Show script preview and ask for confirmation
4. Execute script with argument `13`
5. Return output to the user
