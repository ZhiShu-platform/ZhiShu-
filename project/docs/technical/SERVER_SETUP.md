# Emergency Management System - Server Setup Guide

This guide provides multiple ways to start the Emergency Management System server.

## Quick Start

### Option 1: LangGraph Dev Mode (Recommended)

```bash
# Using LangGraph CLI (recommended for development)
langgraph dev

# Or using the startup script
python start_server.py

# Or using Make
make serve
```

**Features:**
- 🌐 Server: http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
- 🎨 LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 🔄 Auto-reload on code changes
- 🛠️ Full LangGraph integration

### Option 2: Direct FastAPI Mode

```bash
# Using direct execution
python src/main.py

# Or using the startup script
python start_server.py --mode direct

# Or using Make
make serve_direct
```

**Features:**
- 🌐 Server: http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
- 🔄 Auto-reload on code changes
- ⚠️ No LangGraph Studio UI

### Option 3: Production Mode

```bash
# Using the startup script
python start_server.py --mode production

# Or using Make
make serve_prod
```

**Requirements:** `pip install gunicorn`

## Windows Users

Use the provided batch script:

```cmd
# Default (LangGraph dev mode)
start_server.bat

# Direct FastAPI mode
start_server.bat direct
```

## Prerequisites

### Required Dependencies

```bash
pip install -e . "langgraph-cli[inmem]"
```

### Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Configure your API keys in `.env`:
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   LANGFUSE_SECRET_KEY=your_key_here
   LANGFUSE_PUBLIC_KEY=your_key_here
   ```

## API Endpoints

Once the server starts, the following endpoints are available:

### Core Endpoints

- **`GET /`** - Root endpoint with system information
- **`GET /system_health`** - System health check
- **`POST /process_emergency_event`** - Process emergency events
- **`GET /docs`** - Interactive API documentation

### Request Format

For emergency processing, send a POST request to `/process_emergency_event`:

```json
{
  "input_data": {
    "user_question": "What should I do in case of a wildfire?",
    "region": "California",
    "emergency_type": "wildfire",
    "severity_level": "medium",
    "timestamp": "2024-01-15T10:30:00Z",
    "model_info": {
      "name": "emergency_model",
      "type": "disaster_analysis"
    },
    "datasets": [
      {"name": "fire_risk_data", "source": "NFDRS"}
    ]
  }
}
```

### Response Format

The server returns a comprehensive report:

```json
{
  "final_report": {
    "processing_log": [...],
    "alerts": [...],
    "recommendations": [...],
    "coordination_results": {...},
    "damage_assessment": {...},
    "summary": "..."
  }
}
```

## Testing the Server

Run the test suite to verify server functionality:

```bash
# Start the server first (in another terminal)
langgraph dev

# Then run tests
python test_server.py
```

## Integration with Frontend

The server is designed to work with the Node.js proxy and Vue.js frontend:

1. **Vue.js Frontend** (port 10.0.3.4) → **Node.js Backend** (port 3000) → **LangGraph Server** (port 2024)

2. Node.js backend proxies requests from `/api/chat` to LangGraph's `/process_emergency_event`

3. Health checks are available via Node.js `/api/langgraph/health` endpoint

## Troubleshooting

### Common Issues

1. **Port 2024 already in use:**
   ```bash
   # Find process using port 2024
   netstat -ano | findstr :2024  # Windows
   lsof -i :2024                 # Linux/Mac
   
   # Kill the process if needed
   taskkill /PID <PID> /F        # Windows
   kill -9 <PID>                 # Linux/Mac
   ```

2. **LangGraph CLI not found:**
   ```bash
   pip install "langgraph-cli[inmem]"
   ```

3. **Import errors:**
   ```bash
   pip install -e .
   ```

4. **Environment variables not loaded:**
   - Ensure `.env` file exists in project root
   - Check `.env` file contains required API keys

### Debug Mode

For detailed logging, set environment variables:

```bash
export LANGFUSE_TRACING=true
export LOG_LEVEL=DEBUG
langgraph dev
```

## Development Workflow

1. **Make code changes** in `src/` directory
2. **Server auto-reloads** (in dev mode)
3. **Test changes** using LangGraph Studio or API calls
4. **Run tests** with `python test_server.py`
5. **Format code** with `make format`
6. **Run lints** with `make lint`

## Architecture Overview

```
Frontend (Vue.js) → Node.js Proxy → LangGraph Server
                                   ↓
                              Multi-Agent Graph
                                   ↓
                           Emergency Processing Pipeline
```

The server orchestrates a multi-agent emergency management system that processes disaster events through coordinated workflows involving threat detection, alert generation, agent coordination, response execution, damage assessment, and comprehensive reporting.