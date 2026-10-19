#!/usr/bin/env python3
"""Run live or simulated Alexa Voice to AMD Radeon latency demo."""
import sys
import json
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alexa_amd_demo.voice_handler import AlexaVoiceBridge

def main():
    print("=== INNEROS ALEXA -> AMD RADEON AI PRO R9700 DEMO ===")
    bridge = AlexaVoiceBridge()
    
    # 1. Simulate Alexa LaunchRequest
    launch_req = {"request": {"type": "LaunchRequest"}}
    resp_launch = bridge.handle_alexa_skill_request(launch_req)
    print("\n[Alexa Launch Response]")
    print(resp_launch["response"]["outputSpeech"]["ssml"])

    # 2. Simulate User Query
    user_query = "Alexa, pídele a InnerOS el estado de latencia y velocidad del modelo en el clúster AMD."
    print(f"\n[Usuario por Voz]: \"{user_query}\"")
    
    intent_req = {
        "request": {
            "type": "IntentRequest",
            "intent": {
                "name": "QueryAMDClusterIntent",
                "slots": {
                    "query": {
                        "name": "query",
                        "value": "Dame un resumen breve del estado del acelerador AMD Radeon y velocidad de inferencia."
                    }
                }
            }
        }
    }

    start_exec = bridge.execute_voice_query("Dame un resumen breve del estado del acelerador AMD Radeon y velocidad de inferencia.")
    alexa_reply = start_exec["alexa_response"]["response"]["outputSpeech"]["ssml"]
    
    print("\n[Respuesta sintetizada de Alexa]:")
    print(alexa_reply)
    
    print("\n[Métricas de Inferencia en Acelerador AMD]:")
    lat = start_exec["latency"]
    print(f"- Dispositivo: {lat.get('device')}")
    print(f"- Latencia Total: {lat.get('total_latency_ms')} ms")
    print(f"- TTFT (Tiempo al primer token): {lat.get('ttft_ms')} ms")
    print(f"- Tokens completados: {lat.get('completion_tokens')}")
    print(f"- Velocidad: {lat.get('tokens_per_second')} tok/s")
    print(f"- Ejecución en vivo (Hardware real): {lat.get('live')}")

    # Save evidence
    ev_path = ROOT / "evidence" / "alexa_amd_demo_evidence.json"
    ev_path.write_text(json.dumps(start_exec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEvidencia guardada exitosamente en {ev_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
