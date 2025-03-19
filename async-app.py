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
import loggingfrom pathlib import Path

# Set up logging
logger = setup_logging(app_name="nasdaq_assistant", log_level=logging.INFO, max_logs=20)ry if it doesn't exist

# Global agent ID (module-level instead of file-based)
GLOBAL_AGENT_ID = None
estamp
# Constantse.now().strftime('%Y%m%d_%H%M%S')}.log"
POLLING_INTERVAL = 2  # Seconds between polling requestsilepath = log_dir / log_filename
MESSAGE_TIMEOUT = 60  # Maximum seconds to wait for a response
# Configure logging
class AppState:
    _instance = None
        level=logging.INFO,
    # Improved initialization'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    def init_attributes(self):
        """Initialize instance attributes only once"""
        if not hasattr(self, 'initialized'):        logging.FileHandler(log_filepath)
            self.project_client = None
            self.agent = None
            self.thread = None
            self.functions = Noneation and log file location
            self.initialized = Falseting. Logs will be saved to {log_filepath}")
            logger.debug("AppState attributes initialized")
    ile-based)
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance.init_attributes()etween polling requests
        return cls._instancends to wait for a response

app_state = AppState()s AppState:

# Create credential only once and cache it
@lru_cache(maxsize=1)
def get_credential():
    return DefaultAzureCredential()ce attributes only once"""
        if not hasattr(self, 'initialized'):
# Resource management using async context managerct_client = None
@asynccontextmanager            self.agent = None
async def get_client():
    """Context manager for creating and managing client connections"""tions = None
    credential = get_credential()ialized = False
    client = AIProjectClient.from_connection_string(attributes initialized")
        credential=credential,    
        conn_str=os.environ["PROJECT_CONNECTION_STRING"]
    )ance is None:
    try:ce = super(AppState, cls).__new__(cls)
        yield client
    finally:
        await client.close()

# Initialize the application with optimized client creation
async def initialize() -> None:ate credential only once and cache it
    global GLOBAL_AGENT_IDhe(maxsize=1)
    :
    if app_state.initialized:efaultAzureCredential()
        logger.debug("Session already initialized, skipping...")
        return# Resource management using async context manager
    
    try:
        # Create client connection creating and managing client connections"""
        app_state.project_client = AIProjectClient.from_connection_string(credential = get_credential()
            credential=get_credential(),from_connection_string(
            conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )tr=os.environ["PROJECT_CONNECTION_STRING"]
        )
        # Initialize function tools - do this once and cache
        app_state.functions = AsyncFunctionTool(functions=user_async_functions)
        
        # Use existing agent if available, otherwise create new one
        if GLOBAL_AGENT_ID:
            try:ize the application with optimized client creation
                app_state.agent = await app_state.project_client.agents.get_agent(GLOBAL_AGENT_ID)f initialize() -> None:
                logger.info(f"Using existing agent with ID: {GLOBAL_AGENT_ID}")
            except Exception as e:
                logger.warning(f"Failed to get existing agent: {e}. Will create new one.")pp_state.initialized:
                GLOBAL_AGENT_ID = None
        
        # Create agent if needed
        if not GLOBAL_AGENT_ID:
            app_state.agent = await app_state.project_client.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"], AIProjectClient.from_connection_string(
                name="Nasdaq Stock Assistant",
                instructions="You support people to get information or news about Nasdaq Stocks.",CT_CONNECTION_STRING"]
                tools=app_state.functions.definitions,)
            )
            GLOBAL_AGENT_ID = app_state.agent.idools - do this once and cache
            logger.info(f"Created new agent, agent ID: {GLOBAL_AGENT_ID}")

        # Create a new thread for this sessionerwise create new one
        app_state.thread = await app_state.project_client.agents.create_thread()
        logger.info(f"Created thread, ID: {app_state.thread.id}")
           app_state.agent = await app_state.project_client.agents.get_agent(GLOBAL_AGENT_ID)
        app_state.initialized = Truent with ID: {GLOBAL_AGENT_ID}")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")                logger.warning(f"Failed to get existing agent: {e}. Will create new one.")
        # Clean up any partial resources
        await cleanup_session()
        raise
