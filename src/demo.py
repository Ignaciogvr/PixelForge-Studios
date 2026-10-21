# ================================================================
# demo.py — Demo en vivo del agente PixelForge EP2
# ================================================================
# PASO 5 COMPLETADO
#
# PROPÓSITO:
#   Este script es la demostración técnica del sistema para la evaluación.
#   Ejecuta 5 escenarios que cubren todas las capacidades del agente:
#
#   Escenario 1 — Multi-hop GDD + Código:
#     El agente combina dos fuentes para responder.
#     Prueba que el ciclo ReAct llama a MÁS DE UNA tool cuando es necesario.
#
#   Escenario 2 — Exactitud CSV (Bugs Jira):
#     Pregunta con ID exacto de bug.
#     Prueba que el agente Pandas retorna datos exactos sin alucinaciones.
#
#   Escenario 3 — Multi-hop GDD + Balance:
#     Combina información de diseño con estadísticas numéricas.
#     Prueba la coordinación entre tools semánticas y tabulares.
#
#   Escenario 4 — Anti-alucinación (pregunta fuera del dominio):
#     Pregunta completamente ajena al proyecto.
#     Prueba que el agente rechaza correctamente sin inventar.
#
#   Escenario 5 — Memoria conversacional:
#     La segunda pregunta referencia la primera ("el que mencioné antes").
#     Prueba que el MemorySaver mantiene el historial entre turnos.
#
# USO:
#   venv\Scripts\activate
#   python src\demo.py
#
# REQUIERE:
#   - OPENAI_API_KEY configurada en .env
#   - Todos los archivos en data/
#   - venv con dependencias instaladas
# ================================================================

from __future__ import annotations

import os
import sys
import time
import logging
from typing import List

from dotenv import load_dotenv

# Asegurar que src/ esté en sys.path para imports relativos
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from agent import construir_agente, consultar_agente

load_dotenv()

# ----------------------------------------------------------------
# Logging de la demo — separado del log del agente
# ----------------------------------------------------------------
_BASE_DIR = os.path.abspath(os.path.join(_SRC_DIR, ".."))
_LOGS_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,  # solo warnings en consola durante la demo
    handlers=[
        logging.FileHandler(
            os.path.join(_LOGS_DIR, "demo.log"), encoding="utf-8"
        )
    ],
)
logger = logging.getLogger("pixelforge.demo")


# ================================================================
# ESCENARIOS DE DEMO
# ================================================================
# Cada escenario tiene:
#   id:          identificador único
#   thread_id:   hilo de conversación (escenario 5 comparte hilo con 2)
#   titulo:      título para mostrar en pantalla
#   descripcion: qué demuestra este escenario
#   preguntas:   lista de preguntas (multi-turno si hay más de una)
#   esperar:     segundos de pausa entre preguntas (para demo en vivo)
# ================================================================

