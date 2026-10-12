import os
from openai import OpenAI
from dotenv import load_dotenv
import re
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Forntend"))

# Load environment variables from Backend/.env with override=True
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
load_dotenv(override=True)

# Initialize OpenAI client with API key from .env
api_key = os.getenv("OPENAI_API_KEY")

# Check if an OpenRouter key was provided (starts with sk-or-v1)
is_openrouter = bool(api_key and api_key.startswith("sk-or-v1"))
base_url = "https://openrouter.ai/api/v1" if is_openrouter else None

client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free" if is_openrouter else "gpt-4o-mini"

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

SYSTEM_PROMPT = """You are a polite, helpful, and professional Customer Support Assistant.
Your role is to assist customers with:
- Broadband and Fibre packages (speeds, unlimited plans, web family, gaming packages)
- Bill payments and account inquiries (MySLT app, online portal at myslt.slt.lk, e-billing)
- PEO TV packages, channels, and activation
- Mobitel mobile services (prepaid, postpaid, eSIM, #170# selfcare)
- Router troubleshooting (restarting router, checking LOS red light / PON green light)
- Customer support hotlines (SLT: 1212, Mobitel: 1717, WhatsApp: +94 70 599 9999)

Guidelines:
- Provide clear, concise, and structured answers (use bullet points where appropriate).
- If the user has a technical fault, guide them step-by-step and provide hotline numbers if unresolved.
- Maintain a courteous and friendly tone.
"""


def get_bot_response(user_message: str) -> str:
    message = user_message.strip()

    if not message:
        return "Please type a message so I can help you."

    if not client:
        return (
            "⚠️ OpenAI API key is missing. Please add OPENAI_API_KEY to your Backend/.env file."
        )

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
        print(f"AI API error: {err_msg}")
        if "credit_balance_exhausted" in err_msg or "insufficient_quota" in err_msg:
            return (
                "⚠️ OpenAI account has zero credits remaining.\n"
                "Please add credits at https://platform.openai.com/settings/organization/billing/ "
                "or use an OpenRouter API key."
            )
        elif "invalid_api_key" in err_msg or "Incorrect API key" in err_msg:
            return "⚠️ Invalid API key provided. Please verify the key in Backend/.env."
        return (
            "I'm sorry, I am currently having trouble connecting to AI services. "
            "Please try again in a moment, or contact our 24/7 hotline at 1212 for urgent assistance."
        )


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    API endpoint for frontend web requests.
    Expects JSON: {"message": "Hello"}
    Returns JSON: {"reply": "..."}
    """
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
        "service": "SLT-Mobitel Chatbot API",
        "version": "1.0.0"
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
