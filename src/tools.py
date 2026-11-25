# ================================================================
# tools.py — Las 4 herramientas del agente PixelForge EP2
# ================================================================
# PASO 2 — API MODERNA (LangChain 0.3.x / LCEL)
#
# Herramientas implementadas:
#   1. consultar_GDD      -> RAG semántico sobre el Game Design Document
#   2. consultar_codigo   -> RAG semántico sobre la Guía de Estándares de Código
#   3. consultar_bugs     -> Consulta exacta sobre el CSV de Jira (Pandas Agent)
#   4. consultar_balance  -> Consulta exacta sobre el CSV de Balance (Pandas Agent)
#
# API utilizada: create_retrieval_chain + create_stuff_documents_chain (LCEL)
# La cadena de recuperación antigua (deprecada en 0.3.x) fue reemplazada
# por el pipeline LCEL que funciona correctamente con langchain-core 0.3.x.
# ================================================================

from __future__ import annotations

import os
from typing import Callable, List

import pandas as pd
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

# Soporte Groq (gratis) — importacion opcional
try:
    from langchain_groq import ChatGroq
    _GROQ_DISPONIBLE = True
except ImportError:
    _GROQ_DISPONIBLE = False

# Modelo de embeddings gratuito (corre local, sin API key)
_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Cargar variables de entorno desde .env al importar el módulo
load_dotenv()

# ----------------------------------------------------------------
# Rutas absolutas a los datos — independientes del CWD actual
# ----------------------------------------------------------------
_SRC_DIR   = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR  = os.path.abspath(os.path.join(_SRC_DIR, ".."))
_DATA_DIR  = os.path.join(_BASE_DIR, "data")
_FAISS_DIR = os.path.join(_BASE_DIR, "faiss_index")

PATH_GDD    = os.path.join(_DATA_DIR, "gdd.txt")
PATH_CODIGO = os.path.join(_DATA_DIR, "codigo_guia.txt")
PATH_BUGS   = os.path.join(_DATA_DIR, "bugs.csv")
PATH_BALANCE = os.path.join(_DATA_DIR, "balance.csv")


# ================================================================
# BLOQUE 1 — Wrapper de seguridad universal
# ================================================================

def _safe_run(tool_name: str, func: Callable, query: str) -> str:
    """
    Envuelve cualquier función de tool en try/except.

    Si la función lanza excepción, retorna un mensaje de error legible
    en lugar de propagar la excepción y crashear el agente.

    Distingue entre:
    - ValueError: suele ocurrir cuando el agente pandas recibe una consulta
      ambigua o mal formada. El mensaje sugiere reformular.
    - Exception genérico: cualquier otro error (red, API, archivo).

    Args:
        tool_name: nombre de la tool (para el mensaje de error)
        func:      función a ejecutar, recibe un string y retorna uno
        query:     consulta del usuario

    Returns:
        Resultado de func(query) como string, o mensaje de error descriptivo.
    """
    try:
        result = func(query)
        if result is None:
            return f"[{tool_name}]: La consulta no produjo resultados."
        return str(result).strip()
    except ValueError as e:
        return (
            f"[{tool_name}]: No pude interpretar esa consulta. "
            f"Detalle: {e}. "
            "Intenta ser más específico (ejemplo: usa el ID del bug como 'PF-1001' "
            "o el nombre exacto del personaje como 'Golem_Basalto')."
        )
    except Exception as e:
        return (
            f"[{tool_name} - {type(e).__name__}]: {e}. "
            "Si el error persiste, reformula la pregunta o verifica "
            "que el sistema esté inicializado correctamente."
        )


# ================================================================
# BLOQUE 2a — Backend RAG con LCEL (API moderna LangChain 0.3.x)
# ================================================================

# Prompt estándar para los retrievers — respuesta en español,
# sin alucinaciones: si no está en el contexto, lo dice.
_PROMPT_RAG = ChatPromptTemplate.from_template(
    "Responde la siguiente pregunta basándote ÚNICAMENTE en el contexto "
    "proporcionado. Si la respuesta no está en el contexto, responde: "
    "'No tengo información sobre eso en los documentos de PixelForge Studios.'\n\n"
    "Contexto:\n{context}\n\n"
    "Pregunta: {input}"
)


