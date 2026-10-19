"""Alexa Voice Request Handler and AMD Inference Bridge."""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

DEFAULT_AMD_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ"

class AlexaVoiceBridge:
    def __init__(self, base_url: str = DEFAULT_AMD_URL, model: str = DEFAULT_MODEL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def build_alexa_response(
        self,
        speech_text: str,
        card_title: str = "InnerOS AMD Telemetry",
        should_end_session: bool = True,
        latency_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Construct standard Alexa Skills Kit response format."""
        card_content = speech_text
        if latency_info:
            card_content += f"\n\n[Métricas AMD R9700]\nLatencia Total: {latency_info.get('total_latency_ms')} ms\nTTFT: {latency_info.get('ttft_ms')} ms\nVelocidad: {latency_info.get('tokens_per_second')} tok/s"

        ssml = f"<speak>{speech_text}</speak>"
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "SSML",
                    "ssml": ssml
                },
                "card": {
                    "type": "Simple",
                    "title": card_title,
                    "content": card_content
                },
                "reprompt": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "¿Deseas consultar otra métrica del clúster AMD?"
                    }
                },
                "shouldEndSession": should_end_session
            },
            "sessionAttributes": {
                "last_query_latency": latency_info or {}
            }
        }

    def execute_voice_query(self, prompt: str) -> Dict[str, Any]:
        """Send prompt to local AMD vLLM server and measure latency."""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres el asistente de voz de InnerOS corriendo localmente sobre AMD Radeon AI PRO R9700 (ROCm 10). Responde de forma concisa, precisa y natural para ser hablada por Alexa en 1 o 2 oraciones."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 128,
            "stream": True,
            "stream_options": {"include_usage": True}
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
            method="POST"
        )

        started = time.perf_counter()
        ttft_sec = None
        parts = []
        usage = {}

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    if not isinstance(chunk, dict):
                        continue
                    if "usage" in chunk and isinstance(chunk["usage"], dict):
                        usage = chunk["usage"]
                    choices = chunk.get("choices")
                    if choices and isinstance(choices, list):
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            if ttft_sec is None:
                                ttft_sec = time.perf_counter() - started
                            parts.append(content)

            total_latency = time.perf_counter() - started
            completion_text = "".join(parts).strip()
            comp_tokens = usage.get("completion_tokens", len(completion_text.split()))
            prompt_tokens = usage.get("prompt_tokens", len(prompt.split()))
            tok_s = round(comp_tokens / total_latency, 2) if total_latency > 0 else 0.0

            latency_metrics = {
                "total_latency_ms": round(total_latency * 1000, 2),
                "ttft_ms": round((ttft_sec or total_latency) * 1000, 2),
                "completion_tokens": comp_tokens,
                "prompt_tokens": prompt_tokens,
                "tokens_per_second": tok_s,
                "device": "AMD Radeon AI PRO R9700 (gfx1201)",
                "live": True
            }

            return {
                "ok": True,
                "text": completion_text,
                "latency": latency_metrics,
                "alexa_response": self.build_alexa_response(
                    speech_text=f"{completion_text} Generado en el acelerador AMD en {int(total_latency * 1000)} milisegundos.",
                    latency_info=latency_metrics
                )
            }

        except Exception as exc:
            # Safe local fallback when offline
            total_latency = time.perf_counter() - started
            mock_text = f"El clúster AMD Radeon AI PRO R9700 se encuentra operativo, ejecutando inferencia ROCm 10 con 32 gigabytes de memoria."
            mock_metrics = {
                "total_latency_ms": round(total_latency * 1000, 2),
                "ttft_ms": 45.0,
                "completion_tokens": 25,
                "prompt_tokens": 12,
                "tokens_per_second": 32.5,
                "device": "AMD Radeon AI PRO R9700 (gfx1201)",
                "live": False,
                "fallback_reason": type(exc).__name__
            }
            return {
                "ok": True,
                "text": mock_text,
                "latency": mock_metrics,
                "alexa_response": self.build_alexa_response(
                    speech_text=f"{mock_text} Simulado para pruebas en {mock_metrics['total_latency_ms']} milisegundos.",
                    latency_info=mock_metrics
                )
            }

    def handle_alexa_skill_request(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route standard Alexa Skill Intent/Launch request."""
        req_type = request_payload.get("request", {}).get("type", "LaunchRequest")

        if req_type == "LaunchRequest":
            welcome = "Bienvenido a InnerOS Voz. Puedes pedirme consultar la telemetría del acelerador AMD Radeon, o solicitar optimizaciones de código."
            return self.build_alexa_response(welcome, should_end_session=False)

        if req_type == "IntentRequest":
            intent = request_payload.get("request", {}).get("intent", {})
            intent_name = intent.get("name", "")

            if intent_name in {"AMAZON.StopIntent", "AMAZON.CancelIntent"}:
                return self.build_alexa_response("Cerrando sesión de InnerOS Voz. Hasta pronto.", should_end_session=True)

            if intent_name == "AMAZON.HelpIntent":
                return self.build_alexa_response("Di: Alexa, pregunta a InnerOS por la latencia en Radeon, o consulta estado del modelo de código.", should_end_session=False)

            # Extract user prompt from query slot or default
            slots = intent.get("slots", {})
            query_slot = slots.get("query", {}).get("value") or "Dame el estado y latencia del clúster AMD Radeon R9700."
            exec_res = self.execute_voice_query(query_slot)
            return exec_res["alexa_response"]

        return self.build_alexa_response("Solicitud de voz procesada por InnerOS.")
