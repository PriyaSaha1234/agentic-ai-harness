# Agentic AI Harness

A custom agentic AI harness built in Python that combines LLM-powered reasoning, tool calling, persistent memory, task planning, MCP integration, failure recovery, and autonomous workspace execution.

The project demonstrates how an AI agent can reason about a task, select and execute tools, maintain context, recover from failures, and produce persistent artifacts.

## Features

* **LLM-Powered Agent** — Uses Google Gemini for reasoning and decision-making.
* **Tool Calling** — Dynamically selects and executes tools based on the task.
* **Persistent Memory** — Stores important information that remains available across sessions.
* **Task Planning** — Breaks complex tasks into steps and tracks their completion.
* **MCP Integration** — Connects external tools through the Model Context Protocol.
* **File Reading & Writing** — Safely reads workspace files and creates generated artifacts.
* **Failure Recovery** — Handles failed tool calls and avoids repeatedly executing the same failed operation.
* **Conversation History** — Maintains context throughout an ongoing interaction.
* **Safe Calculator** — Evaluates mathematical expressions without using unsafe `eval()`.
* **Autonomous Workspace Execution** — Analyzes workspace data and generates persistent reports and other artifacts.

## Architecture

The system follows an agent loop in which the user provides a task, the Gemini-powered agent determines the required actions, selects appropriate tools, processes their results, and continues until the task is completed.

The main components are:

* **Agent** — Handles the reasoning loop, conversation history, Gemini integration, and tool execution.
* **Task Planner** — Creates and tracks multi-step execution plans.
* **Tool Manager** — Provides local tools for calculations, file operations, memory, and planning.
* **Persistent Memory** — Stores information in `memory.md` for use across sessions.
* **MCP Server** — Provides additional tools through the Model Context Protocol.
* **Workspace** — Stores input files and generated artifacts.

## Tech Stack

* Python 3.13+
* Google Gemini API
* Google GenAI SDK
* Model Context Protocol (MCP)
* Pydantic
* Git / GitHub

## Project Structure

```text
agentic-ai-harness/
│
├── agent.py              # Main agent loop and Gemini integration
├── tools.py              # Local tool implementations
├── planner.py            # Task planning and execution tracking
├── memory.py             # Persistent memory management
├── memory.md             # Stored agent memories
│
├── mcp/
│   └── server.py         # MCP tool server
│
├── workspace/
│   ├── test.txt
│   └── analysis_report.md
│
├── mcp_servers.json      # MCP server configuration
├── pyproject.toml        # Project configuration
└── .gitignore
```

## How It Works

The agent receives a user request and determines what actions are required.

For a multi-step task, the agent can:

1. Create an execution plan.
2. Select the appropriate tools.
3. Execute the tools.
4. Inspect the returned results.
5. Track completed steps.
6. Recover from tool failures when possible.
7. Generate a final response or persistent workspace artifact.

This allows the system to move beyond simple question answering and perform actual multi-step tasks.

## Example

### User Request

```text
Analyze test.txt and create a report called analysis_report.md.

The report should contain:
1. A brief summary of the file.
2. The total number of bullet points.
3. The percentage represented by 3 out of the total number of bullet points.
4. A short conclusion.

Save the completed report inside the workspace folder.
```

### Agent Execution

The agent reads the requested file, analyzes its contents, performs the required calculation, generates the report, and saves it using the workspace file-writing tool.

### Generated Result

```text
Total bullet points: 5
3 out of 5 bullet points: 60%
```

The generated report is saved inside the `workspace/` directory.

## Available Tools

### Local Tools

| Tool                 | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `calculator`         | Safely evaluates mathematical expressions |
| `read_file`          | Reads files from the workspace            |
| `write_file`         | Creates or overwrites workspace artifacts |
| `save_memory`        | Stores information for future sessions    |
| `get_memory`         | Retrieves persistent memory               |
| `create_plan`        | Creates a multi-step execution plan       |
| `complete_plan_step` | Marks a plan step as completed            |
| `get_plan_status`    | Displays the current plan status          |

### MCP Tools

The project also includes an MCP server providing workspace-related tools such as:

* `get_time`
* `list_workspace_files`

## Safety

The harness includes several safeguards around tool execution.

* File operations are restricted to the workspace.
* Mathematical expressions are evaluated using a safe AST-based parser instead of `eval()`.
* Repeated failed tool calls are limited.
* Tool execution errors are handled explicitly.
* API credentials are loaded through environment variables rather than being stored in source code.

## Installation

Clone the repository:

```bash
git clone https://github.com/PriyaSaha1234/agentic-ai-harness.git
cd agentic-ai-harness
```

Install the project and its dependencies:

```bash
pip install -e .
```

Set your Gemini API key as an environment variable.

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

Run the agent:

```powershell
python agent.py
```

## Environment Variables

The project expects:

```text
GEMINI_API_KEY
```

The API key should never be committed to GitHub.

## Future Improvements

* Additional MCP servers and external tools
* More advanced long-term memory
* Improved planning and task decomposition
* Web browsing capabilities
* Better execution tracing and observability
* Human approval for sensitive actions
* More sophisticated artifact generation

## Author

**Priya Saha**

B.Tech. Artificial Intelligence and Data Science
Guru Gobind Singh Indraprastha University

[GitHub](https://github.com/PriyaSaha1234)
[Portfolio](https://priyasahaportfolio.vercel.app/)