def _crear_retriever_faiss(path_txt: str, nombre: str, llm: ChatOpenAI):
    """
    Construye una cadena de recuperación RAG para un archivo de texto.

    Pipeline LCEL (LangChain 0.3.x):
        TextLoader -> RecursiveCharacterTextSplitter -> OpenAIEmbeddings
        -> FAISS -> retriever -> create_stuff_documents_chain -> create_retrieval_chain

    Parámetros de chunking:
        chunk_size=500:    fragmentos pequeños = mayor precisión semántica
        chunk_overlap=100: preserva contexto entre fragmentos adyacentes
        separators=["\\n\\n","\\n","##","###",...]: respeta estructura del documento

    La cadena retorna un dict {"input": ..., "context": [...], "answer": ...}.
    El wrapper _run_rag() extrae solo el campo "answer".

    Args:
        path_txt: ruta absoluta al archivo .txt a indexar
        nombre:   identificador para los logs de progreso
        llm:      instancia del modelo de lenguaje

    Returns:
        Cadena LCEL lista para invocar con {"input": "pregunta"}
    """
    print(f"  -> Indexando '{nombre}'...")

    loader = TextLoader(path_txt, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
        length_function=len,
        separators=["\n\n", "\n", "##", "###", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"     {len(chunks)} chunks generados")

    # Embeddings gratuitos — corren localmente sin API key
    # Modelo all-MiniLM-L6-v2: 90MB, excelente calidad para documentos cortos
    embeddings = HuggingFaceEmbeddings(
        model_name=_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": int(os.getenv("RETRIEVER_K", "3"))},
    )

    combine_docs_chain = create_stuff_documents_chain(llm, _PROMPT_RAG)
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    print(f"     '{nombre}' indexado correctamente")
    return retrieval_chain


def _run_rag(chain, query: str) -> str:
    """
    Ejecuta una cadena LCEL de retrieval y extrae la respuesta.

    La cadena retorna un dict; este wrapper extrae solo el campo "answer"
    para que la Tool entregue un string limpio al agente.
    """
    result = chain.invoke({"input": query})
    return result.get("answer", str(result))


# ================================================================
# BLOQUE 2b — Backend Pandas Agent (datos tabulares exactos)
# ================================================================

def _crear_agente_pandas(df: pd.DataFrame, nombre: str, llm: ChatOpenAI):
    """
    Crea un agente especializado en consultas sobre un DataFrame de Pandas.

    Usa create_pandas_dataframe_agent que genera y ejecuta código Python
    sobre el DataFrame de forma autónoma para responder preguntas numéricas
    y de filtrado con precisión exacta.

    Parámetros:
        max_iterations=8: límite de pasos del agente para evitar bucles
                         infinitos en consultas ambiguas (default=15 es excesivo)
        allow_dangerous_code=True: necesario para que el agente ejecute Python.
                                   Solo usar con datos internos controlados.

    Args:
        df:     DataFrame con los datos del CSV
        nombre: identificador para logs
        llm:    instancia del modelo de lenguaje

    Returns:
        Agente Pandas listo para usar como backend de una Tool
    """
    print(f"  -> Inicializando agente Pandas '{nombre}'...")
    agente = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=False,
        allow_dangerous_code=True,
        max_iterations=8,
    )
    print(f"     '{nombre}': {df.shape[0]} filas × {df.shape[1]} columnas")
    return agente


# ================================================================
# BLOQUE 3 — Construcción de las 4 Tools
# ================================================================


# Schema explicito para las tools — evita el problema __arg1 vs arg1
class _Q(BaseModel):
    query: str = Field(description="La consulta a realizar")


