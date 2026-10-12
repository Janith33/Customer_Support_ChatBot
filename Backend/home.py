import os
import re
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Forntend"))

# Initialize Flask application
app = Flask(__name__, static_folder=FRONTEND_DIR)
# Enable CORS so your frontend (home.html) can send requests from browser
CORS(app)



def get_bot_response(user_message: str) -> str:
    
    message = user_message.lower().strip()

    if not message:
        return "Please type a message so I can help you."

    if re.search(r"\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b", message):
        return (
            "Hello! Welcome to Customer Support. "
            "How can I help you today?"
        )

    elif re.search(r"\b(fiber|fibre|package|packages|broadband|internet|unlimited|speed|data)\b", message):
        return (
            "SLT-Mobitel offers high-speed Fibre broadband packages:\n"
            "• Fibre Unlimited (Flash 10, Flash 25, Unlimited Entertainment)\n"
            "• Web Starter & Web Family packages\n"
            "• Work & Learn / Gaming add-on bundles\n"
            "Visit https://www.slt.lk/broadband or open the MySLT app for full package details."
        )

    elif re.search(r"\b(bill|billing|pay|payment|due|balance|reload)\b", message):
        return (
            "You can view and pay your SLT-Mobitel bills through:\n"
            "• MySLT Mobile App (Android / iOS)\n"
            "• Online Portal: https://myslt.slt.lk\n"
            "• E-bill registration via SMS or email\n"
            "• Any SLT Teleshop, regional telecom office, or online banking."
        )

    elif re.search(r"\b(peo|peotv|peo tv|tv|channels|channel)\b", message):
        return (
            "SLT PEO TV provides crystal-clear HD channels, video-on-demand, and rewind TV.\n"
            "Packages include Titanium, Gold, Silver, and Bronze.\n"
            "To activate new channels or packages, visit the MySLT app or call 1212."
        )

    elif re.search(r"\b(mobitel|sim|esim|mobile|4g|5g|postpaid|prepaid|roaming)\b", message):
        return (
            "For Mobitel mobile services:\n"
            "• Prepaid & Postpaid data/voice plans\n"
            "• eSIM activation available at all Mobitel branches\n"
            "• Dial #170# for self-care services or download the Mobitel Selfcare App."
        )

    elif re.search(r"\b(slow|not working|broken|fault|red light|los|pon|router|wifi|wi-fi|disconnected|issue)\b", message):
        return (
            "Quick troubleshooting steps for your connection:\n"
            "1. Restart your router (turn off, wait 30 seconds, turn back on).\n"
            "2. Check the 'LOS' light: if it's blinking red, there is a fiber cable issue.\n"
            "3. Ensure the 'PON' light is solid green.\n"
            "To report a technical fault, dial 1212 or submit a fault ticket via the MySLT app."
        )

    elif re.search(r"\b(hotline|call|contact|agent|human|customer care|number|help|support)\b", message):
        return (
            "You can reach SLT-Mobitel customer support 24/7:\n"
            "• SLT Hotline: 1212\n"
            "• Mobitel Hotline: 1717\n"
            "• WhatsApp Support: +94 70 599 9999\n"
            "• Email: info@slt.com.lk"
        )

    elif re.search(r"\b(thanks|thank you|bye|goodbye|cya)\b", message):
        return "Thank you for contacting Us! Have a wonderful day!"

    else:
        return (
            "I'm sorry, I didn't quite catch that. "
            "You can ask me about:\n"
            "1. Fibre / Broadband packages\n"
            "2. Bill payments & balance\n"
            "3. PEO TV\n"
            "4. Router & connection issues\n"
            "5. Contact hotline numbers"
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
    # If run with '--cli', run the terminal chat
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        # Default: start the web API server on port 5000
        print("Starting SLT Chatbot Flask server on http://127.0.0.1:5000 ...")
        print("Run with 'python home.py --cli' if you want terminal chat mode.")
        app.run(host="127.0.0.1", port=5000, debug=True)
