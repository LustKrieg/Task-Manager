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