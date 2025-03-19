import asyncio
import os
import chainlit as cl
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AsyncFunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
from azure.identity.aio import DefaultAzureCredential
from user_async_functions import user_async_functions
from functools import lru_cache
from contextlib import asynccontextmanager
from log_utils import setup_logging
import logging

# Set up logging
logger = setup_logging(app_name="nasdaq_assistant", log_level=logging.INFO, max_logs=20)

# Global agent ID (module-level instead of file-based)
GLOBAL_AGENT_ID = None

# Constants
POLLING_INTERVAL = 2  # Seconds between polling requests
MESSAGE_TIMEOUT = 60  # Maximum seconds to wait for a response

class AppState:
    _instance = None
    
    # Improved initialization
    def init_attributes(self):
        """Initialize instance attributes only once"""
        if not hasattr(self, 'initialized'):
            self.project_client = None
            self.agent = None
            self.thread = None
            self.functions = None
            self.initialized = False
            logger.debug("AppState attributes initialized")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance.init_attributes()
        return cls._instance

app_state = AppState()

# Create credential only once and cache it
@lru_cache(maxsize=1)
def get_credential():
    return DefaultAzureCredential()

# Resource management using async context manager
@asynccontextmanager
async def get_client():
    """Context manager for creating and managing client connections"""
    credential = get_credential()
    client = AIProjectClient.from_connection_string(
        credential=credential,
        conn_str=os.environ["PROJECT_CONNECTION_STRING"]
    )
    try:
        yield client
    finally:
        await client.close()

# Initialize the application with optimized client creation
async def initialize() -> None:
    global GLOBAL_AGENT_ID
    
    if app_state.initialized:
        logger.debug("Session already initialized, skipping...")
        return
    
    try:
        # Create client connection
        app_state.project_client = AIProjectClient.from_connection_string(
            credential=get_credential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
        
        # Initialize function tools - do this once and cache
        app_state.functions = AsyncFunctionTool(functions=user_async_functions)
        
        # Use existing agent if available, otherwise create new one
        if GLOBAL_AGENT_ID:
            try:
                app_state.agent = await app_state.project_client.agents.get_agent(GLOBAL_AGENT_ID)
                logger.info(f"Using existing agent with ID: {GLOBAL_AGENT_ID}")
            except Exception as e:
                logger.warning(f"Failed to get existing agent: {e}. Will create new one.")
                GLOBAL_AGENT_ID = None
        
        # Create agent if needed
        if not GLOBAL_AGENT_ID:
            app_state.agent = await app_state.project_client.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name="Nasdaq Stock Assistant",
                instructions="You support people to get information or news about Nasdaq Stocks.",
                tools=app_state.functions.definitions,
            )
            GLOBAL_AGENT_ID = app_state.agent.id
            logger.info(f"Created new agent, agent ID: {GLOBAL_AGENT_ID}")

        # Create a new thread for this session
        app_state.thread = await app_state.project_client.agents.create_thread()
        logger.info(f"Created thread, ID: {app_state.thread.id}")
        
        app_state.initialized = True
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        # Clean up any partial resources
        await cleanup_session()
        raise

# Separate session cleanup from agent cleanup
async def cleanup_session():
    if app_state.initialized:
        if app_state.project_client:
            try:
                await app_state.project_client.close()
                logger.info("Closed project client for session")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
        app_state.initialized = False

# Complete server shutdown with agent deletion
async def shutdown_server():
    global GLOBAL_AGENT_ID
    
    if GLOBAL_AGENT_ID:
        try:
            # Create a temporary client if needed
            temp_client = None
            if not app_state.project_client:
                credential = DefaultAzureCredential()
                temp_client = AIProjectClient.from_connection_string(
                    credential=credential,
                    conn_str=os.environ["PROJECT_CONNECTION_STRING"]
                )
                client_to_use = temp_client
            else:
                client_to_use = app_state.project_client
            
            # Delete the agent
            try:
                await client_to_use.agents.delete_agent(GLOBAL_AGENT_ID)
                logger.info(f"Server shutdown: Deleted agent: {GLOBAL_AGENT_ID}")
                GLOBAL_AGENT_ID = None
            except Exception as e:
                logger.error(f"Error deleting agent during shutdown: {e}")
            
            # Close temp client if created
            if temp_client:
                await temp_client.close()
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")

