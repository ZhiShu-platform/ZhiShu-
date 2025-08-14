# Langfuse Integration Guide

This document explains how to use Langfuse integration in the Emergency Management System.

## Overview

Langfuse is an open-source LLM observability platform that provides:
- **Tracing**: Track LLM calls and application logic
- **Prompt Management**: Centralized prompt versioning and management
- **Evaluations**: Score and evaluate LLM outputs
- **Monitoring**: Real-time insights into AI application performance

## Setup

### 1. Environment Variables

Create a `.env` file with your Langfuse credentials:

```bash
# Langfuse Configuration
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_HOST=https://cloud.langfuse.com  # or your self-hosted instance
```

### 2. Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Langfuse Account Setup

1. Go to [Langfuse Cloud](https://cloud.langfuse.com) or [self-host](https://langfuse.com/self-hosting)
2. Create a new project
3. Generate API keys in project settings
4. Copy the keys to your `.env` file

## Usage

### Basic Tracing

```python
from src.core.langfuse_integration import langfuse_manager

# Create a trace for a session
trace = langfuse_manager.create_trace(
    name="emergency_management_workflow",
    session_id="session_123",
    user_id="user_456"
)

# Log workflow steps
langfuse_manager.log_span(
    trace_id=trace.id,
    name="threat_detection",
    input={"user_input": "flood warning"},
    output={"threats": ["flood"], "confidence": 0.8}
)

# Log LLM generations
langfuse_manager.log_generation(
    trace_id=trace.id,
    name="risk_assessment",
    model="gpt-4",
    prompt="Assess flood risk",
    completion="High risk due to heavy rainfall"
)

# Flush events
langfuse_manager.flush()
```

### LangChain Integration

```python
from src.core.langfuse_integration import get_langfuse_handler

# Get the callback handler
handler = get_langfuse_handler()

# Use with LangChain
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler

llm = ChatOpenAI(
    callbacks=[handler],  # Langfuse will automatically trace all calls
    temperature=0.7
)
```

### Workflow Tracing

```python
from src.core.langfuse_integration import langfuse_manager

async def emergency_workflow(input_data):
    # Create trace
    trace = langfuse_manager.create_trace(
        name="emergency_response",
        session_id=input_data.get("session_id"),
        user_id=input_data.get("user_id")
    )
    
    try:
        # Step 1: Input processing
        langfuse_manager.log_span(
            trace_id=trace.id,
            name="input_processing",
            input=input_data,
            output={"processed": True}
        )
        
        # Step 2: Threat detection
        langfuse_manager.log_span(
            trace_id=trace.id,
            name="threat_detection",
            input={"processed_input": input_data},
            output={"threats": ["flood"], "level": "high"}
        )
        
        # Step 3: Response generation
        langfuse_manager.log_generation(
            trace_id=trace.id,
            name="response_generation",
            model="gpt-4",
            prompt="Generate emergency response",
            completion="Activate flood response protocols"
        )
        
        return {"status": "success"}
        
    except Exception as e:
        # Log error
        langfuse_manager.log_span(
            trace_id=trace.id,
            name="error",
            input={"error": str(e)},
            metadata={"error": True}
        )
        raise
    finally:
        # Always flush events
        langfuse_manager.flush()
```

## Features

### 1. Automatic Tracing
- All LangChain operations are automatically traced
- MCP calls are logged with detailed metadata
- Workflow steps are tracked with input/output states

### 2. Session Management
- Each user session gets a unique trace
- User interactions are grouped by session
- Cross-session analytics are available

### 3. Performance Monitoring
- Track response times for each step
- Monitor MCP call success rates
- Identify bottlenecks in workflows

### 4. Error Tracking
- Automatic error logging
- Stack traces and error context
- Error rate monitoring

## Dashboard Features

Once integrated, you can view in Langfuse:

1. **Traces**: Complete workflow executions
2. **Generations**: LLM calls and responses
3. **Scores**: Evaluation metrics
4. **Analytics**: Performance insights
5. **Prompts**: Version-controlled prompt management

## Best Practices

1. **Always flush**: Call `langfuse_manager.flush()` after completing operations
2. **Use meaningful names**: Give traces and spans descriptive names
3. **Include metadata**: Add relevant context to traces
4. **Handle errors**: Log errors with appropriate metadata
5. **Monitor performance**: Use spans to track timing

## Troubleshooting

### Common Issues

1. **Authentication failed**: Check your API keys and host URL
2. **Events not appearing**: Ensure you're calling `flush()`
3. **Import errors**: Verify Langfuse is installed correctly

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("langfuse").setLevel(logging.DEBUG)
```

## API Reference

### LangfuseManager Methods

- `create_trace(name, session_id, user_id, metadata)`: Create new trace
- `log_span(trace_id, name, input, output, metadata)`: Log workflow step
- `log_generation(trace_id, name, model, prompt, completion, metadata)`: Log LLM call
- `log_score(trace_id, name, value, comment)`: Log evaluation score
- `flush()`: Send events to Langfuse
- `shutdown()`: Clean shutdown

### Environment Variables

- `LANGFUSE_SECRET_KEY`: Your secret API key
- `LANGFUSE_PUBLIC_KEY`: Your public API key  
- `LANGFUSE_HOST`: Langfuse instance URL

## Examples

See the following files for complete examples:
- `src/main.py`: Main API with Langfuse integration
- `src/agent/graph.py`: LangGraph workflow with tracing
- `src/MCP/servers/`: MCP servers with call logging
