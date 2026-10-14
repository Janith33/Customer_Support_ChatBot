# Customer Support ChatBot

An intelligent customer support chatbot designed for telecommunication services (broadband, fibre packages, bill payments, PEO TV, Mobitel services, and router troubleshooting).

## 📁 Project Structure

```
Customer_Support_ChatBot/
├── Backend/
│   ├── .env                 # Environment variables (API keys, Ollama host/model)
│   ├── home.py              # Flask server (Web UI host + /api/chat + CLI mode)
│   ├── main.py              # FastAPI server (Ollama AI endpoints + streaming)
│   └── ollama_service.py    # Local Ollama integration service
├── Forntend/
│   ├── home.html            # Responsive customer support chat interface
│   └── home.css             # Modern styling and animations
├── requirements.txt         # Python package dependencies
└── README.md
```

## 🚀 Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`Backend/.env`)
Create or edit `Backend/.env`:

```env
# For local Ollama AI:
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# For OpenAI or OpenRouter (optional):
# OPENAI_API_KEY=sk-...
```

---

## 🏃 Running the Application

### Option A: Flask Server (Web UI + API) - Recommended for Web UI
Runs on `http://127.0.0.1:5000` and automatically serves the chat frontend:
```bash
python Backend/home.py
```
Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Option B: Terminal CLI Mode
Chat directly in your command line:
```bash
python Backend/home.py --cli
```

### Option C: FastAPI Server (Ollama AI API)
Runs on `http://127.0.0.1:8000` with interactive Swagger docs at `/docs`:
```bash
python Backend/main.py
```
Available endpoints:
- `GET  /` - Status and API overview
- `GET  /health` - Check Ollama connection status
- `POST /api/chat` - Compatible chat endpoint
- `POST /api/ai/generate` - Single-turn generation
- `POST /api/ai/chat` - Multi-turn chat
- `POST /api/ai/stream` - Server-Sent Events (SSE) streaming