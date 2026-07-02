# MediConnect Care Assistant — Streamlit UI

A rich chat interface for your n8n RAG Agent, so anyone can use it in a browser without touching n8n.

## 1. Get your n8n webhook URL

1. Open your **RAG Agent** workflow in n8n
2. Click on the **"When chat message received"** node
3. Make sure the workflow is **Published/Active**
4. Copy the **Production URL** shown on that node (it looks like `https://your-instance.app.n8n.cloud/webhook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

> If you're using n8n's built-in Chat Trigger node specifically, this is the webhook that receives `chatInput` and `sessionId` and returns the agent's reply.

## 2. Configure the app

Open `app.py` and update this line near the top with your actual webhook URL:

```python
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/your-webhook-id"
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the app

```bash
streamlit run app.py
```

It will open automatically at `http://localhost:8501`.

## 5. Share it with others

- **Quick share (temporary):** use a tunnel like `ngrok http 8501`
- **Permanent hosting:** deploy free on [Streamlit Community Cloud](https://streamlit.io/cloud) by connecting this GitHub repo
- **Internal team use:** host on any VM/server with `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`

## Troubleshooting

| Symptom | Likely Cause |
|---|---|
| "Could not connect to the assistant" | n8n workflow isn't Published/Active, or wrong webhook URL |
| Response is generic/empty | Check the response field name — some n8n versions return `output`, others `text` — adjust in `get_agent_response()` if needed |
| Slow responses | Normal for RAG (embedding + vector search + LLM generation) — typically 2-5 seconds |
| Rate limit errors showing in chat | Your Groq free-tier TPM limit was hit — see main project README for model recommendations |

## Notes

- Each browser session gets its own `session_id`, so conversations don't mix between users.
- Click **"New Conversation"** in the sidebar to reset chat memory for a fresh session.
- The sidebar's suggested questions are just quick-start examples — feel free to edit them in `app.py` to match your actual document content.
