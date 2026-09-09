"""
PIXELFORGE AI AGENT - DEMO EP1
Demo simplificada usando OpenAI directamente (sin dependencias de LangChain)
Muestra las 4 preguntas de prueba con contexto real de los archivos de datos.
"""
import os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# ── Cargar los archivos de datos ──────────────────────────────────────────────
def leer_archivo(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def leer_csv(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

BASE = os.path.join(os.path.dirname(__file__), '..', 'data')

GDD          = leer_archivo(os.path.join(BASE, 'gdd.txt'))
CODIGO_GUIA  = leer_archivo(os.path.join(BASE, 'codigo_guia.txt'))
BUGS_CSV     = leer_csv(os.path.join(BASE, 'bugs.csv'))
BALANCE_CSV  = leer_csv(os.path.join(BASE, 'balance.csv'))

# ── System prompt del agente ──────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres el asistente tecnico de Inteligencia Artificial para PixelForge Studios.
Tu objetivo es ayudar a programadores, disenadores y testers a resolver dudas operativas.

REGLAS ESTRICTAS DE RESPUESTA:
1. CERO ALUCINACIONES: Si la respuesta NO esta en el contexto entregado, responde EXACTAMENTE:
   "La informacion solicitada no se encuentra en la documentacion actual del proyecto."
2. TRAZABILIDAD: Siempre cita la fuente (Segun el GDD... / La guia de codigo indica... / Revisando Jira...).
3. ESTRUCTURA: Responde con bullet points (guiones).
4. SINTESIS: Si el problema cruza areas, cruza las fuentes y combina la respuesta."""

# ── Funcion de consulta al agente ─────────────────────────────────────────────
def consultar_agente(pregunta, contexto):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"CONTEXTO DISPONIBLE:\n{contexto}\n\nPREGUNTA: {pregunta}"}
    ]
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0,
    )
    return resp.choices[0].message.content

# ── Definicion de las 4 preguntas con su contexto relevante ──────────────────
DEMOS = [
    {
        "titulo": "PREGUNTA 1 — Cruce Bug + Codigo (Multi-hop QA)",
        "pregunta": "Hay un bug PF-1001 sobre un freeze del personaje al saltar y atacar. Segun la guia de codigo, como deberia solucionarse para evitar este glitch?",
        "contexto": f"=== REPORTE DE BUGS (Jira) ===\n{BUGS_CSV}\n\n=== GUIA DE CODIGO ===\n{CODIGO_GUIA}"
    },
    {
        "titulo": "PREGUNTA 2 — Consulta CSV exacta (Jira Bugs)",
        "pregunta": "Quien tiene asignado el bug PF-1003 y que prioridad tiene?",
        "contexto": f"=== REPORTE DE BUGS (Jira) ===\n{BUGS_CSV}"
    },
    {
        "titulo": "PREGUNTA 3 — Cruce GDD + Balance estadistico",
        "pregunta": "Cuanto dano base hace un Golem de Basalto y cual es la estrategia para derrotarlo segun el GDD?",
        "contexto": f"=== TABLA DE BALANCE ===\n{BALANCE_CSV}\n\n=== GAME DESIGN DOCUMENT (GDD) ===\n{GDD}"
    },
    {
        "titulo": "PREGUNTA 4 — Validacion Anti-Alucinacion",
        "pregunta": "Cual es la historia del Rey Palido en el mundo de Aethelgard?",
        "contexto": f"=== GAME DESIGN DOCUMENT (GDD) ===\n{GDD}"
    },
]

# ── Ejecucion de la demo ──────────────────────────────────────────────────────
print()
print("=" * 65)
print("   PIXELFORGE AI AGENT  ·  DEMO EVALUACION PARCIAL 1")
print("   Asignatura: ISY0101 | Ignacio Nunez · Rene Marambio")
print("=" * 65)

for demo in DEMOS:
    print(f"\n>>> {demo['titulo']}")
    print(f"Desarrollador > {demo['pregunta']}")
    print("-" * 65)
    try:
        respuesta = consultar_agente(demo['pregunta'], demo['contexto'])
        print(f"Agente PixelForge AI >\n{respuesta}")
    except Exception as e:
        print(f"[Error]: {e}")
    print("-" * 65)

print("\n[FIN DE LA DEMO]")