def build_tools(cadena_gdd, cadena_codigo, agente_bugs, agente_balance) -> List[Tool]:
    """
    Ensambla y retorna las 4 herramientas del agente usando StructuredTool
    con schema explicito (query: str) para maxima compatibilidad con cualquier LLM.
    """
    def _make(name, desc, fn):
        return StructuredTool.from_function(
            func=fn,
            name=name,
            description=desc,
            args_schema=_Q,
        )

    tools = [
        _make(
            "consultar_GDD",
            (
                "USAR CUANDO: la pregunta es sobre el lore del mundo de Aethelgard, "
                "mecanicas del juego (salto, dash, combate, parry, stamina), "
                "habilidades activas (Corte Igneo, Barrera Refractiva, Salto Sismico), "
                "comportamiento o estrategia de enemigos (Slime Corrupto, Golem de Basalto, "
                "Lobo Sombrio, Caballero Caido), progresion del personaje, economia "
                "(Esquirlas de Eter), o cualquier regla de diseno del juego. "
                "Ejemplos: 'como funciona el parry?', 'cual es la estrategia para el Golem?'. "
                "NO usar para: consultas de codigo, bugs de Jira, ni estadisticas numericas."
            ),
            lambda query: _safe_run("consultar_GDD", lambda x: _run_rag(cadena_gdd, x), query),
        ),
        _make(
            "consultar_codigo",
            (
                "USAR CUANDO: la pregunta es sobre estandares de programacion en Unity/C#, "
                "arquitectura de controladores, maquina de estados (FSM), convenciones de "
                "nomenclatura, manejo de memoria, fisicas, capas de colision, object pooling, "
                "prevencion de glitches de animacion. "
                "Ejemplos: 'como prevenir un freeze en transicion de animacion?', "
                "'cuando usar FixedUpdate?'. "
                "NO usar para: mecanicas de diseno del juego, bugs de Jira, ni estadisticas."
            ),
            lambda query: _safe_run("consultar_codigo", lambda x: _run_rag(cadena_codigo, x), query),
        ),
        _make(
            "consultar_bugs",
            (
                "USAR CUANDO: la pregunta pide informacion de un ticket de bug: "
                "estado, prioridad, responsable, sprint, descripcion o pasos para reproducir. "
                "Busca por ID exacto (PF-1001 a PF-1006) o palabras clave. "
                "Columnas: Issue_Key, Summary, Status, Priority, Assignee, Sprint, "
                "Description, Steps_to_Reproduce. "
                "Ejemplos: 'quien tiene asignado PF-1003?', 'cuantos bugs criticos hay?'. "
                "NO usar para: mecanicas, codigo, ni estadisticas de balance."
            ),
            lambda query: _safe_run("consultar_bugs", agente_bugs.run, query),
        ),
        _make(
            "consultar_balance",
            (
                "USAR CUANDO: la pregunta requiere valores numericos exactos de personajes "
                "o enemigos: HP_Base, Mana_Base, Stamina, Move_Speed, Attack_Base, Def_Base, "
                "Crit_Chance o Crit_Multiplier. "
                "Jugadores: Arquero_Viento, Guerrero_Tierra, Mago_Fuego. "
                "Enemigos: Slime_Corrupto, Lobo_Sombrio, Golem_Basalto, Caballero_Caido. "
                "Ejemplos: 'cuanto HP tiene el Golem de Basalto?', "
                "'que personaje tiene mayor dano base?'. "
                "NO usar para: lore del juego, bugs de Jira, ni codigo."
            ),
            lambda query: _safe_run("consultar_balance", agente_balance.run, query),
        ),
    ]

    return tools


# ================================================================
# BLOQUE 4 — Factory completa: inicializa TODO desde cero
# ================================================================