ESCENARIOS = [
    {
        "id": 1,
        "thread_id": "demo-escenario-1",
        "titulo": "Multi-hop: Bug + Guia de Codigo",
        "descripcion": (
            "El agente debe combinar el reporte del bug PF-1001 "
            "(Freeze en transicion de animacion) con la guia de codigo "
            "para sugerir cómo solucionarlo. "
            "DEMUESTRA: ciclo ReAct con 2+ tools en un solo turno."
        ),
        "preguntas": [
            "Tengo el bug PF-1001 de freeze en animacion. "
            "Segun la guia de codigo, cual es la causa probable y como deberia solucionarlo?"
        ],
        "esperar": 2,
    },
    {
        "id": 2,
        "thread_id": "demo-escenario-2",
        "titulo": "Exactitud CSV: Datos precisos de Jira",
        "descripcion": (
            "Pregunta sobre un ticket con ID exacto de Jira. "
            "DEMUESTRA: el agente Pandas retorna datos exactos del CSV "
            "sin inventar ni aproximar."
        ),
        "preguntas": [
            "Quien tiene asignado el bug PF-1003? "
            "Cual es su prioridad y en que sprint esta?"
        ],
        "esperar": 2,
    },
    {
        "id": 3,
        "thread_id": "demo-escenario-3",
        "titulo": "Multi-hop: Estrategia GDD + Stats de Balance",
        "descripcion": (
            "El agente combina la estrategia de combate del Golem de Basalto "
            "(del GDD) con sus estadísticas numéricas (del CSV de balance). "
            "DEMUESTRA: coordinacion entre RAG semantico y datos tabulares."
        ),
        "preguntas": [
            "Cual es la estrategia para derrotar al Golem de Basalto "
            "y cuantos HP tiene? Que personaje tiene mayor ataque base para enfrentarlo?"
        ],
        "esperar": 2,
    },
    {
        "id": 4,
        "thread_id": "demo-escenario-4",
        "titulo": "Anti-alucinacion: Pregunta fuera del dominio",
        "descripcion": (
            "Pregunta completamente ajena al proyecto PixelForge. "
            "DEMUESTRA: el agente rechaza con el mensaje estandar "
            "y NO inventa informacion."
        ),
        "preguntas": [
            "Cual es la capital de Francia y cuanto vale el euro hoy?"
        ],
        "esperar": 1,
    },
    {
        "id": 5,
        "thread_id": "demo-escenario-2",  # MISMO HILO que escenario 2
        "titulo": "Memoria Conversacional: Referencia al turno anterior",
        "descripcion": (
            "La segunda pregunta referencia el bug consultado en el "
            "escenario 2 sin repetir el ID. "
            "DEMUESTRA: el MemorySaver mantiene el historial — el agente "
            "recuerda de que bug se habló antes."
        ),
        "preguntas": [
            # Esta pregunta solo tiene sentido si el agente recuerda PF-1003
            "Y cuales son los pasos para reproducir ese bug que mencionamos?"
        ],
        "esperar": 1,
    },
]


# ================================================================
# FUNCIONES DE PRESENTACIÓN
# ================================================================

def _separador(char: str = "─", ancho: int = 60) -> str:
    return char * ancho


def _imprimir_encabezado_demo():
    print("\n" + "=" * 60)
    print("  PIXELFORGE EP2 — Demo del Agente de IA Interno")
    print("  Proyecto: Aethelgard: The Fractured Realm")
    print("  5 Escenarios de Evaluacion")
    print("=" * 60)
    print()


def _imprimir_encabezado_escenario(escenario: dict):
    n = escenario["id"]
    titulo = escenario["titulo"]
    desc   = escenario["descripcion"]
    thread = escenario["thread_id"]

    print(f"\n{_separador('═')}")
    print(f"  ESCENARIO {n}/5 — {titulo}")
    print(_separador())
    print(f"  {desc}")
    print(f"  Hilo: {thread}")
    print(_separador())


def _imprimir_pregunta(pregunta: str, turno: int):
    print(f"\n  [Pregunta {turno}]")
    print(f"  {pregunta}")
    print(f"\n  [Respuesta del Agente]")


def _imprimir_respuesta(respuesta: str, tiempo: float):
    # Indentar cada línea de la respuesta
    for linea in respuesta.split("\n"):
        print(f"  {linea}")
    print(f"\n  [Tiempo de respuesta: {tiempo:.1f}s]")


def _imprimir_resumen(resultados: List[dict]):
    print(f"\n{'=' * 60}")
    print("  RESUMEN DE LA DEMO")
    print("=" * 60)
    exitosos = sum(1 for r in resultados if r["ok"])
    print(f"  Escenarios completados: {exitosos}/{len(resultados)}")
    print()
    for r in resultados:
        estado = "OK" if r["ok"] else "FALLO"
        print(f"  [{estado}] Escenario {r['id']}: {r['titulo']}")
        if not r["ok"]:
            print(f"         Error: {r['error']}")
        else:
            print(f"         Tiempo: {r['tiempo']:.1f}s")
    print(f"\n  Logs guardados en: logs/agent.log y logs/demo.log")
    print("=" * 60)


