# Summarizing Large Legacy Databases for LLMs

When dealing with legacy enterprise systems, databases often contain thousands of tables, cryptic column names (`CUST_M_ADDR_L1`), and no formal documentation. Feeding this entire schema to an LLM is impossible due to token limits, cost, and hallucination. 

To solve this, we can apply core concepts from **Operating Systems**, **Data Structures**, and **Object-Oriented Programming (OOP)**.

---

## 1. OS Concept: Virtual Memory Paging & Working Sets

In an OS, **Virtual Memory** allows programs to run even if they require more RAM than physically exists, by loading only the active "Pages" into memory.

### Application: Schema Paging
Instead of keeping the entire database schema in the LLM context, we treat the schema as virtual pages:
*   **Table Page**: Each table's structural definition (columns, types, comments, relationships) is serialized into a discrete text "page" (usually 1–2KB).
*   **Working Set**: The agent maintains a "Working Set" of active tables currently relevant to the user's conversational context.
*   **Page Table**: A mapping registry (held in memory or Redis) tracking which tables are currently loaded in the LLM's prompt context.
*   **Page Fault**: When the user asks a question requiring tables outside the current working set (e.g. joining `biz_payments` with `biz_reviews` when only `biz_orders` is loaded), a "Page Fault" occurs. The schema retriever intercepts this, loads the missing pages from the vector database, and evicts the Least Recently Used (LRU) tables to fit the token budget.

---

## 2. Data Structure Concept: Merkle Trees & Prefix Tries

### Merkle Schema Trees (Hash Trees)
To ensure the agent is "quick on uptake" for updates, we structure database metadata hierarchically as a **Merkle Tree**:
*   Every table column is a leaf node containing a hash of its definition.
*   A table node's hash is the cryptographic combination of all its column hashes.
*   A schema domain (e.g., `Sales`, `Inventory`) is a parent node combining table hashes.
*   The entire database has a single **Root Schema Hash**.
*   **Instant Uptake**: When the watcher runs, it only compares the root hashes. If they match, the system bypasses catalog reloading. If they differ, it traverses down the tree in $O(\log N)$ time to pinpoint the exact table that was altered and re-embeds only that single node.

### Trie-Based Semantic Indexes (Prefix Trees)
Legacy systems often use abbreviated columns (e.g., `rev_inr` for revenue in Indian Rupees).
*   We index all columns and table definitions in a **Prefix Trie** structure containing business synonyms (e.g., matching `earnings`, `sales`, `revenue` to the Trie node path pointing to `rev_inr`).
*   This allows the agent to translate user keywords to physical column names instantly in $O(L)$ time (where $L$ is the keyword length), bypass LLM calls entirely for lookup, and pre-filter schema context.

---

## 3. OOP Design Pattern: Flyweights & Virtual Proxies

### Flyweight Pattern
With thousands of tables, creating heavy representation objects for every table in python memory can lead to high resource usage.
*   We use the **Flyweight Pattern** to share common schema metadata. We create a shared pool of data types (e.g., VARCHAR, TIMESTAMP) and table relationships.
*   Only the unique semantic attributes (table name and primary key) are stored in individual objects, keeping the memory footprint minimal.

### Virtual Proxy Pattern
Instead of instantiating the full schema object representing columns, foreign keys, constraints, and statistical distributions, we use a **Virtual Proxy**:
*   The application works with a lightweight `TableProxy` object.
*   The `TableProxy` contains only the table name and a vector representation.
*   Only when the LLM orchestrator explicitly requests column details does the proxy intercept the call, retrieve the full details from pgvector, instantiate the underlying database schema model on demand, and cache it.
