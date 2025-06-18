import os
import openai


class IntentClassifier:
    """Simple intent classifier using OpenAI chat-completion API."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        openai.api_key = self.api_key

    def classify(self, text: str) -> str:
        """Return intent label for the given text."""
        system_prompt = (
            "You are an intent classifier.\n"
            "Possible intents: SCHEDULE_CALLBACK, RESOLVE_ISSUE, OTHER.\n"
            "Return only the intent label."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
        )
        intent = response["choices"][0]["message"]["content"].strip().upper()
        return intent
