import json
import urllib.request


class OllamaProvider:
    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"
    SYSTEM_PROMPT = "You are a helpful assistant. Answer concisely."

    def __init__(self, host=None, model=None):
        self.host = host or self.DEFAULT_HOST
        self.model = model or self.DEFAULT_MODEL

    def chat_stream(self, messages, on_chunk):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        full_text_parts = []
        with urllib.request.urlopen(req, timeout=180) as response:
            for raw_line in response:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    full_text_parts.append(chunk)
                    on_chunk(chunk)
                if data.get("done"):
                    break
        return "".join(full_text_parts)

    def generate_title(self, first_message: str) -> str:
        messages = [
            {"role": "system", "content": "Summarize the user's message into a 2-4 word title. Do not use punctuation or quotes. Use the same language as the user."},
            {"role": "user", "content": first_message}
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 10} # Keep it extremely short
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                title = data.get("message", {}).get("content", "").strip()
                # Clean up the title (remove quotes, newlines)
                title = title.replace('"', '').replace("'", "").strip()
                if '\n' in title:
                    title = title.split('\n')[0]
                return title[:80] if title else " ".join(first_message.split()[:3])
        except Exception as e:
            print(f"Title generation failed: {e}")
            # Smart fallback: just take the first 3 words (prevents horizontal scroll)
            return " ".join(first_message.split()[:3])