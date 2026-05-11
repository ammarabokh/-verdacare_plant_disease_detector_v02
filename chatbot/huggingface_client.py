import os
from huggingface_hub import InferenceClient
from config import Config


class HuggingFaceClient:
    def __init__(self):
        self.api_key = os.environ.get("HF_TOKEN") or Config.HF_TOKEN
        self.model = os.environ.get("HF_MODEL") or "Qwen/Qwen2.5-72B-Instruct"
        self.max_tokens = Config.HF_MAX_TOKENS
        self.temperature = Config.HF_TEMPERATURE

    def _client(self):
        if not self.api_key:
            raise RuntimeError("HF_TOKEN is missing.")
        return InferenceClient(api_key=self.api_key)

    def generate_response(self, prompt, history=None, system_prompt=None):
        """Generate non-streaming response using Hugging Face chat completions."""
        messages = self._build_messages(prompt, history, system_prompt)

        client = self._client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=False,
        )

        return response.choices[0].message.content

    def generate_stream(self, prompt, history=None, system_prompt=None):
        """Generate streaming response using Hugging Face chat completions."""
        messages = self._build_messages(prompt, history, system_prompt)

        try:
            client = self._client()
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"[Streaming failed for {self.model}] {e}")
            yield "Sorry, the AI service is currently unavailable."

    def _build_messages(self, prompt, history, system_prompt):
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system",
                "content": (
                    "You are an agricultural expert assistant. "
                    "Help farmers with plant disease questions, treatment advice, "
                    "and general farming tips. Be concise and practical."
                ),
            })

        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({"role": "user", "content": prompt})
        return messages
