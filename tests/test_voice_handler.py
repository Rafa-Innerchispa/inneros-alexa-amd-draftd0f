import pytest
from alexa_amd_demo.voice_handler import AlexaVoiceBridge

@pytest.fixture
def bridge():
    return AlexaVoiceBridge()

def test_launch_request(bridge):
    req = {"request": {"type": "LaunchRequest"}}
    resp = bridge.handle_alexa_skill_request(req)
    assert resp["version"] == "1.0"
    assert "<speak>" in resp["response"]["outputSpeech"]["ssml"]
    assert resp["response"]["shouldEndSession"] is False
    assert "InnerOS Voz" in resp["response"]["outputSpeech"]["ssml"]

def test_help_intent(bridge):
    req = {
        "request": {
            "type": "IntentRequest",
            "intent": {"name": "AMAZON.HelpIntent"}
        }
    }
    resp = bridge.handle_alexa_skill_request(req)
    assert resp["response"]["shouldEndSession"] is False
    assert "pregunta a InnerOS" in resp["response"]["outputSpeech"]["ssml"]

def test_stop_intent(bridge):
    req = {
        "request": {
            "type": "IntentRequest",
            "intent": {"name": "AMAZON.StopIntent"}
        }
    }
    resp = bridge.handle_alexa_skill_request(req)
    assert resp["response"]["shouldEndSession"] is True
    assert "Hasta pronto" in resp["response"]["outputSpeech"]["ssml"]

def test_build_alexa_response_formatting(bridge):
    latency = {
        "total_latency_ms": 350.2,
        "ttft_ms": 110.5,
        "tokens_per_second": 32.4
    }
    resp = bridge.build_alexa_response("Test de voz", card_title="Test Card", latency_info=latency)
    assert resp["response"]["card"]["title"] == "Test Card"
    assert "Latencia Total: 350.2 ms" in resp["response"]["card"]["content"]
    assert resp["response"]["outputSpeech"]["ssml"] == "<speak>Test de voz</speak>"

def test_execute_voice_query_contract(bridge):
    res = bridge.execute_voice_query("Hola AMD")
    assert res["ok"] is True
    assert "latency" in res
    assert "total_latency_ms" in res["latency"]
    assert "tokens_per_second" in res["latency"]
    assert "alexa_response" in res
