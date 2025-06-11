# RAG Application with Azure OpenAI and Azure AI Search

This project implements a Retrieval Augmented Generation (RAG) application using Azure OpenAI and Azure AI Search. It includes authentication, LangGraph and LangChain for creating agent tools, and Application Insights for monitoring.

## Features

- Azure OpenAI integration for LLM capabilities
- Azure AI Search for document retrieval
- FastAPI backend with authentication
- Agent-based architecture using LangGraph
- Application Insights monitoring
- Virtual environment setup

## Project Structure

```
rag-azure-app/
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── app/                     # Main application package
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration settings
│   ├── auth/                # Authentication module
│   ├── api/                 # API routes
│   ├── core/                # Core functionality
│   ├── agents/              # Agent tools and graph
│   ├── schemas/             # Pydantic models
│   └── services/            # Services like telemetry
└── scripts/                 # Utility scripts
```

## Setup

1. Clone the repository
2. Run the setup script to create a virtual environment and install dependencies:

```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

3. Update the `.env` file with your Azure credentials
4. Start the application:

```bash
python run.py
```

## Azure Resources Required

- Azure OpenAI service with a deployment
- Azure AI Search service with an index
- Azure Blob Storage (for document processing)
- Azure Form Recognizer (for document processing)
- Application Insights

## API Endpoints

- `/api/chat/completions` - Generate chat completions with RAG
- `/api/search` - Search documents using Azure AI Search
- `/token` - Get an authentication token
- `/health` - Health check endpoint

## Authentication

The application uses JWT authentication. To get a token:

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
```

Use the token in subsequent requests:

```bash
curl -X POST "http://localhost:8000/api/chat/completions" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "What is RAG?"}], "use_retrieval": true}'
```

## Development

To run the application in development mode:

```bash
uvicorn app.main:app --reload
```

This will start the FastAPI application with hot reloading.