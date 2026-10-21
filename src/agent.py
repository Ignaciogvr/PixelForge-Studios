# ================================================================
# agent.py — Agente principal PixelForge EP2 con LangGraph
# ================================================================
# PASO 4 COMPLETADO
#
# ARQUITECTURA: Agente ReAct con LangGraph (prebuilt create_react_agent)
#
# ¿Por qué create_react_agent y no StateGraph manual?
#   - create_react_agent es el agente ReAct oficial de LangGraph 0.4.x
#   - Implementa el ciclo Thought → Action → Observation internamente
#   - Se integra nativamente con MemorySaver, tools y system prompt
#   - Un StateGraph manual requiere ~200 líneas más sin agregar valor
#     para este caso de uso
#
# CICLO DE RAZONAMIENTO (ReAct):
#   1. Usuario escribe una pregunta
#   2. El LLM razona (Thought): decide qué tool usar y con qué consulta
#   3. El agente ejecuta la tool (Action): llama a consultar_GDD, etc.
#   4. El agente observa el resultado (Observation): lo incorpora al contexto
#   5. El LLM razona de nuevo: ¿tengo suficiente info? ¿necesito otra tool?
#   6. Si tiene suficiente → responde al usuario con fuente citada
#   Si no → repite desde el paso 2 (máximo MAX_ITERATIONS veces)
#
# SISTEMA ANTI-ALUCINACIÓN (en el system prompt):
#   - "Solo usa información de las 4 herramientas"
#   - "Nunca inventes datos — si no tienes información, dilo"
#   - "Cita siempre la fuente: [GDD], [CÓDIGO], [BUG id], [BALANCE]"
#   - "Si la pregunta no es de PixelForge Studios, responde que no puedes ayudar"
# ================================================================

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Importar los módulos EP2 del mismo paquete
from tools import build_tools_desde_datos
from memory import SistemaMemoriaDual, FAISS_INDEX_DIR

load_dotenv()

# ----------------------------------------------------------------
# Logging del agente — los eventos van a consola Y a logs/agent.log
# ----------------------------------------------------------------
_BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_LOGS_DIR  = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_LOGS_DIR, "agent.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("pixelforge.agent")

# ----------------------------------------------------------------
# Parámetros del agente — leídos del .env con defaults robustos
# ----------------------------------------------------------------
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
LLM_MODEL      = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMP       = float(os.getenv("LLM_TEMPERATURE", "0"))

# ----------------------------------------------------------------
# Rutas de los documentos que se indexan en FAISS (Memoria Tipo 2)
# ----------------------------------------------------------------
_DATA_DIR   = os.path.join(_BASE_DIR, "data")
PATH_GDD    = os.path.join(_DATA_DIR, "gdd.txt")
PATH_CODIGO = os.path.join(_DATA_DIR, "codigo_guia.txt")

# ================================================================
# SYSTEM PROMPT — El contrato de comportamiento del agente
# ================================================================
# Las reglas aquí determinan si el agente alucina o no.
# Cada regla tiene una razón de diseño explícita.

_SYSTEM_PROMPT = """Eres el asistente de IA interno de PixelForge Studios, un estudio de
videojuegos indie que desarrolla "Aethelgard: The Fractured Realm".

Tu propósito es ayudar al equipo de desarrollo respondiendo preguntas sobre:
  - El Game Design Document (GDD): mecánicas, lore, enemigos, habilidades
  - Guía de estándares de código Unity/C#: arquitectura, patrones, FSM
  - Tickets de bugs de Jira: estado, prioridad, responsables, pasos de reproducción
  - Balance estadístico de entidades: HP, daño, velocidad, críticos

REGLAS ESTRICTAS (incumplirlas degrada la calidad de la respuesta):

1. SOLO USES LAS 4 HERRAMIENTAS para obtener información.
   Nunca inventes datos sobre el juego, los personajes, los bugs o las estadísticas.

2. CITA SIEMPRE LA FUENTE de cada dato que menciones:
   - [GDD] si el dato viene del Game Design Document
   - [CÓDIGO] si viene de la guía de estándares
   - [BUG <ID>] si viene de un ticket de Jira (ej: [BUG PF-1003])
   - [BALANCE] si viene de las estadísticas de entidades

3. SI NO TIENES INFORMACIÓN responde exactamente:
   "No tengo información sobre eso en los documentos de PixelForge Studios."
   No especules ni completes con conocimiento general.

4. ELIGE LA HERRAMIENTA CORRECTA:
   - consultar_GDD:     diseño del juego, lore, mecánicas, enemigos
   - consultar_codigo:  estándares de código, patrones, arquitectura Unity
   - consultar_bugs:    tickets de Jira, estado, prioridad, pasos de reproducción
   - consultar_balance: estadísticas numéricas de personajes y enemigos

5. PREGUNTAS FUERA DE CONTEXTO:
   Si la pregunta no está relacionada con PixelForge Studios, responde:
   "Soy el asistente interno de PixelForge Studios y solo puedo responder
   preguntas relacionadas con el proyecto Aethelgard."

6. RESPONDE SIEMPRE EN ESPAÑOL."""


