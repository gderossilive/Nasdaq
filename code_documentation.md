# Nasdaq Stock Assistant - Code Documentation

## Main Application (async-app.py)

### Imports
The application uses several key libraries:
- **asyncio**: For asynchronous programming
- **chainlit**: For the web interface
- **azure.ai.projects.aio**: Azure AI Projects asynchronous client
- **azure.identity.aio**: Azure authentication

### Global Variables
- **GLOBAL_AGENT_ID**: Stores the agent ID to reuse across sessions
- **logger**: Configured logger for application-wide logging

### AppState Class
```python
class AppState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            # Initialize instance attributes
        return cls._instance
```

A singleton class that maintains the application state. Key attributes:
- **project_client**: Connection to Azure AI Projects
- **agent**: Reference to the AI agent
- **thread**: Current conversation thread
- **functions**: Available function tools
- **initialized**: Flag indicating if the state is initialized

### Key Functions

#### initialize()
```python
async def initialize() -> None:
    # Initialize the application components
```

- Creates client connection to Azure AI Projects
- Initializes function tools
- Retrieves existing agent or creates a new one
- Creates a new thread for the session

#### cleanup_session()
```python
async def cleanup_session():
    # Clean up session resources
```

- Closes the project client
- Marks the state as uninitialized

#### shutdown_server()
```python
async def shutdown_server():
    # Clean up server resources
```

- Deletes the agent when server shuts down
- Creates a temporary client if needed

### ChainLit Event Handlers

#### on_chat_start()
```python
@cl.on_chat_start
async def on_chat_start() -> None:
    # Handle new chat session
```

- Called when a new chat session starts
- Initializes the application state

#### on_chat_end()
```python
@cl.on_chat_end
async def on_chat_end():
    # Handle chat session end
```

- Called when a chat session ends
- Cleans up session resources

#### main() (on_message handler)
```python
@cl.on_message
async def main(message: cl.Message):
    # Process user message
```

- Receives user message
- Sends message to the agent
- Creates and monitors the agent run
- Handles tool calls and executes functions
- Returns agent's response to the user

### Main Execution Block
```python
if __name__ == "__main__":
    # Entry point
```

- Registers the shutdown function with atexit
- Starts the ChainLit web application
- Handles exceptions and ensures cleanup

## Function Definitions (user_async_functions.py)

This file contains the custom async functions that the agent can call:

### Stock Information Functions
- Functions to retrieve stock quotes
- Functions to get company information
- Functions to get market news
- Functions to analyze stock trends

Each function follows a standard pattern:
1. Receives parameters from the agent
2. Makes external API calls or processes data
3. Returns formatted information back to the agent

## Application Flow

1. **Server Start**:
   - Application initializes
   - Singleton AppState is created
   - Server starts listening for connections

2. **New Session**:
   - User connects to ChainLit interface
   - `on_chat_start` is triggered
   - Application state is initialized
   - New thread is created for conversation

3. **User Interaction**:
   - User sends a message
   - `on_message` handler processes it
   - Message is sent to agent
   - Agent determines which functions to call
   - Functions are executed and results returned
   - Agent generates a response
   - Response is sent back to user

4. **Session End**:
   - User closes the session
   - `on_chat_end` is triggered
   - Session resources are cleaned up

5. **Server Shutdown**:
   - Server is terminated
   - Shutdown function is called via atexit
   - Agent is deleted
   - All resources are released

## Exception Handling

The application uses a comprehensive exception handling approach:
1. **Try-Except Blocks**: Around all external API calls
2. **Error Logging**: Detailed error information is logged
3. **Graceful Degradation**: Application continues functioning when possible
4. **Resource Cleanup**: Resources are cleaned up even after exceptions

## Asynchronous Patterns

The application follows best practices for async programming:
1. **Await for I/O Operations**: All I/O is non-blocking
2. **Async Context Managers**: For resource cleanup
3. **Async Sleep**: Non-blocking sleep in polling loops
4. **Task Management**: Proper management of async tasks
