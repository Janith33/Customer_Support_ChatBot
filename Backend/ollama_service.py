# ollama_service.py
import os
import sys
from dotenv import load_dotenv
import ollama

# Always load .env from the Backend folder regardless of current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
load_dotenv(override=True)


class OllamaService:
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=self.host)

        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        self.kv_cache_type = os.getenv("OLLAMA_KV_CACHE_TYPE", "q8_0")

    def is_available(self) -> bool:
        """Check if local Ollama daemon is running and reachable."""
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def generate(self, prompt: str, system: str = None) -> str:
        """Simple single-turn generation with friendly error handling."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat(model=self.model, messages=messages,
            options={
                "num_ctx": self.num_ctx,
                "kv_cache_type": self.kv_cache_type,
            
            },)
            if hasattr(response, "message") and hasattr(response.message, "content"):
                return response.message.content
            return response["message"]["content"]
        except Exception as e:
            err_text = str(e)
            if "10061" in err_text or "refused" in err_text.lower() or "connect" in err_text.lower():
                raise ConnectionError(
                    f"Could not connect to Ollama at {self.host}. "
                    "Make sure Ollama is installed and running ('ollama serve')."
                ) from e
            raise

    def chat(self, messages: list) -> str:
        """Multi-turn chat with friendly error handling."""
        try:
            response = self.client.chat(model=self.model, messages=messages,
            options={
                "num_ctx": self.num_ctx,
                "kv_cache_type": self.kv_cache_type,
                
            },)
            if hasattr(response, "message") and hasattr(response.message, "content"):
                return response.message.content
            return response["message"]["content"]
        except Exception as e:
            err_text = str(e)
            if "10061" in err_text or "refused" in err_text.lower() or "connect" in err_text.lower():
                raise ConnectionError(
                    f"Could not connect to Ollama at {self.host}. "
                    "Make sure Ollama is installed and running ('ollama serve')."
                ) from e
            raise

    def stream_generate(self, prompt: str):
        """Streaming response generator with error handling."""
        try:
            for chunk in self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                options={
                    "num_ctx": self.num_ctx,
                    "kv_cache_type": self.kv_cache_type,
                    
                },
            ):
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    yield chunk.message.content
                else:
                    yield chunk["message"]["content"]
        except Exception as e:
            err_text = str(e)
            if "10061" in err_text or "refused" in err_text.lower() or "connect" in err_text.lower():
                yield f"[Error: Ollama server is not running at {self.host}. Run 'ollama serve' to start.]"
            else:
                yield f"[Error: {err_text}]"


ollama_service = OllamaService()