if not GLOBAL_AGENT_ID:
# Separate session cleanup from agent cleanupapp_state.project_client.agents.create_agent(
async def cleanup_session():nviron["MODEL_DEPLOYMENT_NAME"],
    if app_state.initialized:
        if app_state.project_client:t people to get information or news about Nasdaq Stocks.",
            try:.functions.definitions,
                await app_state.project_client.close()
                logger.info("Closed project client for session")            GLOBAL_AGENT_ID = app_state.agent.id
            except Exception as e:agent ID: {GLOBAL_AGENT_ID}")
                logger.error(f"Error during session cleanup: {e}")
        app_state.initialized = False for this session
_state.project_client.agents.create_thread()
# Complete server shutdown with agent deletionnfo(f"Created thread, ID: {app_state.thread.id}")
async def shutdown_server():
    global GLOBAL_AGENT_ID
    
    if GLOBAL_AGENT_ID:
        try:ces
            # Create a temporary client if needed        await cleanup_session()
            temp_client = None
            if not app_state.project_client:
                credential = DefaultAzureCredential() from agent cleanup
                temp_client = AIProjectClient.from_connection_string(c def cleanup_session():
                    credential=credential,lized:
                    conn_str=os.environ["PROJECT_CONNECTION_STRING"]pp_state.project_client:
                )
                client_to_use = temp_cliente.project_client.close()
            else:client for session")
                client_to_use = app_state.project_client
            
            # Delete the agent
            try:
                await client_to_use.agents.delete_agent(GLOBAL_AGENT_ID) shutdown with agent deletion
                logger.info(f"Server shutdown: Deleted agent: {GLOBAL_AGENT_ID}")
                GLOBAL_AGENT_ID = None_AGENT_ID
            except Exception as e:
                logger.error(f"Error deleting agent during shutdown: {e}")L_AGENT_ID:
            
            # Close temp client if createdeate a temporary client if needed
            if temp_client:
                await temp_client.close()
        except Exception as e:ureCredential()
            logger.error(f"Error during server shutdown: {e}")ojectClient.from_connection_string(

# Optimized message processing function        conn_str=os.environ["PROJECT_CONNECTION_STRING"]
async def process_message(message_content):
    """Process a user message and get a response from the agent"""se = temp_client
    try:
        if not app_state.initialized:= app_state.project_client
            await initialize()
                    # Delete the agent
        # Create and send message
        message = await app_state.project_client.agents.create_message(delete_agent(GLOBAL_AGENT_ID)
            thread_id=app_state.thread.id, role="user", content=message_contentBAL_AGENT_ID}")
        )        GLOBAL_AGENT_ID = None
        
        # Create and run assistant task"Error deleting agent during shutdown: {e}")
        run = await app_state.project_client.agents.create_run(    
            thread_id=app_state.thread.id, agent_id=app_state.agent.idf created
        )
        
        start_time = asyncio.get_event_loop().time()xcept Exception as e:
            logger.error(f"Error during server shutdown: {e}")
        # Improved polling loop
        while run.status in ["queued", "in_progress", "requires_action"]:
            # Check for timeout
            current_time = asyncio.get_event_loop().time()ocess a user message and get a response from the agent"""
            if current_time - start_time > MESSAGE_TIMEOUT:
                logger.warning(f"Run {run.id} timed out after {MESSAGE_TIMEOUT} seconds")
                await app_state.project_client.agents.cancel_run(    await initialize()
                    thread_id=app_state.thread.id, run_id=run.id
                )
                return "Request timed out. Please try again."te.project_client.agents.create_message(
            ntent=message_content
            # Sleep with appropriate back-off
            await asyncio.sleep(POLLING_INTERVAL)
            
            # Get updated run status
            run = await app_state.project_client.agents.get_run(d_id=app_state.thread.id, agent_id=app_state.agent.id
                thread_id=app_state.thread.id, run_id=run.id
            )
            .time()
            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                await handle_tool_calls(run, app_state.thread.id)proved polling loop
        ", "in_progress", "requires_action"]:
        # Get response when run completes
        if run.status == "completed":
            messages = await app_state.project_client.agents.list_messages(thread_id=app_state.thread.id)f current_time - start_time > MESSAGE_TIMEOUT:
            return messages['data'][0]['content'][0]['text']['value']    logger.warning(f"Run {run.id} timed out after {MESSAGE_TIMEOUT} seconds")
        else:
            logger.error(f"Run ended with unexpected status: {run.status}")
            return f"Sorry, I encountered an issue. Run status: {run.status}"        )
            . Please try again."
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        return "Sorry, I encountered an error processing your request."

# Separate function for handling tool calls
async def handle_tool_calls(run, thread_id):
    """Handle tool calls from the agent"""    thread_id=app_state.thread.id, run_id=run.id
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    if not tool_calls:
        logger.error("No tool calls provided - cancelling run")red_action, SubmitToolOutputsAction):
        await app_state.project_client.agents.cancel_run(                await handle_tool_calls(run, app_state.thread.id)
            thread_id=thread_id, run_id=run.id
        )
        return
essages(thread_id=app_state.thread.id)
    tool_outputs = []sages['data'][0]['content'][0]['text']['value']
    for tool_call in tool_calls:
        if isinstance(tool_call, RequiredFunctionToolCall):us: {run.status}")
            try:ssue. Run status: {run.status}"
                output = await app_state.functions.execute(tool_call)   
                if output:eption as e:
                    tool_outputs.append(        logger.exception(f"Error processing message: {e}")
                        ToolOutput(, I encountered an error processing your request."
                            tool_call_id=tool_call.id,
                            output=output,
                        )_tool_calls(run, thread_id):
                    )
            except Exception as e:red_action.submit_tool_outputs.tool_calls
                logger.error(f"Error executing tool_call {tool_call.id}: {e}")
 provided - cancelling run")
    if tool_outputs:un(
        await app_state.project_client.agents.submit_tool_outputs_to_run(n.id
            thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
        )

@cl.on_chat_start
async def on_chat_start() -> None:    for tool_call in tool_calls:
    logger.info("A new chat session has started!")e(tool_call, RequiredFunctionToolCall):
    await initialize()
    await cl.Message(content="Welcome to the Nasdaq Stock Assistant! How can I help you?").send()
       if output:
@cl.on_chat_end                    tool_outputs.append(
async def on_chat_end():       ToolOutput(
    logger.info("Chat session ended")all_id=tool_call.id,
    await cleanup_session()
  )
@cl.on_message
async def main(message: cl.Message):            except Exception as e:
    logger.info(f"User input: {message.content}") logger.error(f"Error executing tool_call {tool_call.id}: {e}")
    
    # Send thinking indicator
    thinking_msg = cl.Message(content="")ject_client.agents.submit_tool_outputs_to_run(
    await thinking_msg.send()            thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
    
    # Process the message
    response = await process_message(message.content)
    c def on_chat_start() -> None:
    # Update with the actual responseession has started!")
    await thinking_msg.update(content=response)
    logger.info("Response sent to user")"Welcome to the Nasdaq Stock Assistant! How can I help you?").send()

if __name__ == "__main__":
    logger.info("Starting server...")
    import atexitlogger.info("Chat session ended")
    
    # Register shutdown function to run at server exit
    def sync_shutdown():
        asyncio.run(shutdown_server())async def main(message: cl.Message):
    ut: {message.content}")
    atexit.register(sync_shutdown)
    ng indicator
    try:thinking_msg = cl.Message(content="")
        # Initialize server-wide components
        cl.run()
    except Exception as e:
        logger.error(f"Error running server: {e}")response = await process_message(message.content)
    finally:
        logger.info("Server shutting down...")    # Register shutdown function to run at server exit
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