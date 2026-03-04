# Retail Store Assistant — RAG + MCP

An AI-powered customer support chatbot for a retail store that answers **store policy questions** and **order inquiries** using two specialized agents orchestrated by a parent routing agent.

- Blog post: [Retail Store Assistant Using RAG and MCP](https://skeralapura.github.io/2026/02/20/Retail-Store-Assistant-RAG-MCP.html)

---

## How It Works

```
User Query
    │
    ▼
Parent Agent (GPT-4.1)
    │
    ├──► RAG Agent           ──► Chroma Vector DB ──► Store FAQ answers
    │    (policies/FAQs)
    │
    └──► Sales DB Agent      ──► MCP ──► PostgreSQL ──► Order/shipping answers
         (orders/shipping)
```

The parent agent evaluates each user query and routes it to one of two tools:

- **RAG Agent** — retrieves answers from an internal help-desk knowledge base (store hours, returns, delivery policy, etc.)
- **Sales DB Agent** — queries a PostgreSQL database via MCP for order tracking and sales data

Both agents use GPT-4.1 at `temperature=0` to ensure deterministic, grounded responses.

---

## Key Features

- **No hallucinations** — RAG answers are strictly grounded in retrieved context; unanswerable questions fall back with an escalation message
- **Intelligent routing** — parent agent selects the right tool automatically based on query type
- **MCP integration** — SQL agent connects to a live PostgreSQL database using the Model Context Protocol
- **Relevance filtering** — similarity score threshold (0.25) prevents irrelevant context from being injected
- **Web chat UI** — Chainlit-powered interface for end-to-end customer interaction

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | GPT-4.1 (temperature=0) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector DB | Chroma (persistent, cosine similarity) |
| Database | PostgreSQL (AWS-hosted) |
| DB Protocol | MCP (Model Context Protocol) |
| Agent Framework | LangChain ReAct + LangGraph |
| Chat UI | Chainlit |
| Development | Jupyter Notebook |

---

## Project Structure

```
retail-store-assistant/
├── chainlit_chatbot_app.py        # Production Chainlit chat application
├── customer_chatbot.ipynb         # Step-by-step development notebook
├── retail-store-help-desk-data.md # Knowledge base (50+ Q&A pairs)
├── rag-system-prompt.txt          # System prompt for the RAG agent
├── sql-system-prompt.txt          # System prompt for the SQL agent
├── retail_vector_db_chroma/       # Persisted Chroma vector database
├── requirements.txt               # Python dependencies
├── chainlit.md                    # Chainlit welcome screen content
└── .env                           # Environment variables (not committed)
```

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- PostgreSQL database access (AWS)

### Install

```bash
uv venv .venv-cust-chat-uv
source .venv-cust-chat-uv/bin/activate
uv pip install -r requirements.txt
```

### Configure environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key

POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_DBNAME=your_db
POSTGRES_PASSWORD=your_password
```

---

## Usage

### Development (Jupyter Notebook)

Walk through the full implementation step by step:

```bash
jupyter notebook customer_chatbot.ipynb
```

The notebook covers:
1. Data preparation — loading and chunking the help-desk markdown by `###` headers
2. RAG system — embedding generation, Chroma DB creation, retriever configuration
3. SQL agent — MCP connection to PostgreSQL, SQL query generation
4. Parent agent — tool registration and query routing
5. End-to-end testing with sample queries

### Production Chat UI

```bash
source .venv-cust-chat-uv/bin/activate
chainlit run chainlit_chatbot_app.py
```

Opens a browser-based chat interface at `http://localhost:8000`.

---

## RAG Knowledge Base

The knowledge base (`retail-store-help-desk-data.md`) contains 32 Q&A pairs covering:

- Store locations and hours
- Delivery Club membership ($100/year, free delivery)
- Delivery policies (minimum order, time windows)
- Return and exchange policies (48 hrs perishables, 14 days shelf-stable)
- Payment methods and security
- Product substitutions

Documents are chunked by `###` header markers, embedded with `text-embedding-3-small`, and stored in a persistent Chroma vector database. Retrieval uses cosine similarity with `k=6` and a `score_threshold=0.25`.

---

## SQL Database

The PostgreSQL database (`retail_db.retail_sales_dataset`) contains order data from 2019–2022 with columns: `Order_ID`, `Order_Date`, `Ship_Date`, `Shipping_Status`, `Customer_ID`, `Customer_Name`, `Customer_Segment`, `Country`, `City`, `State`, `Product_ID`, `Total_Sales_Amount`.

The SQL agent generates SELECT-only queries, schema-qualifies all table names, and limits results to 100 rows.

---

## Learning Objectives

- Build an end-to-end RAG system (ingestion → chunking → embedding → retrieval → generation)
- Connect an LLM agent to a live database using MCP
- Design a multi-tool agentic system with intelligent query routing
- Apply prompt engineering for strict grounding and safe fallback behavior

---

## Potential Enhancements

- Conversational memory and multi-turn context tracking
- Multi-format document ingestion (PDFs, product catalogs)
- Automated document re-indexing pipeline
- React + FastAPI production frontend
- Customer lookup and refund handling tools