# Optimized message processing function
async def process_message(message_content):
    """Process a user message and get a response from the agent"""
    try:
        if not app_state.initialized:
            await initialize()
        
        # Create and send message
        message = await app_state.project_client.agents.create_message(
            thread_id=app_state.thread.id, role="user", content=message_content
        )
        
        # Create and run assistant task
        run = await app_state.project_client.agents.create_run(
            thread_id=app_state.thread.id, agent_id=app_state.agent.id
        )
        
        start_time = asyncio.get_event_loop().time()
        
        # Improved polling loop
        while run.status in ["queued", "in_progress", "requires_action"]:
            # Check for timeout
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > MESSAGE_TIMEOUT:
                logger.warning(f"Run {run.id} timed out after {MESSAGE_TIMEOUT} seconds")
                await app_state.project_client.agents.cancel_run(
                    thread_id=app_state.thread.id, run_id=run.id
                )
                return "Request timed out. Please try again."
            
            # Sleep with appropriate back-off
            await asyncio.sleep(POLLING_INTERVAL)
            
            # Get updated run status
            run = await app_state.project_client.agents.get_run(
                thread_id=app_state.thread.id, run_id=run.id
            )
            
            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                await handle_tool_calls(run, app_state.thread.id)
        
        # Get response when run completes
        if run.status == "completed":
            messages = await app_state.project_client.agents.list_messages(thread_id=app_state.thread.id)
            return messages['data'][0]['content'][0]['text']['value']
        else:
            logger.error(f"Run ended with unexpected status: {run.status}")
            return f"Sorry, I encountered an issue. Run status: {run.status}"
            
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        return "Sorry, I encountered an error processing your request."

# Separate function for handling tool calls
async def handle_tool_calls(run, thread_id):
    """Handle tool calls from the agent"""
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    if not tool_calls:
        logger.error("No tool calls provided - cancelling run")
        await app_state.project_client.agents.cancel_run(
            thread_id=thread_id, run_id=run.id
        )
        return

    tool_outputs = []
    for tool_call in tool_calls:
        if isinstance(tool_call, RequiredFunctionToolCall):
            try:
                output = await app_state.functions.execute(tool_call)
                if output:
                    tool_outputs.append(
                        ToolOutput(
                            tool_call_id=tool_call.id,
                            output=output,
                        )
                    )
            except Exception as e:
                logger.error(f"Error executing tool_call {tool_call.id}: {e}")

    if tool_outputs:
        await app_state.project_client.agents.submit_tool_outputs_to_run(
            thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
        )

@cl.on_chat_start
async def on_chat_start() -> None:
    logger.info("A new chat session has started!")
    await initialize()
    await cl.Message(content="Welcome to the Nasdaq Stock Assistant! How can I help you?").send()

@cl.on_chat_end
async def on_chat_end():
    logger.info("Chat session ended")
    await cleanup_session()

@cl.on_message
async def main(message: cl.Message):
    logger.info(f"User input: {message.content}")
    
    # Send thinking indicator
    thinking_msg = cl.Message(content="")
    await thinking_msg.send()
    
    # Process the message
    response = await process_message(message.content)
    
    # Update with the actual response
    await thinking_msg.update(content=response)
    logger.info("Response sent to user")

if __name__ == "__main__":
    logger.info("Starting server...")
    import atexit
    
    # Register shutdown function to run at server exit
    def sync_shutdown():
        asyncio.run(shutdown_server())
    
    atexit.register(sync_shutdown)
    
    try:
        # Initialize server-wide components
        cl.run()
    except Exception as e:
        logger.error(f"Error running server: {e}")
    finally:
        logger.info("Server shutting down...")