# ================================================================
# FUNCIÓN PRINCIPAL — Construir el agente
# ================================================================

def construir_agente(force_rebuild_faiss: bool = False) -> dict:
    """
    Construye y retorna el agente ReAct de PixelForge EP2.

    Flujo de construcción:
    ┌─────────────────────────────────────────────────────────┐
    │ 1. Validar OPENAI_API_KEY                               │
    │ 2. Inicializar el LLM (gpt-4o-mini, temperatura=0)      │
    │ 3. Construir las 4 herramientas (tools.py)              │
    │ 4. Inicializar Sistema de Memoria Dual (memory.py)      │
    │    ├─ Tipo 1: MemorySaver (conversación en RAM)         │
    │    └─ Tipo 2: FAISS (semántica en disco)                │
    │ 5. Crear el agente ReAct con create_react_agent         │
    │ 6. Compilar el grafo con el checkpointer de memoria     │
    └─────────────────────────────────────────────────────────┘

    Args:
        force_rebuild_faiss: si True, reconstruye el índice FAISS aunque
                             ya exista en disco. Usar cuando el GDD cambia.

    Returns:
        dict con las claves:
          "agente"    → grafo compilado de LangGraph listo para invocar
          "memoria"   → SistemaMemoriaDual (para acceso a stats y debugging)
          "tools"     → lista de Tool (para inspección)
          "llm"       → instancia del ChatOpenAI (para reutilizar en demo.py)

    Raises:
        EnvironmentError:  OPENAI_API_KEY no configurada
        FileNotFoundError: algún archivo de datos falta en data/
    """
    logger.info("=" * 55)
    logger.info("  PixelForge EP2 — Construyendo agente ReAct")
    logger.info("=" * 55)

    # ── 1. Validar API key ───────────────────────────────────────────────────
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-..."):
        raise EnvironmentError(
            "OPENAI_API_KEY no configurada.\n"
            "Pasos:\n"
            "  1. Copia .env.example como .env\n"
            "  2. Pon tu clave real de OpenAI\n"
            "  3. Vuelve a ejecutar"
        )

    # ── 2. Inicializar LLM ───────────────────────────────────────────────────
    logger.info(f"[Agent] LLM: {LLM_MODEL} | temperatura={LLM_TEMP}")
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMP,
        api_key=api_key,
    )

    # ── 3. Construir las 4 herramientas ─────────────────────────────────────
    logger.info("[Agent] Inicializando herramientas (tools.py)...")
    tools = build_tools_desde_datos(verbose=True)
    logger.info(f"[Agent] {len(tools)} herramientas listas: {[t.name for t in tools]}")

    # ── 4. Inicializar Sistema de Memoria Dual ───────────────────────────────
    logger.info("[Agent] Inicializando memoria dual (memory.py)...")
    memoria = SistemaMemoriaDual.inicializar(
        paths_documentos=[PATH_GDD, PATH_CODIGO],
        force_rebuild=force_rebuild_faiss,
    )

    # ── 5. Crear el agente ReAct ─────────────────────────────────────────────
    # create_react_agent es el agente ReAct oficial de LangGraph 0.4.x.
    # Recibe:
    #   model:          el LLM con capacidad de tool-calling
    #   tools:          las 4 tools del agente
    #   prompt:         el system prompt con las reglas de comportamiento
    #   checkpointer:   el MemorySaver para persistir el historial de mensajes
    #
    # El result es un CompiledGraph con el ciclo ReAct ya implementado:
    #   ┌─ llm_node ──────────────────────────────┐
    #   │  Razona y decide qué tool llamar         │
    #   └─ tools_node ─────────────────────────────┘
    #      Ejecuta la tool y devuelve el resultado
    #   (ciclo hasta que el LLM no llame más tools)
    logger.info("[Agent] Creando grafo ReAct con create_react_agent...")

    agente_compilado = create_react_agent(
        model=llm,
        tools=tools,
        prompt=_SYSTEM_PROMPT,
        checkpointer=memoria.conversacion,
    )

    logger.info("[Agent] Agente ReAct compilado correctamente")
    logger.info(f"[Agent] Max iterations: {MAX_ITERATIONS}")
    logger.info("[Agent] Sistema listo para recibir consultas")

    return {
        "agente":  agente_compilado,
        "memoria": memoria,
        "tools":   tools,
        "llm":     llm,
    }


