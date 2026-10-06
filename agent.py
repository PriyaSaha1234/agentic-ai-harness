import os
import asyncio
from contextlib import AsyncExitStack

from google import genai
from google.genai import types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tools import tools_registry
from planner import planner


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


# ============================================================
# AGENT
# ============================================================

class Agent:

    def __init__(self):

        self.history = []

        self.mcp_session = None

        self.exit_stack = AsyncExitStack()

        self.mcp_tools = {}

        self.gemini_tools = []

        # Track repeated tool failures.
        self.tool_attempts = {}

        # Maximum attempts for the exact same
        # tool + arguments combination.
        self.MAX_TOOL_ATTEMPTS = 3


    # ========================================================
    # MCP CONNECTION
    # ========================================================

    async def connect_mcp(self):

        server_params = StdioServerParameters(
            command="python",
            args=["mcp/server.py"],
        )

        stdio_transport = (
            await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
        )

        self.stdio, self.write = stdio_transport

        self.mcp_session = (
            await self.exit_stack.enter_async_context(
                ClientSession(
                    self.stdio,
                    self.write,
                )
            )
        )

        await self.mcp_session.initialize()

        response = (
            await self.mcp_session.list_tools()
        )

        print(
            "\n[MCP] Connected successfully."
        )

        print(
            "[MCP] Available tools:"
        )

        for tool in response.tools:

            print(
                f"  - {tool.name}"
            )

            self.mcp_tools[
                tool.name
            ] = tool

            schema = tool.input_schema

            properties = {}

            for name, value in schema.get(
                "properties",
                {}
            ).items():

                properties[name] = types.Schema(
                    type=value.get(
                        "type",
                        "STRING",
                    ).upper(),

                    description=value.get(
                        "description",
                        "",
                    ),
                )

            self.gemini_tools.append(
                types.FunctionDeclaration(

                    name=tool.name,

                    description=(
                        tool.description or ""
                    ),

                    parameters=types.Schema(

                        type="OBJECT",

                        properties=properties,

                        required=schema.get(
                            "required",
                            [],
                        ),
                    )
                )
            )


    # ========================================================
    # TOOL DEFINITIONS
    # ========================================================

    def get_gemini_tools(self):

        local_tools = [

            # ------------------------------------------------
            # CALCULATOR
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="calculator",

                description=(
                    "Safely calculate a "
                    "mathematical expression."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "expression": types.Schema(

                            type="STRING",

                            description=(
                                "Mathematical expression "
                                "to calculate."
                            ),
                        )
                    },

                    required=[
                        "expression"
                    ],
                ),
            ),

            # ------------------------------------------------
            # READ FILE
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="read_file",

                description=(
                    "Read a text file from "
                    "the workspace folder."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "filename": types.Schema(

                            type="STRING",

                            description=(
                                "Filename inside "
                                "the workspace folder."
                            ),
                        )
                    },

                    required=[
                        "filename"
                    ],
                ),
            ),

            # ------------------------------------------------
            # WRITE FILE
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="write_file",

                description=(
                    "Create or overwrite a text file "
                    "inside the workspace. Use this to "
                    "save reports, summaries, analysis, "
                    "plans, and other generated artifacts."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "filename": types.Schema(

                            type="STRING",

                            description=(
                                "Filename to create "
                                "inside the workspace."
                            ),
                        ),

                        "content": types.Schema(

                            type="STRING",

                            description=(
                                "Complete content to "
                                "write into the file."
                            ),
                        ),
                    },

                    required=[
                        "filename",
                        "content",
                    ],
                ),
            ),

            # ------------------------------------------------
            # SAVE MEMORY
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="save_memory",

                description=(
                    "Save important information "
                    "for future conversations."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "memory": types.Schema(

                            type="STRING",

                            description=(
                                "Information that "
                                "should be remembered."
                            ),
                        )
                    },

                    required=[
                        "memory"
                    ],
                ),
            ),

            # ------------------------------------------------
            # GET MEMORY
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="get_memory",

                description=(
                    "Retrieve persistent memory "
                    "from previous conversations."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={},
                ),
            ),

            # ------------------------------------------------
            # CREATE PLAN
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="create_plan",

                description=(
                    "Create an execution plan "
                    "for a complex task."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "task": types.Schema(

                            type="STRING",

                            description=(
                                "The overall task."
                            ),
                        ),

                        "steps": types.Schema(

                            type="STRING",

                            description=(
                                "One execution "
                                "step per line."
                            ),
                        ),
                    },

                    required=[
                        "task",
                        "steps",
                    ],
                ),
            ),

            # ------------------------------------------------
            # COMPLETE PLAN STEP
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="complete_plan_step",

                description=(
                    "Mark a step in the current "
                    "plan as completed."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={

                        "step_number": types.Schema(

                            type="INTEGER",

                            description=(
                                "Completed step number."
                            ),
                        )
                    },

                    required=[
                        "step_number"
                    ],
                ),
            ),

            # ------------------------------------------------
            # PLAN STATUS
            # ------------------------------------------------

            types.FunctionDeclaration(

                name="get_plan_status",

                description=(
                    "Get the current execution "
                    "plan and status."
                ),

                parameters=types.Schema(

                    type="OBJECT",

                    properties={},
                ),
            ),
        ]

        return types.Tool(

            function_declarations=(
                local_tools
                + self.gemini_tools
            )
        )


    # ========================================================
    # TOOL EXECUTION
    # ========================================================

    async def execute_tool(
        self,
        name,
        arguments,
    ):
        """
        Execute a tool with controlled retry tracking.

        The same tool with the same arguments can only
        fail three times before the harness stops
        allowing that exact operation.
        """

        # ----------------------------------------------------
        # CREATE UNIQUE ATTEMPT KEY
        # ----------------------------------------------------

        try:

            attempt_key = (
                name,
                tuple(
                    sorted(
                        (
                            str(key),
                            str(value)
                        )
                        for key, value
                        in arguments.items()
                    )
                ),
            )

        except Exception:

            attempt_key = (
                name,
                str(arguments),
            )


        # ----------------------------------------------------
        # CHECK PREVIOUS ATTEMPTS
        # ----------------------------------------------------

        attempts = self.tool_attempts.get(
            attempt_key,
            0,
        )

        if attempts >= self.MAX_TOOL_ATTEMPTS:

            print(
                f"[Recovery] Maximum attempts "
                f"reached for {name}."
            )

            return (
                f"Tool '{name}' has failed "
                f"{self.MAX_TOOL_ATTEMPTS} times "
                f"with the same arguments. "
                f"Do not retry this exact operation. "
                f"Try a different approach."
            )


        # Record this attempt.
        self.tool_attempts[
            attempt_key
        ] = attempts + 1


        # ----------------------------------------------------
        # PLANNER TOOLS
        # ----------------------------------------------------

        if name == "create_plan":

            result = planner.create_plan(
                task=arguments["task"],
                steps=arguments["steps"],
            )

            self.tool_attempts.pop(
                attempt_key,
                None,
            )

            return result


        if name == "complete_plan_step":

            result = planner.complete_step(
                step_number=int(
                    arguments["step_number"]
                )
            )

            self.tool_attempts.pop(
                attempt_key,
                None,
            )

            return result


        if name == "get_plan_status":

            result = planner.get_status()

            self.tool_attempts.pop(
                attempt_key,
                None,
            )

            return result


        # ----------------------------------------------------
        # MCP TOOLS
        # ----------------------------------------------------

        if name in self.mcp_tools:

            print(
                f"[MCP] Calling tool: {name}"
            )

            try:

                result = (
                    await self.mcp_session.call_tool(
                        name,
                        arguments,
                    )
                )

                output = []

                for content in result.content:

                    if hasattr(
                        content,
                        "text",
                    ):

                        output.append(
                            content.text
                        )

                result_text = "\n".join(
                    output
                )

                # --------------------------------------------
                # DETECT MCP-LEVEL ERRORS
                # --------------------------------------------

                if not result_text.strip():

                    return (
                        "MCP tool error: "
                        "Tool returned no result."
                    )


                # Successful execution.
                self.tool_attempts.pop(
                    attempt_key,
                    None,
                )

                return result_text

            except Exception as e:

                return (
                    f"MCP tool error: {e}"
                )


        # ----------------------------------------------------
        # LOCAL TOOLS
        # ----------------------------------------------------

        tool = tools_registry.get(
            name
        )

        if tool is None:

            return (
                f"Unknown tool: {name}"
            )


        try:

            result = tool(
                **arguments
            )


            # --------------------------------------------
            # DETECT TOOL-LEVEL ERRORS
            # --------------------------------------------

            if isinstance(
                result,
                str,
            ):

                error_prefixes = (
                    "Error:",
                    "File not found:",
                    "Calculator error:",
                    "MCP tool error:",
                    "Tool execution error:",
                    "Invalid arguments",
                )

                if result.startswith(
                    error_prefixes
                ):

                    return result


            # Successful execution.
            self.tool_attempts.pop(
                attempt_key,
                None,
            )

            return result


        except TypeError as e:

            return (
                f"Invalid arguments for "
                f"{name}: {e}"
            )

        except Exception as e:

            return (
                f"Tool execution error: {e}"
            )


    # ========================================================
    # AGENT LOOP
    # ========================================================

    async def run(
        self,
        user_input,
    ):

        self.history.append(

            types.Content(

                role="user",

                parts=[
                    types.Part.from_text(
                        text=user_input
                    )
                ],
            )
        )

        tool_round = 0

        MAX_TOOL_ROUNDS = 15

        while True:

            tool_round += 1

            if tool_round > MAX_TOOL_ROUNDS:

                return (
                    "I stopped because the task "
                    "required too many tool calls."
                )


            # ------------------------------------------------
            # MODEL REQUEST
            # ------------------------------------------------

            try:

                response = (
                    client.models.generate_content(

                        model=(
                            "gemini-3.5-flash-lite"
                        ),

                        contents=self.history,

                        config=(
                            types.GenerateContentConfig(

                                tools=[
                                    self.get_gemini_tools()
                                ],

                                system_instruction=(

                                    "You are an autonomous "
                                    "agentic AI assistant.\n\n"

                                    "You have access to "
                                    "local tools and MCP tools.\n\n"

                                    "PLANNING:\n"

                                    "For complex tasks "
                                    "requiring multiple "
                                    "actions, first use "
                                    "create_plan.\n\n"

                                    "Break complex tasks "
                                    "into clear ordered "
                                    "steps.\n\n"

                                    "After completing a "
                                    "planned step, use "
                                    "complete_plan_step.\n\n"

                                    "Use get_plan_status "
                                    "when needed.\n\n"

                                    "Do not create a plan "
                                    "for simple requests.\n\n"

                                    "FILE ACCESS:\n"

                                    "Use read_file when "
                                    "information is inside "
                                    "a workspace file.\n\n"

                                    "Use write_file when "
                                    "you need to create a "
                                    "report, summary, "
                                    "analysis, plan, or "
                                    "other artifact inside "
                                    "the workspace.\n\n"

                                    "Only create or modify "
                                    "files inside the "
                                    "workspace.\n\n"

                                    "CALCULATIONS:\n"

                                    "Use calculator for "
                                    "mathematical operations.\n\n"

                                    "MEMORY:\n"

                                    "Use get_memory when "
                                    "previous information "
                                    "may be relevant.\n\n"

                                    "Use save_memory when "
                                    "the user explicitly "
                                    "asks you to remember "
                                    "something.\n\n"

                                    "MCP:\n"

                                    "Use MCP tools when "
                                    "workspace information "
                                    "requires them.\n\n"

                                    "FAILURE RECOVERY:\n"

                                    "If a tool returns an "
                                    "error or fails, do not "
                                    "immediately give up.\n\n"

                                    "Analyze the error and "
                                    "determine whether another "
                                    "tool or a different "
                                    "approach can solve the "
                                    "problem.\n\n"

                                    "For example, if a file "
                                    "does not exist, use "
                                    "list_workspace_files "
                                    "to discover available "
                                    "files before trying "
                                    "again.\n\n"

                                    "Never repeatedly execute "
                                    "the same failed tool "
                                    "with identical "
                                    "arguments.\n\n"

                                    "The harness limits "
                                    "repeated failed "
                                    "operations to three "
                                    "attempts.\n\n"

                                    "If an operation has "
                                    "reached its retry limit, "
                                    "change your strategy "
                                    "instead of repeating it.\n\n"

                                    "Prefer discovering "
                                    "information with "
                                    "available tools "
                                    "rather than guessing.\n\n"

                                    "Use the information "
                                    "returned by tools to "
                                    "make the next decision.\n\n"

                                    "ARTIFACT CREATION:\n"

                                    "When the user asks you "
                                    "to analyze workspace "
                                    "information and produce "
                                    "a report or document, "
                                    "perform the analysis "
                                    "using the available "
                                    "tools and save the "
                                    "final artifact using "
                                    "write_file.\n\n"

                                    "Do not merely describe "
                                    "the artifact. Actually "
                                    "create it when requested.\n\n"

                                    "Continue using tools "
                                    "until the task is "
                                    "complete or genuinely "
                                    "cannot be completed.\n\n"

                                    "Then provide a concise "
                                    "final answer."
                                ),
                            )
                        ),
                    )
                )

            except Exception as e:

                return (
                    f"Model error: {e}"
                )


            # ------------------------------------------------
            # VALIDATE RESPONSE
            # ------------------------------------------------

            if not response.candidates:

                return (
                    "The model returned "
                    "no response."
                )

            model_content = (
                response.candidates[0].content
            )

            self.history.append(
                model_content
            )


            # ------------------------------------------------
            # FIND TOOL CALLS
            # ------------------------------------------------

            function_calls = []

            for part in model_content.parts:

                if part.function_call:

                    function_calls.append(
                        part.function_call
                    )


            # ------------------------------------------------
            # FINAL ANSWER
            # ------------------------------------------------

            if not function_calls:

                return response.text


            # ------------------------------------------------
            # EXECUTE TOOLS
            # ------------------------------------------------

            for function_call in function_calls:

                tool_name = (
                    function_call.name
                )

                tool_args = dict(
                    function_call.args
                )

                print(
                    f"\n[Agent] Using tool: "
                    f"{tool_name}"
                )

                print(
                    f"[Agent] Arguments: "
                    f"{tool_args}"
                )

                result = (
                    await self.execute_tool(
                        tool_name,
                        tool_args,
                    )
                )

                print(
                    f"[Tool] Result: "
                    f"{result}"
                )

                self.history.append(

                    types.Content(

                        role="user",

                        parts=[
                            types.Part.from_function_response(

                                name=tool_name,

                                response={
                                    "result": result
                                },
                            )
                        ],
                    )
                )


    # ========================================================
    # CLOSE MCP
    # ========================================================

    async def close(self):

        await self.exit_stack.aclose()


# ============================================================
# MAIN
# ============================================================

async def main():

    agent = Agent()

    try:

        await agent.connect_mcp()

        print(
            "\n======================================"
        )

        print(
            "       AGENTIC AI HARNESS"
        )

        print(
            "======================================"
        )

        print(
            "Gemini + Tools + MCP + Memory + Planning"
        )

        print(
            "Type 'exit' or 'quit' to stop."
        )

        print(
            "Press Ctrl+C to exit.\n"
        )

        while True:

            try:

                user_input = input("You: ")

                if user_input.strip().lower() in [
                    "exit",
                    "quit",
                ]:

                    print(
                        "\nBye!"
                    )

                    break

                if not user_input.strip():

                    continue

                answer = await agent.run(
                    user_input
                )

                print(
                    f"Agent: {answer}"
                )

            except KeyboardInterrupt:

                print(
                    "\n\nBye!"
                )

                break

            except Exception as e:

                print(
                    f"Agent error: {e}"
                )

    finally:

        await agent.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print(
            "\n\nBye!"
        )