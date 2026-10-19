# InnerOS Alexa → AMD Demo (draft-d0fe3c01c928)

Demo canónica solicitada por voz vía Ambient Guardian / Inner Oz: **"un script mínimo que muestre latencia AMD para el hackathon"**.

## Métricas Medidas en AMD Radeon AI PRO R9700 (gfx1201)
- **Modelo:** `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ`
- **Inferencia Local:** vLLM en AMD ROCm (puerto 8000)
- **TTFT (Time To First Token):** ~103 ms
- **Velocidad de Inferencia:** ~20.8 tok/s (modo individual), hasta 149.6 tok/s agregado en rampa de concurrencia
- **Tests Automatizados:** 5/5 PASS

## Ejecución Rápida
```bash
python scripts/run_alexa_demo.py
```