def build_tools_desde_datos(verbose: bool = True) -> List[Tool]:
    """
    Factory completa que valida el ambiente, inicializa los 4 backends
    y retorna las herramientas listas para el agente.

    Flujo de inicialización:
    1. Verifica que OPENAI_API_KEY esté configurada (falla rápido y claro)
    2. Verifica que los 4 archivos de datos existen en disco
    3. Inicializa el LLM con temperatura=0 (respuestas deterministas)
    4. Construye las 2 cadenas RAG con FAISS para GDD y Código
    5. Carga los 2 CSV y crea los agentes Pandas para Bugs y Balance
    6. Ensambla y retorna las 4 Tools

    Args:
        verbose: si True, imprime progreso detallado en consola

    Returns:
        List[Tool]: las 4 herramientas listas para el agente

    Raises:
        EnvironmentError: OPENAI_API_KEY no configurada o es el valor template
        FileNotFoundError: algún archivo de datos no existe en data/
    """
    # --- Validación API key segun proveedor (Groq o OpenAI) ---
    proveedor = os.getenv("LLM_PROVIDER", "openai").lower()

    if proveedor == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY no configurada.\n"
                "Registrate gratis en console.groq.com y pon tu key en .env:"
                "  GROQ_API_KEY=gsk_..."
            )
        if not _GROQ_DISPONIBLE:
            raise EnvironmentError(
                "langchain-groq no instalado. Ejecuta:\n"
                "  venv\\Scripts\\pip install langchain-groq==0.2.3"
            )
    else:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-..."):
            raise EnvironmentError(
                "OPENAI_API_KEY no configurada.\n"
                "Pasos:\n"
                "  1. Copia .env.example como .env\n"
                "  2. Abre .env y reemplaza 'sk-...' con tu clave real de OpenAI\n"
                "  3. Guarda el archivo y vuelve a ejecutar"
            )

    # --- Validación temprana de archivos de datos ---
    archivos_requeridos = {
        "gdd.txt":         PATH_GDD,
        "codigo_guia.txt": PATH_CODIGO,
        "bugs.csv":        PATH_BUGS,
        "balance.csv":     PATH_BALANCE,
    }
    for nombre, ruta in archivos_requeridos.items():
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"Archivo de datos requerido no encontrado: '{nombre}'\n"
                f"Ruta esperada: {ruta}\n"
                "Verifica que la carpeta data/ contiene los 4 archivos."
            )

    if verbose:
        print("\n[Tools] Inicializando motor LLM...")
        print(f"  Proveedor: {proveedor.upper()}")
        print(f"  Modelo: {os.getenv('LLM_MODEL', 'openai/gpt-oss-120b' if proveedor == 'groq' else 'gpt-4o-mini')}")
        print(f"  Embeddings: HuggingFace/{_EMBEDDING_MODEL} (gratuito, local)")
        print(f"  Temperatura: 0 (determinista)")

    if proveedor == "groq":
        modelo = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        llm = ChatOpenAI(temperature=0, model=modelo, api_key=api_key,
                         base_url="https://api.groq.com/openai/v1")
    else:
        modelo = os.getenv("LLM_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(temperature=0, model=modelo, api_key=api_key)

    if verbose:
        print("\n[Tools] Construyendo cadenas RAG (FAISS + LCEL)...")

    cadena_gdd    = _crear_retriever_faiss(PATH_GDD,    "GDD",            llm)
    cadena_codigo = _crear_retriever_faiss(PATH_CODIGO, "Guía de Código", llm)

    if verbose:
        print("\n[Tools] Cargando DataFrames CSV...")

    df_bugs    = pd.read_csv(PATH_BUGS,    encoding="utf-8")
    df_balance = pd.read_csv(PATH_BALANCE, encoding="utf-8")

    agente_bugs    = _crear_agente_pandas(df_bugs,    "Bugs Jira", llm)
    agente_balance = _crear_agente_pandas(df_balance, "Balance",   llm)

    if verbose:
        print("\n[Tools] Ensamblando las 4 herramientas...")

    tools = build_tools(cadena_gdd, cadena_codigo, agente_bugs, agente_balance)

    if verbose:
        print(f"\n[Tools] ✅ Listo. {len(tools)} herramientas inicializadas:")
        for t in tools:
            print(f"  - {t.name}")

    return tools


# ================================================================
# BLOQUE 5 — Smoke test: verifica que las tools no crashean
# ================================================================

def test_tools(tools: List[Tool]) -> bool:
    """
    Ejecuta una consulta mínima sobre cada tool y verifica que retorna
    un string no vacío sin crashear. No valida la calidad de la respuesta.

    Requiere OPENAI_API_KEY configurada porque hace llamadas reales a la API.
    Usar solo para validar el sistema antes de la demo.

    Args:
        tools: lista de Tools a testear

    Returns:
        True si todas pasaron, False si alguna falló
    """
    PREGUNTAS_TEST = {
        "consultar_GDD":     "¿En qué mundo se ambienta el juego?",
        "consultar_codigo":  "¿Qué patrón de diseño usan los controladores?",
        "consultar_bugs":    "¿Cuántos bugs hay en total?",
        "consultar_balance": "¿Cuántas entidades hay en la tabla de balance?",
    }

    tools_por_nombre = {t.name: t for t in tools}
    resultados: dict[str, bool] = {}

    print("\n[Test] Ejecutando smoke test de las 4 tools (requiere API key)...")
    for nombre, pregunta in PREGUNTAS_TEST.items():
        tool = tools_por_nombre.get(nombre)
        if not tool:
            print(f"  ✗ '{nombre}' no encontrada en la lista")
            resultados[nombre] = False
            continue
        try:
            respuesta = tool.func(pregunta)
            ok = isinstance(respuesta, str) and len(respuesta.strip()) > 10
            print(f"  {'✅' if ok else '✗'} {nombre}: {respuesta[:80]}...")
            resultados[nombre] = ok
        except Exception as e:
            print(f"  ✗ {nombre}: {type(e).__name__}: {e}")
            resultados[nombre] = False

    todas_ok = all(resultados.values())
    estado = "✅ Todas las tools pasaron." if todas_ok else "⚠️  Algunas fallaron — revisar antes de la demo."
    print(f"\n[Test] {estado}")
    return todas_ok


# ================================================================
# Ejecución directa: venv\Scripts\python.exe src\tools.py
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  PIXELFORGE EP2 — Test aislado de Tools (Paso 2)")
    print("=" * 60)
    herramientas = build_tools_desde_datos(verbose=True)
    test_tools(herramientas)
