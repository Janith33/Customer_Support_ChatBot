import os
import re
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure Windows terminal can print Unicode/emojis without charmap encoding crash
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Locate Frontend directory (support both 'Forntend' and 'Frontend' folder spellings)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Forntend"))
if not os.path.exists(FRONTEND_DIR):
    alt_frontend = os.path.abspath(os.path.join(BASE_DIR, "..", "Frontend"))
    if os.path.exists(alt_frontend):
        FRONTEND_DIR = alt_frontend

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
load_dotenv(override=True)

# Optional local Ollama integration
try:
    from ollama_service import ollama_service
except ImportError:
    ollama_service = None

# OpenAI / OpenRouter client setup
api_key = os.getenv("OPENAI_API_KEY")
is_openrouter = bool(api_key and api_key.startswith("sk-or-v1"))
base_url = "https://openrouter.ai/api/v1" if is_openrouter else None

client = None
if api_key and (api_key.startswith("sk-") or is_openrouter):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception as init_err:
        print(f"Warning: Failed to initialize OpenAI client: {init_err}")
        client = None

DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free" if is_openrouter else "gpt-4o-mini"

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

SYSTEM_PROMPT = """You are a polite, helpful, and professional Customer Support Assistant.
Your role is to assist customers with:
- Broadband and Fibre packages (speeds, unlimited plans, web family, gaming packages and no promotion that going on currently)
- Bill payments (MySLT app, online portal at myslt.slt.lk, e-billing)
- PEO TV packages, channels, and activation
- Mobitel mobile services (prepaid, postpaid, eSIM, #170# selfcare)
- Router troubleshooting (restarting router, checking LOS red light / PON green light)
- Customer support hotlines (SLT: 1212, Mobitel: 1717, WhatsApp: +94 70 599 9999)

Guidelines:
- Provide clear, concise, and structured answers (use bullet points where appropriate).
- If the user has a technical fault, guide them step-by-step and provide hotline numbers if unresolved.
- Maintain a courteous and friendly tone.
- if user sent "Hi", "Hello", "Hey", "Hi", "Hay" or "Hii", respond as "Hello! How can I help you today?"
-if user sent "thank you", "thanks", "Thank you" or "Thanks", respond as "You're welcome! Is there anything else I can help you with?"
-if the user ask anything irrelevant to the above topics, respond as "I'm sorry, I can only help with broadband and Fibre packages, bill payments, 
    PEO TV packages, Mobitel mobile services, router troubleshooting, and customer support hotlines. Please ask your question again."
-don't give always as "Hello! How can I help you today?" beginning of the all the responses.
- every key word should be in bold ""
"""


def get_bot_response(user_message: str) -> str:
    message = user_message.strip()

    if not message:
        return "Please type a message so I can help you."

    # 1. Try OpenAI if a valid key is provided
    if client:
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_msg = str(e)
            print(f"OpenAI API error: {err_msg}")
            # If OpenAI fails, fall through to Ollama check below

    # 2. Fallback to local Ollama if available
    if ollama_service and ollama_service.is_available():
        try:
            return ollama_service.generate(prompt=message, system=SYSTEM_PROMPT)
        except Exception as ollama_err:
            err_text = str(ollama_err).lower()
            print(f"Ollama generation error: {ollama_err}")
            if "out-of-memory" in err_text or "allocate" in err_text or "buffer" in err_text:
                return (
                    f"⚠️ Local AI (Ollama) ran out of memory loading '{ollama_service.model}'.\n\n"
                    "Your computer does not have enough free RAM to run the 8B model.\n\n"
                    "👉 Recommended fix:\n"
                    "1. Use a lighter model like llama3.2 (3B or 1B):\n"
                    "   • In terminal run: ollama run llama3.2\n"
                    "   • In Backend/.env set: OLLAMA_MODEL=llama3.2\n"
                    "2. Or use a free OpenRouter key (https://openrouter.ai/keys) in Backend/.env:\n"
                    "   • OPENAI_API_KEY=sk-or-v1-..."
                )
            if "not found" in err_text or "pull" in err_text:
                return (
                    f"⚠️ Model '{ollama_service.model}' was not found in Ollama.\n\n"
                    f"Please run `ollama run {ollama_service.model}` in your terminal to download it."
                )
            return f"⚠️ Ollama error: {ollama_err}"

    # 3. Informative error messages if neither service responded
    if not api_key:
        return (
            "[!] AI service is not configured.\n"
            "Options to enable AI:\n"
            "1. Add a valid OPENAI_API_KEY (or OpenRouter key) in Backend/.env, OR\n"
            "2. Start Ollama locally ('ollama serve' and 'ollama run llama3')."
        )

    if not (api_key.startswith("sk-") or is_openrouter):
        return (
            "[!] The OPENAI_API_KEY in Backend/.env does not look like a standard OpenAI key (starting with 'sk-').\n"
            "If you want to use local AI, please start Ollama ('ollama serve') with model 'llama3'."
        )

    return (
        "I'm sorry, I am currently having trouble connecting to AI services. "
        "Please try again in a moment, or contact our 24/7 hotline at 1212 for assistance."
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """API endpoint for frontend web requests."""
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"reply": "Please provide a valid message."}), 400

    bot_reply = get_bot_response(user_message)
    return jsonify({"reply": bot_reply})


@app.route("/", methods=["GET"])
def index():
    """Serve frontend home.html if accessed via browser, else return JSON status."""
    frontend_file = os.path.join(FRONTEND_DIR, "home.html")
    if os.path.exists(frontend_file) and "application/json" not in request.headers.get("Accept", ""):
        return send_from_directory(FRONTEND_DIR, "home.html")
    return jsonify({
        "status": "online",
        "service": "SLT-Mobitel Chatbot API (Flask)",
        "version": "1.0.0",
        "has_openai": bool(client),
        "has_ollama": bool(ollama_service and ollama_service.is_available())
    })


@app.route("/<path:filename>", methods=["GET"])
def static_files(filename):
    """Serve frontend static assets like home.css or images."""
    return send_from_directory(FRONTEND_DIR, filename)


def run_cli():
    """Run interactive chatbot directly in the terminal."""
    print("=" * 55)
    print("       SLT-Mobitel Chatbot (Terminal Mode)")
    print("=" * 55)
    print("Type your question and press Enter.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower().strip() in ["exit", "quit", "q"]:
                print("Bot: Goodbye! Have a great day.")
                break
            response = get_bot_response(user_input)
            print(f"Bot: {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        print("Starting SLT Chatbot Flask server on http://127.0.0.1:5000 ...")
        print("Run with 'python home.py --cli' if you want terminal chat mode.")
        app.run(host="127.0.0.1", port=5000, debug=True)

