# MediConnect Care – RAG Agent

A Retrieval-Augmented Generation (RAG) chatbot built with **n8n** that ingests PDF project documents, generates embeddings via **Cohere**, stores them in **Supabase (pgvector)**, and answers user queries using a **Groq-hosted LLM** with conversational memory (Postgres). Designed to let users ask natural-language questions and get accurate answers grounded in uploaded documentation.

## 🧠 How It Works

1. **Ingestion Flow** (manual trigger)
   - Downloads a PDF file (Google Drive)
   - Loads and splits the document into chunks (Recursive Character Text Splitter)
   - Generates embeddings for each chunk (Cohere `embed-english-v3.0`)
   - Stores chunks + embeddings in a Supabase `documents` table (pgvector)

2. **Chat Flow** (triggered on incoming chat message)
   - User sends a question
   - AI Agent (powered by Groq LLM) decides whether to search the document store
   - Retrieves relevant chunks from Supabase Vector Store as a tool
   - Uses Postgres Chat Memory to maintain conversation context
   - Returns a grounded, context-aware answer

## 🏗️ Architecture

```
Chat Trigger → AI Agent ──┬── Chat Model (Groq)
                           ├── Memory (Postgres Chat Memory)
                           └── Tool: Supabase Vector Store
                                       └── Embeddings (Cohere)

Manual Trigger → Download File (Google Drive)
               → Default Data Loader (Binary/PDF)
               → Recursive Character Text Splitter
               → Embeddings (Cohere)
               → Supabase Vector Store (Insert Documents)
```

## 🛠️ Tech Stack

- **Workflow Engine:** [n8n](https://n8n.io)
- **LLM:** Groq (`llama-3.1-8b-instant` recommended for RAG workloads)
- **Embeddings:** Cohere (`embed-english-v3.0`, 1024 dimensions)
- **Vector Store:** Supabase (Postgres + pgvector)
- **Chat Memory:** Postgres Chat Memory (n8n node)
- **File Source:** Google Drive

## ⚙️ Setup

### 1. Prerequisites
- n8n instance (self-hosted or cloud)
- Supabase project with `pgvector` extension enabled
- Groq API key
- Cohere API key
- Google Drive OAuth credential (for document source)

### 2. Supabase Table Setup

```sql
create extension if not exists vector;

create table documents (
  id bigserial primary key,
  content text,
  metadata jsonb,
  embedding vector(1024) -- must match your embedding model's output dimension
);

create or replace function match_documents (
  query_embedding vector(1024),
  match_count int default 4,
  filter jsonb default '{}'
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where documents.metadata @> filter
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

> ⚠️ If you change your embedding model/provider later, make sure the `vector(...)` dimension matches your new model's output size on **both** the table and the function.

### 3. Environment / Credentials Needed in n8n
| Credential         | Used By                          |
|---------------------|-----------------------------------|
| Groq API Key         | Groq Chat Model node             |
| Cohere API Key        | Embeddings Cohere nodes         |
| Supabase URL + Service Role Key | Supabase Vector Store nodes |
| Google Drive OAuth2    | Download File node              |
| Postgres credentials  | Postgres Chat Memory node        |

### 4. Import the Workflow
1. Download `RAG-Agent.json` from this repo
2. In n8n: **Workflows → Import from File**
3. Reconnect all credentials (they are not exported for security)
4. Update the Google Drive file ID/URL to point to your source document
5. Run the ingestion flow once (**Execute workflow**) to populate Supabase
6. Publish the workflow and test via the Chat panel

## 🚀 Usage

Once deployed, send a question through the chat trigger, e.g.:
> "Search the documents and tell me the project scope and timeline."

The agent will retrieve relevant chunks from Supabase and respond with a grounded answer.

## 📌 Notes / Gotchas

- Embedding dimension **must match exactly** between your embedding model and the Supabase `embedding` column, or inserts will silently fail or error with a dimension mismatch.
- Groq's free tier has token-per-minute (TPM) rate limits — for RAG workloads (long context), lighter models like `llama-3.1-8b-instant` are recommended over `llama-3.3-70b-versatile`.
- Ensure the "Document" sub-node connection between your Data Loader and Vector Store node is a real (solid) connection, not just visually adjacent — a broken link causes silent ingestion failures.

## 📄 License

MIT (or update as appropriate)