# ================================================================
# FUNCIÓN PRINCIPAL DE DEMO
# ================================================================

def ejecutar_demo(pausa_entre_escenarios: float = 2.0) -> bool:
    """
    Ejecuta los 5 escenarios de demo del agente PixelForge EP2.

    Construye el sistema una sola vez y reutiliza el agente para
    todos los escenarios. El escenario 5 comparte el hilo de conversación
    del escenario 2 para demostrar la memoria conversacional.

    Args:
        pausa_entre_escenarios: segundos de pausa entre escenarios (para demo en vivo)

    Returns:
        True si todos los escenarios completaron sin error fatal,
        False si alguno lanzó una excepción no manejada.
    """
    _imprimir_encabezado_demo()

    # ── Construir el sistema una sola vez ────────────────────────────────────
    print("  Inicializando el agente (puede tomar unos segundos)...")
    print("  (En la segunda ejecucion, el indice FAISS carga desde disco)\n")

    try:
        sistema = construir_agente(force_rebuild_faiss=False)
        print(f"\n  Agente listo. Tools: {[t.name for t in sistema['tools']]}")
        print(f"  Memoria: {sistema['memoria']}")
    except EnvironmentError as e:
        print(f"\n  ERROR DE CONFIGURACION:\n  {e}")
        return False
    except FileNotFoundError as e:
        print(f"\n  ERROR DE ARCHIVOS:\n  {e}")
        return False

    # ── Ejecutar los 5 escenarios ────────────────────────────────────────────
    resultados = []

    for escenario in ESCENARIOS:
        _imprimir_encabezado_escenario(escenario)
        logger.info(f"[Demo] Iniciando escenario {escenario['id']}: {escenario['titulo']}")

        escenario_ok = True
        error_msg    = ""
        tiempo_total = 0.0

        for turno, pregunta in enumerate(escenario["preguntas"], start=1):
            _imprimir_pregunta(pregunta, turno)

            t0 = time.time()
            try:
                respuesta = consultar_agente(
                    sistema=sistema,
                    pregunta=pregunta,
                    thread_id=escenario["thread_id"],
                )
                tiempo = time.time() - t0
                tiempo_total += tiempo
                _imprimir_respuesta(respuesta, tiempo)

                logger.info(
                    f"[Demo] Escenario {escenario['id']} turno {turno}: "
                    f"{tiempo:.1f}s | respuesta={len(respuesta)} chars"
                )

            except Exception as e:
                tiempo = time.time() - t0
                error_msg = f"{type(e).__name__}: {e}"
                print(f"\n  [ERROR] {error_msg}")
                logger.error(f"[Demo] Escenario {escenario['id']} turno {turno}: {error_msg}")
                escenario_ok = False

            # Pausa entre preguntas del mismo escenario
            if turno < len(escenario["preguntas"]):
                time.sleep(escenario["esperar"])

        resultados.append({
            "id":     escenario["id"],
            "titulo": escenario["titulo"],
            "ok":     escenario_ok,
            "tiempo": tiempo_total,
            "error":  error_msg,
        })

        # Pausa entre escenarios
        if escenario["id"] < len(ESCENARIOS):
            print(f"\n  [Pausa {pausa_entre_escenarios}s antes del siguiente escenario...]")
            time.sleep(pausa_entre_escenarios)

    # ── Resumen final ────────────────────────────────────────────────────────
    _imprimir_resumen(resultados)
    return all(r["ok"] for r in resultados)


# ================================================================
# Ejecución directa: venv\Scripts\activate && python src\demo.py
# ================================================================
if __name__ == "__main__":
    ok = ejecutar_demo(pausa_entre_escenarios=2.0)
    sys.exit(0 if ok else 1)
