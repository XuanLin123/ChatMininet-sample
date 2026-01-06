import asyncio, os, requests
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from contextlib import AsyncExitStack

# Load environment variables from .env file
load_dotenv('/home/user/Desktop/ChatMininet_sample/MCPserver/adk_agent/.env')

# --- Step 1: Import Tools from MCP Server ---
async def get_tools_async(exit_stack: AsyncExitStack):
    print("Try to Connect MCP Filesystem server...")

    net_tools, net_exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="uv",
            args=["run", "/home/user/Desktop/ChatMininet_sample/MCPserver/Server/Network_server.py"]
        )
    )
    await exit_stack.enter_async_context(net_exit_stack)


    time_tools, time_exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="uv",
            args=["run", "/home/user/Desktop/ChatMininet_sample/MCPserver/Server/Time_server.py"]
        )
    )
    await exit_stack.enter_async_context(time_exit_stack)

    print("MCP Toolset Successfully Established.")
    return  net_tools + time_tools


# --- Step 2: Agent Define ---
async def get_agent_async(exit_stack: AsyncExitStack):
    tools = await get_tools_async(exit_stack)
    print(f"From MCP Server get {len(tools)} tools.")
    root_agent = LlmAgent(
        model='gemini-2.5-flash-lite',
        name='filesystem_assistant',
        instruction=(
            "You are a network assistant. "
            "Use the available tools to solve the user's problem step by step."
        ),  
        tools=tools,
    )
    return root_agent

# --- Step 3: Main Execution Logic ---
async def async_main():
    session_service = InMemorySessionService()
    artifacts_service = InMemoryArtifactService()

    async with AsyncExitStack() as exit_stack:
        root_agent = await get_agent_async(exit_stack)

        runner = Runner(
            app_name='mcp_filesystem_app',
            agent=root_agent,
            artifact_service=artifacts_service,
            session_service=session_service,
        )

        session = session_service.create_session(
            state={}, app_name='mcp_filesystem_app', user_id='user_fs'
        )
   
        print("Running agent...")
        
        while True:
            query = input("User: ")
            if query.lower() in ["q", "exit", "bye"]:
                break

            content = types.Content(role='user', parts=[types.Part(text=query)])

            events_async = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )

            try:
                async for event in events_async:
                    print("=" * 30)
                    
                    if event.content is None:
                        print("[WARNING] Event content is None. Skipping.")
                        print("[RAW EVENT]", event)
                        continue
                        
                    role = event.content.role
                    print(f"Event Role: {role}")

                    part = event.content.parts[0]
                    
                    if part.function_response:
                        print("[TOOL RETURN] =>", part.function_response.response)
                    elif part.text:
                        print("[TEXT] =>", part.text)
                    # else:
                    #     print("[RAW EVENT]", event)

            except Exception as e:
                import traceback
                print("[ERROR TYPE]", type(e).__name__)
                print("[ERROT MESSAGE]", e)
                traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")
