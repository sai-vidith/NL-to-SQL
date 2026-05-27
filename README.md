# Nexus — Enterprise NL-to-SQL Analytics Platform

Nexus is a production-grade, conversational intelligence platform that allows corporate analysts and business executives to query enterprise data warehouses using plain natural language. Nexus compiles intent structures, generates dialect-correct SQL code, validates the queries for database security compliance, and charts visual summaries.

---

## 🌟 Key Features

*   **Conversational Chat Workspace**: Intuitive ChatGPT-like interface that allows multi-turn queries, table rendering, and dynamic data exploration.
*   **Dual LLM Engine Support**: Primary intelligence powered by **Google Gemini 2.5 Flash** for rapid, structured SQL generation, with secondary fallback support for open-source LLMs (e.g. **Qwen-Coder**, **Llama-3**) via the **Hugging Face Inference API**.
*   **Resilient Vector Store (RAG)**: Integrates vector embeddings (Google or Hugging Face sentence-transformers) with **PostgreSQL pgvector** to dynamically fetch schema contexts and select few-shot prompt examples.
*   **AST Safety Validation**: Utilizes **SQLGlot AST Parsing** to inspect generated queries before execution. Blocks all mutating commands (INSERT, DELETE, UPDATE, DROP, ALTER) to enforce read-only safety.
*   **Dynamic Visualizations**: Integrated with **Recharts (Frontend)** and **Matplotlib (Telegram)** to auto-recommend and render Bar, Line, Pie, and Doughnut charts.
*   **Omnichannel Delivery**: Complete feature set exposed via a **Web Dashboard**, an automated **Telegram Bot Interface** (with push chart exports), and a structured **REST API**.
*   **Role-Based Access Control (RBAC)**: Fine-grained security layers distinguishing Admin, Analyst, and Viewer permissions.

---

## 📐 System Architecture

```text
                               ┌────────────────────────────────┐
                               │       Clients: Web / Bot       │
                               └───────────────┬────────────────┘
                                               │ (JWT Auth / REST)
                                               ▼
                              ┌──────────────────────────────────┐
                              │    Gateway Layer (FastAPI)       │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │    Orchestration (QueryService)  │
                              └────────────────┬─────────────────┘
                                               │
             ┌─────────────────────────┼─────────────────────────┐
             ▼                         ▼                         ▼
┌────────────────────────┐┌────────────────────────┐┌────────────────────────┐
│   Intent Classifier    ││    Schema Retriever    ││     SQL Generator      │
│  (Gemini / HuggingFace)││  (pgvector Search)     ││ (Gemini / Qwen-Coder)  │
└────────────────────────┘└────────────────────────┘└────────────────────────┘
             │                         │                         │
             └─────────────────────────┼─────────────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │  AST Safety Filter (SQLGlot)     │
                              └────────────────┬─────────────────┘
                                               │ (Only SELECTs permitted)
                                               ▼
                              ┌──────────────────────────────────┐
                              │   Read-Only Connection Pool      │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │    Matplotlib / Recharts         │
                              │     (Visual Summarization)       │
                              └──────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
*   Node.js (v20+) & npm
*   Python (v3.11+)
*   Docker & Docker Compose

### Option A: Local Containerized Run (Recommended)
This runs the entire stack (FastAPI Backend, React Frontend, PostgreSQL with pgvector, and Redis cache) using a single command:

1. Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```
2. Build and launch the containers:
   ```bash
   docker-compose up --build
   ```
3. Open `http://localhost` in your browser to access the dashboard.

---

### Option B: Local Developer Mode

#### 1. Setup Backend
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   source venv/bin/activate  # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure `.env` and start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Setup Frontend
1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 🔌 Database Connection & Setup

To connect Nexus to your own target database, configure the connection strings in your environment variables.

### 1. Update Connection Settings (`.env`)
Create or edit your `.env` file (e.g., `backend/.env`) to declare connection drivers. By default, Nexus operates using a self-custodial local SQLite database, meaning your schemas, bookmarks, and logs are saved privately in your local environment.
```env
# Read-write connection (Nexus metadata, logs, and user schemas stored locally)
DATABASE_URL=sqlite+aiosqlite:///./nexus.db

# Or use private remote PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nlsql
```
*Note: Nexus uses `aiosqlite` for SQLite and `asyncpg` for PostgreSQL in SQLAlchemy connection strings for asynchronous database interactions.*

### 2. Configure Database Privileges (PostgreSQL)
Ensure your read-only user only has SELECT rights on target tables:
```sql
GRANT CONNECT ON DATABASE nlsql TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER USER readonly_user SET statement_timeout = '10000'; -- 10s query limit
```

