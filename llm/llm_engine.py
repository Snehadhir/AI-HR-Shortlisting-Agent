"""
llm/llm_engine.py
-----------------
FINAL Deterministic LLM Engine
Optimized for CPU + 16GB RAM
"""

import re
import requests


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"

# FAST SMALL MODEL
MODEL = "qwen2.5:1.5b"

# CPU SAFE
TIMEOUT_SECONDS = 120


# ─────────────────────────────────────────────
# LLM ENGINE
# ─────────────────────────────────────────────

class LLMEngine:

    def __init__(
        self,
        model: str = MODEL,
        base_url: str = OLLAMA_BASE_URL
    ):

        self.model = model

        self.base_url = base_url

        self._check_connection()

    # ─────────────────────────────────────────
    # CHAT
    # ─────────────────────────────────────────

    def chat(
        self,
        system_prompt: str,
        user_message: str
    ) -> str:

        raw = self._call(

            system_prompt,

            user_message
        )

        _, final = self._parse_response(raw)

        return final.strip()

    # ─────────────────────────────────────────
    # CHAT WITH THINKING
    # ─────────────────────────────────────────

    def chat_with_thinking(
        self,
        system_prompt: str,
        user_message: str
    ) -> tuple[str, str]:

        raw = self._call(

            system_prompt,

            user_message
        )

        thinking, final = self._parse_response(raw)

        return final.strip(), thinking.strip()

    # ─────────────────────────────────────────
    # CHECK MODEL
    # ─────────────────────────────────────────

    def is_available(self) -> bool:

        try:

            r = requests.get(

                f"{self.base_url}/api/tags",

                timeout=5
            )

            models = [

                m["name"]

                for m in r.json().get(
                    "models",
                    []
                )
            ]

            return any(

                self.model in m

                for m in models
            )

        except Exception:

            return False

    # ─────────────────────────────────────────
    # CHECK OLLAMA
    # ─────────────────────────────────────────

    def _check_connection(self):

        try:

            requests.get(

                f"{self.base_url}/api/tags",

                timeout=5
            )

        except requests.exceptions.ConnectionError:

            raise ConnectionError(

                "\n❌ Ollama is not running!\n\n"

                "Start Ollama:\n"

                "    ollama serve\n\n"

                "Then pull model:\n"

                "    ollama pull qwen2.5:1.5b\n"
            )

    # ─────────────────────────────────────────
    # CALL MODEL
    # ─────────────────────────────────────────

    def _call(
        self,
        system_prompt: str,
        user_message: str
    ) -> str:

        payload = {

            "model": self.model,

            "stream": False,

            "messages": [

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": user_message
                },
            ],

            "options": {

                # FULLY DETERMINISTIC
                "temperature": 0,

                "top_p": 0.1,

                "repeat_penalty": 1.0,

                "seed": 42,

                # LOWER TOKENS = FASTER
                "num_predict": 1024,
            }
        }

        try:

            response = requests.post(

                f"{self.base_url}/api/chat",

                json=payload,

                timeout=TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            data = response.json()

            return data.get(

                "message",

                {}
            ).get(

                "content",

                ""
            )

        except requests.exceptions.Timeout:

            raise TimeoutError(

                f"\n⏱ Model timed out after "

                f"{TIMEOUT_SECONDS}s.\n"
            )

        except requests.exceptions.RequestException as e:

            raise RuntimeError(

                f"\nOllama API error:\n{e}\n"
            )

    # ─────────────────────────────────────────
    # CLEAN OUTPUT
    # ─────────────────────────────────────────

    def _parse_response(
        self,
        raw: str
    ) -> tuple[str, str]:

        if not raw:

            return "", ""

        # REMOVE THINK TAGS
        think_match = re.search(

            r"<think>(.*?)</think>",

            raw,

            flags=re.DOTALL
        )

        if think_match:

            thinking = think_match.group(1).strip()

            final = raw[
                think_match.end():
            ].strip()

        else:

            thinking = ""

            final = raw.strip()

        # REMOVE MARKDOWN
        final = re.sub(

            r"^```(?:json)?\s*",

            "",

            final
        )

        final = re.sub(

            r"\s*```$",

            "",

            final
        )

        # REMOVE CONTROL CHARS
        final = re.sub(

            r"[\x00-\x1f\x7f]",

            " ",

            final
        )

        # NORMALIZE SPACES
        final = re.sub(

            r"\s+",

            " ",

            final
        )

        return thinking, final.strip()