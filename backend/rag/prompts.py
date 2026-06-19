"""Pre-built audit prompts for SEC filing RAG analysis."""

from __future__ import annotations

from typing import Dict

SYSTEM_PROMPT = """Eres un analista financiero experto en Small Caps, dilución y warrants.
Responde usando SOLO la información de los extractos del documento citados.
Si no hay información, di: 'Información no disponible en el documento'.
Cita frases exactas del documento. Sin especulación. Temperatura 0."""

PROMPTS: Dict[str, str] = {
    "warrants": """Identifica si existen 'warrants' en este documento SEC.
Desglosa:
1) Volumen total autorizado
2) Exercise price y expiración
3) Cláusulas anti-dilución Full Ratchet o reajustes de precio
4) Pre-funded warrants / cashless exercise
5) Impacto de dilución si se ejercen todos
Responde en español con citas textuales.""",

    "convertible": """Busca 'Convertible Notes' o 'Convertible Debt'.
Determina si precio de conversión es fijo o flotante con descuento (death-spiral).
Extrae monto, vencimiento, triggers de conversión forzada.
Responde en español con citas textuales.""",

    "atm": """Determina si hay oferta 'At-the-Market' (ATM).
Extrae: sales agent/broker, límite monetario total en USD, shares registradas.
Responde en español con citas textuales.""",

    "dilution": """Auditoría completa de riesgo de dilución.
Analiza: shelf S-3, warrants, convertibles, ATM, splits.
Estima % dilución vs shares outstanding. Clasifica Low/Med/High.
Responde en español con citas textuales.""",

    "shelf": """Analiza shelf registration (S-3).
Extrae monto USD, securities incluidos, use of proceeds, expiración.
Responde en español con citas textuales.""",
}


def get_prompt(name: str) -> str:
    key = name.lower().strip()
    if key not in PROMPTS:
        available = ", ".join(sorted(PROMPTS.keys()))
        raise ValueError(f"Unknown prompt '{name}'. Available: {available}")
    return PROMPTS[key]


def list_prompts() -> Dict[str, str]:
    return {k: v.split("\n")[0] for k, v in PROMPTS.items()}
