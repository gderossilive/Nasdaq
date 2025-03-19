# Nasdaq Stock Assistant

## Overview
This application provides an AI-powered assistant that can help users get information or news about Nasdaq stocks. It utilizes Azure AI Projects with a custom agent backed by a large language model, and exposes functionality through a ChainLit web interface.

## Architecture
The application follows a client-server architecture where:
- **Server-side**: Python application using Azure AI Projects API
- **Client-side**: ChainLit web interface for user interaction
- **Agent**: AI agent that processes user queries and executes functions
- **Functions**: Custom functions that provide stock information and data

## Components

### Core Components
- **AppState**: Singleton class that manages the application state
- **Azure AI Projects Client**: Communicates with Azure AI services
- **Agent**: Processes user queries and decides which functions to call
- **Thread**: Represents a conversation session with the user
- **Function Tools**: Custom functions that the agent can call to retrieve data

### Key Files
- **async-app.py**: Main application file containing core logic
- **user_async_functions.py**: Contains custom functions for the agent to use
- **requirements.txt**: Lists all dependencies needed

## Technical Details

### AppState Singleton
The application uses a singleton pattern to ensure there's only one instance of the application state. This helps maintain consistency across different parts of the application and different user sessions.

### Agent Management
The application creates a single Azure AI agent and reuses it across all sessions:
- A global variable `GLOBAL_AGENT_ID` stores the agent ID
- The agent is created only once when the server starts
- Each new session checks if an agent already exists before creating one

### Session Management
Each user gets their own conversation thread:
- When a new chat session starts, a new thread is created
- Messages are associated with specific threads
- Each thread has its own conversation history

### Asynchronous Execution
The application uses asynchronous programming for better performance:
- Async/await pattern for API calls
- Non-blocking I/O operations
- AsyncIO for managing concurrent operations

### Lifecycle Events
The application responds to several lifecycle events:
- **@cl.on_chat_start**: When a new chat session begins
- **@cl.on_chat_end**: When a chat session ends
- **@cl.on_message**: When a user sends a message

### Resource Cleanup
The application implements proper resource management:
- Session resources are cleaned up when a chat ends
- Agent is deleted when the server shuts down
- Client connections are properly closed

## Setup and Configuration

### Prerequisites
- Python 3.8 or newer
- Azure account with AI Projects set up
- Required environment variables:
  - `PROJECT_CONNECTION_STRING`: Azure AI Project connection string
  - `MODEL_DEPLOYMENT_NAME`: Name of the AI model deployment

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set required environment variables
4. Run the application: `python async-app.py`

### Environment Variables
- **PROJECT_CONNECTION_STRING**: Connection string for the Azure AI Project
- **MODEL_DEPLOYMENT_NAME**: The deployed model to use for the agent

## Usage
1. Start the application
2. Open the ChainLit web interface (default: http://localhost:8000)
3. Type queries about Nasdaq stocks
4. The agent will respond with relevant information

## Error Handling
The application implements comprehensive error handling:
- Graceful handling of API failures
- Session cleanup even after errors
- Proper logging of all operations and errors
- Exception handling during function execution

## Logging
The application uses Python's logging module to track operations:
- INFO level for standard operations
- WARNING and ERROR levels for issues
- Timestamps for all log entries

### Log Files
- Log files are stored in the `./log` directory
- Each run of the application creates a new log file with a timestamp
- Old log files are automatically cleaned up (default: keeps 20 most recent files)
- Logs contain detailed information about application operations and errors

### Log Management
- The `log_utils.py` script provides utilities for log management
- You can archive logs by running `python log_utils.py`
- Log rotation is handled automatically