# ================================================================
# FUNCIÓN DE INVOCACIÓN — Enviar una consulta al agente
# ================================================================

def consultar_agente(
    sistema: dict,
    pregunta: str,
    thread_id: str = "sesion-1",
) -> str:
    """
    Envía una consulta al agente y retorna su respuesta como string.

    El thread_id identifica el hilo de conversación. Mensajes con el
    mismo thread_id comparten historial (MemorySaver los conecta).
    Mensajes con thread_ids distintos son sesiones independientes.

    Args:
        sistema:   dict retornado por construir_agente()
        pregunta:  texto de la consulta del usuario
        thread_id: identificador del hilo de conversación

    Returns:
        Respuesta del agente como string

    Raises:
        ValueError: pregunta vacía
    """
    if not pregunta or not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")

    agente = sistema["agente"]
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"[Agent] Consulta recibida [thread={thread_id}]: {pregunta[:80]}...")

    try:
        resultado = agente.invoke(
            {"messages": [HumanMessage(content=pregunta)]},
            config=config,
        )

        # El resultado es un dict con clave "messages"
        # El último mensaje es la respuesta del agente (AIMessage)
        mensajes = resultado.get("messages", [])
        if not mensajes:
            return "El agente no produjo respuesta."

        # Buscar el último AIMessage en la lista
        respuesta = ""
        for msg in reversed(mensajes):
            if isinstance(msg, AIMessage) and msg.content:
                respuesta = str(msg.content)
                break

        if not respuesta:
            return "El agente procesó la consulta pero no generó texto de respuesta."

        logger.info(f"[Agent] Respuesta generada: {respuesta[:100]}...")
        return respuesta

    except Exception as e:
        logger.error(f"[Agent] Error en consulta: {type(e).__name__}: {e}")
        return (
            f"Error al procesar la consulta: {type(e).__name__}: {e}\n"
            "Verifica que la API key es válida y los archivos de datos existen."
        )


# ================================================================
# CONSOLA INTERACTIVA — Loop de chat en terminal
# ================================================================

def iniciar_consola(sistema: dict, thread_id: str = "sesion-1") -> None:
    """
    Abre un loop de consola interactivo para chatear con el agente.

    Comandos especiales:
        salir / exit / quit  → termina la sesión
        /nueva               → inicia un nuevo hilo de conversación
        /stats               → muestra estadísticas del sistema de memoria

    El historial de conversación se mantiene durante toda la sesión
    gracias al MemorySaver (Memoria Tipo 1).

    Args:
        sistema:   dict retornado por construir_agente()
        thread_id: hilo inicial de conversación
    """
    current_thread = thread_id
    print("\n" + "=" * 60)
    print("  PixelForge Studios — Asistente de IA Interno")
    print("  Proyecto: Aethelgard: The Fractured Realm")
    print("=" * 60)
    print(f"  Hilo de conversación: {current_thread}")
    print("  Comandos: 'salir' | '/nueva' | '/stats'")
    print("=" * 60 + "\n")

    turno = 0
    while True:
        try:
            pregunta = input(f"[Tú #{turno+1}] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSesión terminada.")
            break

        if not pregunta:
            continue

        # ── Comandos especiales ──────────────────────────────────────────────
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("Sesión terminada. ¡Hasta luego!")
            logger.info(f"[Console] Sesión '{current_thread}' cerrada por el usuario ({turno} turnos)")
            break

        if pregunta == "/nueva":
            turno = 0
            current_thread = f"sesion-{os.urandom(4).hex()}"
            print(f"\n[Sistema] Nuevo hilo iniciado: {current_thread}\n")
            logger.info(f"[Console] Nuevo hilo: {current_thread}")
            continue

        if pregunta == "/stats":
            mem = sistema["memoria"]
            print(f"\n[Stats] {mem}")
            print(f"[Stats] {mem.stats}\n")
            continue

        # ── Consulta normal ──────────────────────────────────────────────────
        print(f"\n[Agente] ", end="", flush=True)
        respuesta = consultar_agente(sistema, pregunta, thread_id=current_thread)
        print(respuesta)
        print()
        turno += 1


# ================================================================
# Ejecución directa: venv\Scripts\activate && python src\agent.py
# Construye el agente completo y abre la consola interactiva
# ================================================================
if __name__ == "__main__":
    sistema = construir_agente()
    iniciar_consola(sistema)