---

## 🔒 Security Precautions


*   **Read-Only Database Pool**: Always run client queries against a separate database connection pool configured with a user that has restricted `SELECT` privileges. Never run generated queries using the main write-enabled database user.
*   **Enforce Statement Timeouts**: Set `statement_timeout` (e.g. 5-10 seconds) on the read-only user to prevent complex generated queries (e.g., massive cross-joins) from blocking database threads.
*   **AST Safety Validation**: Keep the AST safety check enabled. Gemini or Hugging Face models can occasionally generate mutating commands if prompted cleverly (Prompt Injection); SQLGlot ensures only `SELECT` structures reach the database.
*   **Result Set Row Limits**: Always cap execution output rows (e.g., `LIMIT 1000`) on the database side to avoid memory overflow on large tables.

---

## 💡 How to Use Efficiently

*   **Few-Shot Prompt Training**: Keep the `few_shot_examples` database table populated. When users ask questions, pgvector searches for similar historical questions and feeds their validated SQL queries into the LLM context. This increases accuracy from 70% to 95%+.
*   **Cache Utilization**: Frequent or identical dashboard queries are cached in Redis. Leverage this by keeping caching active for standard monthly/weekly business metric views.
*   **Clear Schema Definitions**: Keep column descriptions in the database comments or schema metadata table detailed. The AI utilizes these semantic definitions (e.g. "active status indicates order ship date is not null") to select correct tables.

---

## 🔄 Real-Time Schema Synchronization

## 🔄 Real-Time Schema Synchronization

To ensure the agent responds instantly to live database catalog updates (such as newly added tables or altered columns), Nexus implements a real-time **Schema Watcher** service:
*   Calculates a cryptographic hash of the active system catalog (`information_schema` tables/columns).
*   Runs during query orchestration to dynamically verify structural consistency.
*   Automatically invalidates outdated schema embedding caches when catalog changes are detected.

For conceptual design architecture detailing how Nexus handles large-scale legacy database schema mappings using OS Virtual Memory Paging, Merkle Trees, and OOP Virtual Proxies, see the [Legacy System Summarization Guide](backend/docs/legacy_db_summarization.md).

---

## ⚡ In-Memory RAM Execution Engine

For startups requiring sub-millisecond query execution on legacy transactional records without constant network overhead, Nexus supports **In-Memory RAM Database Execution**:
*   **Opt-in Acceleration**: Toggle `ENABLE_IN_MEMORY_DB=true` inside `.env`.
*   **Database Isolation**: At startup, Nexus reads business schema metadata, sets up an in-memory SQLite sandbox (`sqlite+aiosqlite:///:memory:`), and copies metrics into system RAM.
*   **Blazing Speeds**: Client queries execute directly against memory buffers, avoiding cloud database disk latency.

---

## 🔒 Single-User Secure Proxy Architecture

Nexus is specifically engineered for single-users (e.g. startup founders, business owners, or independent developers) who need to access their database metrics securely from anywhere without exposing database credentials or raw database ports directly to the public internet.

*   **API Shielding Proxy**: The database is hosted inside a private VPC or firewall. Only the lightweight Nexus FastAPI backend is exposed to the internet via proxy. All client interactions go through the API, keeping raw database login info protected.
*   **HttpOnly Cookie Authentication**: Instead of storing sensitive authentication tokens inside `localStorage` (which is vulnerable to Cross-Site Scripting or XSS attacks), Nexus uses **HttpOnly Cookies** with `SameSite=Lax` configuration. The tokens are sent to and verified by the backend automatically and cannot be accessed via client-side javascript.
*   **Intelligent Query Cache Memory**: Most frequently queried questions (e.g. weekly KPIs, sales statistics) are saved inside an in-memory query cache dictionary. If the database schema watcher detects DDL catalog changes, the cache is instantly invalidated to prevent serving stale data.

---

## ⚠️ Potential Bottlenecks & Design Trade-offs

*   **LLM Translation Latency**: Query translation using Gemini or Hugging Face Inference API takes roughly ~1.5 seconds. For real-time applications requiring millisecond responses, caching frequent metrics is critical.
*   **Neon Serverless Waking Delay**: If using Neon PostgreSQL free tier, the database compute node suspends after 5 minutes of inactivity. The first query after suspension incurs a cold start waking latency of ~2-3 seconds. Consider **Supabase** or **Render** options for permanent compute nodes.
*   **Vector Dimensionality Match**: Fallback Hugging Face embedding models must be selected carefully to match the pgvector 768-dimension schema metadata table column restrictions.
*   **RAM Limits**: In-memory database mode is limited by the server's available RAM. Suitable for databases under 5GB.


