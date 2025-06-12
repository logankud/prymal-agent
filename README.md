
# Prymal AI Copilot

An intelligent multi-agent system for Shopify data analysis and business intelligence, featuring Slack integration and advanced workflow management.

## Overview

This application provides a conversational AI interface for analyzing Shopify store data through a hierarchical agent architecture:

- **Manager Agent** - Orchestrates tasks and delegates to specialized agents
- **Analyst Agent** - Performs data analysis with self-validation capabilities  
- **Slack Integration** - Enables team collaboration through Slack workspace integration

## Key Features

### 🤖 Multi-Agent Architecture
- **Manager Agent**: Routes queries and coordinates analysis workflows
- **Analyst Agent**: Executes data analysis with built-in validation checks
- **Self-Validating System**: Automatically validates analysis quality and completeness

### 🛍️ Shopify Integration
- **GraphQL API Access**: Direct queries to Shopify Admin API
- **MCP (Model Context Protocol)**: Structured tool calling for Shopify operations
- **Schema Introspection**: Dynamic discovery of available Shopify data structures
- **Documentation Search**: Contextual help from Shopify docs

### 💬 Slack Workspace Integration
- **OAuth Authentication**: Secure workspace installation
- **Real-time Messaging**: Receive and respond to Slack messages
- **Team Collaboration**: Share analysis results directly in Slack channels

### 🧠 Memory & Persistence
- **Conversation Memory**: Maintains context across chat sessions
- **PostgreSQL Storage**: Persistent storage for analysis results
- **Dataset Management**: Store and retrieve analysis datasets
- **SQL Execution**: Direct database query capabilities

### 🔧 Analysis Tools
- **Data Aggregation**: Group and summarize Shopify data
- **SQL Generation**: Automatic query generation for complex analysis
- **Workflow Execution**: Structured analysis pipelines (fetch → validate → group → aggregate)
- **Model Introspection**: Dynamic schema discovery for data models

## Quick Start

### Prerequisites
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)
- Shopify Admin API access
- Slack app credentials (for Slack integration)

### Running the Agent
```bash
# Start the conversational agent
python main.py

# Or run Slack OAuth server
python oauth_slack.py

# Run evaluations
python evaluate.py
```

### Available Workflows
- **Run Agent**: Interactive chat interface with the manager agent
- **Run OAuth Slackbot**: Slack workspace integration server
- **Run Phoenix + Evaluation**: Agent performance evaluation

## Architecture

```
User Query → Manager Agent → Analyst Agent → Shopify Tools → Analysis Results
                ↓
          Memory Storage ← Validation Checks ← Self-Validation
```

### Agent Hierarchy
1. **Manager Agent**: Interprets user queries and delegates to appropriate agents
2. **Analyst Agent**: Executes analysis with access to Shopify tools and data
3. **Validation Layer**: Ensures analysis quality before returning results

### Tool Ecosystem
- `run_shopify_query`: Execute GraphQL queries against Shopify API
- `search_shopify_docs`: Find relevant documentation
- `introspect_shopify_schema`: Discover available data structures
- `execute_sql`: Run SQL queries on stored data
- `group_by_and_agg_data`: Perform data aggregations
- `store_dataset`: Persist analysis results

## Configuration

The system supports multiple model backends:
- **OpenAI GPT-4** (default)
- **HuggingFace Models** (DeepSeek-R1, etc.)
- **Inference Client Models**

Switch models by modifying the `MODEL` configuration in `agent.py`.

## Use Cases

- **Sales Analysis**: Revenue trends, top products, customer segments
- **Inventory Management**: Stock levels, reorder points, product performance
- **Customer Analytics**: Purchase patterns, lifetime value, retention metrics
- **Performance Monitoring**: Store metrics, conversion rates, growth analysis
- **Team Collaboration**: Share insights and reports via Slack integration

## File Structure

- `main.py` - Main agent orchestration and chat interface
- `oauth_slack.py` - Slack OAuth and messaging server
- `tools/` - Shopify integration and analysis tools
- `prompts/` - Agent system prompts and templates
- `models/` - Data models and schemas
- `memory_utils.py` - Conversation and data persistence
- `workflows/` - Structured analysis pipelines
