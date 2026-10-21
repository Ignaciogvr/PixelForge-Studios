# ================================================================
# memory.py — Sistema de memoria DUAL del agente PixelForge EP2
# ================================================================
# PASO 3 COMPLETADO
#
# El agente tiene DOS tipos de memoria, que replican cómo funciona
# la memoria humana:
#
#   TIPO 1 — Memoria de Conversación (MemorySaver de LangGraph)
#   ─────────────────────────────────────────────────────────────
#   • Guarda el historial de mensajes de la sesión actual.
#   • Permite al agente recordar lo que dijo el usuario hace 5 turnos.
#   • Implementada con MemorySaver de LangGraph → se conecta directamente
#     al grafo de estados del agente en Paso 4.
#   • Se persiste automáticamente en RAM mientras el proceso esté activo.
#   • Al cerrar el script, se pierde (no hay BD externa).
#
#   TIPO 2 — Memoria Semántica / Vectorial (FAISS)
#   ─────────────────────────────────────────────────────────────
#   • Indexa los documentos internos de PixelForge (GDD, código).
#   • Permite recuperar los fragmentos más relevantes por similitud semántica.
#   • El índice FAISS se guarda en disco (faiss_index/).
#   • Si el índice ya existe, se carga sin regenerar embeddings
#     (ahorra tiempo de startup y tokens de la API de OpenAI).
#   • Si force_rebuild=True, reconstruye el índice desde cero.
#
# CLASE PRINCIPAL: SistemaMemoriaDual
#   Agrupa ambos tipos en un solo objeto que se pasa al agente.
# ================================================================

from __future__ import annotations

import os
import logging
from typing import List, Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ----------------------------------------------------------------
# Configuración de logging — los mensajes de este módulo se
# distinguen con el prefijo "[Memory]" en los logs del agente
# ----------------------------------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# Rutas absolutas — independientes del directorio de trabajo (CWD)
# ----------------------------------------------------------------
_SRC_DIR       = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR      = os.path.abspath(os.path.join(_SRC_DIR, ".."))
FAISS_INDEX_DIR = os.path.join(_BASE_DIR, "faiss_index")
FAISS_INDEX_NAME = "pixelforge_ep2"   # nombre del índice guardado en disco

# ----------------------------------------------------------------
# Parámetros de chunking — leídos del .env, con defaults robustos
# ----------------------------------------------------------------
DEFAULT_CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "500"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
DEFAULT_K             = int(os.getenv("RETRIEVER_K", "3"))


# ================================================================
# TIPO 1 — Memoria de conversación (LangGraph MemorySaver)
# ================================================================

def crear_memoria_conversacion() -> MemorySaver:
    """
    Crea y retorna la memoria de conversación del agente.

    Usa MemorySaver de LangGraph, que es el mecanismo nativo de
    persistencia del grafo de estados. Almacena el historial de
    mensajes en RAM (checkpoint en memoria) durante la sesión.

    Cómo funciona con el agente (Paso 4):
        - El grafo de LangGraph recibe esta memoria como `checkpointer`
        - Cada turno de conversación se guarda como un checkpoint
        - El agente puede acceder a toda la historia del hilo activo
        - Se identifica el hilo con un `thread_id` (ej: "sesion-1")

    Diferencia vs ConversationBufferMemory (langchain 0.2.x):
        - MemorySaver es la API nativa de LangGraph 0.4.x
        - No requiere wrappers de compatibilidad
        - Se integra directamente en `graph.compile(checkpointer=...)`

    Returns:
        MemorySaver: instancia lista para pasar a graph.compile()
    """
    logger.info("[Memory] Inicializando memoria de conversación (MemorySaver)")
    checkpointer = MemorySaver()
    logger.info("[Memory] MemorySaver creado — historial en RAM activo")
    return checkpointer


# ================================================================
# TIPO 2 — Memoria semántica / vectorial (FAISS)
# ================================================================

def crear_memoria_semantica(
    paths_documentos: List[str],
    force_rebuild: bool = False,
):
    """
    Crea o carga el índice FAISS para memoria semántica (RAG).

    Flujo de decisión:
    ┌─────────────────────────────────────────────────┐
    │ ¿Existe faiss_index/pixelforge_ep2/ en disco?   │
    │ Y ¿force_rebuild es False?                      │
    └─────────┬───────────────────┬───────────────────┘
              │ SÍ                │ NO
              ▼                   ▼
        Carga el índice      Construye el índice:
        desde disco          1. Carga los .txt
        (sin embeddings)     2. Fragmenta en chunks
                             3. Embeds con OpenAI
                             4. Guarda en disco

    Ventaja de cargar desde disco:
        En cada ejecución del agente, NO se regeneran los embeddings.
        Esto ahorra ~2-5 segundos de startup y tokens de OpenAI.

    Parámetros de chunking (leídos del .env):
        CHUNK_SIZE=500:    fragmentos de ~500 caracteres
        CHUNK_OVERLAP=100: solapamiento de 100 chars entre fragmentos
        RETRIEVER_K=3:     recuperar los 3 fragmentos más relevantes

    Args:
        paths_documentos: lista de rutas absolutas a los .txt a indexar.
                          Deben existir en disco o se lanza FileNotFoundError.
        force_rebuild:    si True, reconstruye el índice aunque ya exista.
                          Usar cuando los documentos fuente cambian.

    Returns:
        VectorStoreRetriever configurado con search_type="similarity" y k=DEFAULT_K

    Raises:
        FileNotFoundError: algún archivo de paths_documentos no existe
        EnvironmentError:  OPENAI_API_KEY no configurada (solo al construir)
    """
    # --- Validar que los archivos fuente existen antes de cualquier operación ---
    for path in paths_documentos:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"[Memory] Archivo fuente no encontrado: {path}\n"
                "Verifica que la carpeta data/ contiene los archivos .txt."
            )

    # --- Ruta completa del índice guardado ---
    index_path = os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_NAME)
    index_exists = os.path.exists(index_path)

    embeddings = OpenAIEmbeddings()

    # ── CASO A: Cargar índice existente ─────────────────────────────────────
    if index_exists and not force_rebuild:
        logger.info(
            f"[Memory] Cargando índice FAISS desde disco: {index_path}"
        )
        print(f"  → Cargando índice FAISS desde disco (sin regenerar embeddings)...")
        vectorstore = FAISS.load_local(
            folder_path=index_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,  # necesario en FAISS >= 1.8.x
        )
        n_docs = vectorstore.index.ntotal
        print(f"     Índice cargado: {n_docs} vectores")
        logger.info(f"[Memory] Índice cargado: {n_docs} vectores")

    # ── CASO B: Construir índice desde cero ─────────────────────────────────
    else:
        motivo = "force_rebuild=True" if force_rebuild else "índice no existe en disco"
        logger.info(f"[Memory] Construyendo índice FAISS ({motivo})...")
        print(f"  → Construyendo índice FAISS ({motivo})...")

        # 1. Cargar documentos
        todos_los_docs = []
        for path in paths_documentos:
            loader = TextLoader(path, encoding="utf-8")
            docs = loader.load()
            todos_los_docs.extend(docs)
            logger.debug(f"[Memory] Cargado: {path} ({len(docs)} documento(s))")

        print(f"     {len(todos_los_docs)} documento(s) cargado(s)")

        # 2. Fragmentar en chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            # Separadores ordenados por prioridad: párrafo > línea > encabezado > palabra
            separators=["\n\n", "\n", "## ", "### ", " ", ""],
        )
        chunks = splitter.split_documents(todos_los_docs)
        print(f"     {len(chunks)} chunks generados "
              f"(chunk_size={DEFAULT_CHUNK_SIZE}, overlap={DEFAULT_CHUNK_OVERLAP})")
        logger.info(f"[Memory] {len(chunks)} chunks generados")

        # 3. Vectorizar con embeddings de OpenAI
        print(f"     Vectorizando con OpenAIEmbeddings (esto toma unos segundos)...")
        vectorstore = FAISS.from_documents(chunks, embeddings)

        # 4. Guardar en disco para reutilizar en próximas ejecuciones
        os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
        vectorstore.save_local(index_path)
        n_docs = vectorstore.index.ntotal
        print(f"     Índice guardado en: {index_path} ({n_docs} vectores)")
        logger.info(f"[Memory] Índice guardado: {index_path} ({n_docs} vectores)")

    # ── Configurar y retornar el retriever ──────────────────────────────────
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": DEFAULT_K},
    )
    logger.info(f"[Memory] Retriever configurado: k={DEFAULT_K}")
    return retriever


# ================================================================
# CLASE PRINCIPAL — Sistema de Memoria Dual
# ================================================================

class SistemaMemoriaDual:
    """
    Encapsula los dos tipos de memoria del agente en un solo objeto.

    El agente en Paso 4 recibe una instancia de esta clase y puede:
    - Acceder a `self.memoria.conversacion` para el checkpointer de LangGraph
    - Acceder a `self.memoria.semantica` para el retriever de FAISS

    Uso:
        memoria = SistemaMemoriaDual.inicializar(paths_gdd_y_codigo)
        # Luego en Paso 4:
        graph = construir_grafo(tools, memoria)
        agente = graph.compile(checkpointer=memoria.conversacion)

    Atributos:
        conversacion (MemorySaver):         checkpointer de LangGraph
        semantica    (VectorStoreRetriever): retriever FAISS para RAG
        stats        (dict):                información de diagnóstico
    """

    def __init__(self, conversacion: MemorySaver, semantica, stats: dict):
        self.conversacion = conversacion
        self.semantica    = semantica
        self.stats        = stats

    @classmethod
    def inicializar(
        cls,
        paths_documentos: List[str],
        force_rebuild: bool = False,
    ) -> "SistemaMemoriaDual":
        """
        Constructor principal — inicializa ambos tipos de memoria.

        Args:
            paths_documentos: rutas a los .txt que se indexarán en FAISS
            force_rebuild:    si True, reconstruye el índice FAISS desde cero

        Returns:
            SistemaMemoriaDual con ambas memorias inicializadas
        """
        print("\n[Memory] ─── Inicializando Sistema de Memoria Dual ───")

        # Tipo 1: conversación
        print("\n[Memory] Tipo 1 — Memoria de Conversación:")
        conversacion = crear_memoria_conversacion()
        print("  ✓ MemorySaver activo (historial en RAM)")

        # Tipo 2: semántica
        print("\n[Memory] Tipo 2 — Memoria Semántica (FAISS):")
        semantica = crear_memoria_semantica(paths_documentos, force_rebuild)
        print("  ✓ Retriever FAISS listo")

        stats = {
            "n_documentos_indexados": len(paths_documentos),
            "chunk_size":             DEFAULT_CHUNK_SIZE,
            "chunk_overlap":          DEFAULT_CHUNK_OVERLAP,
            "retriever_k":            DEFAULT_K,
            "faiss_index_path":       os.path.join(FAISS_INDEX_DIR, FAISS_INDEX_NAME),
        }

        print("\n[Memory] ✅ Sistema de Memoria Dual inicializado correctamente")
        print(f"  Documentos indexados: {len(paths_documentos)}")
        print(f"  Chunk size / overlap: {DEFAULT_CHUNK_SIZE} / {DEFAULT_CHUNK_OVERLAP}")
        print(f"  Retriever k:          {DEFAULT_K}")
        print(f"  FAISS en disco:       {stats['faiss_index_path']}")

        return cls(conversacion, semantica, stats)

    def rebuildar_indice(self, paths_documentos: List[str]) -> None:
        """
        Reconstruye el índice FAISS desde cero con nuevos documentos.
        Útil si los archivos fuente cambian (nueva versión del GDD, etc.).
        """
        print("[Memory] Reconstruyendo índice FAISS...")
        self.semantica = crear_memoria_semantica(paths_documentos, force_rebuild=True)
        self.stats["n_documentos_indexados"] = len(paths_documentos)
        print("[Memory] Índice reconstruido.")

    def __repr__(self) -> str:
        return (
            f"SistemaMemoriaDual("
            f"conversacion=MemorySaver, "
            f"semantica=FAISSRetriever(k={self.stats['retriever_k']}), "
            f"docs={self.stats['n_documentos_indexados']})"
        )


# ================================================================
# Ejecución directa: venv\Scripts\activate && python src\memory.py
# Verifica el módulo de forma aislada (requiere OPENAI_API_KEY)
# ================================================================
if __name__ == "__main__":
    import sys

    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    PATH_GDD    = os.path.join(BASE, "data", "gdd.txt")
    PATH_CODIGO = os.path.join(BASE, "data", "codigo_guia.txt")

    print("=" * 60)
    print("  PIXELFORGE EP2 — Test aislado de Memory (Paso 3)")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-..."):
        print("[!] OPENAI_API_KEY no configurada.")
        print("    Configura el .env y vuelve a ejecutar.")
        sys.exit(1)

    memoria = SistemaMemoriaDual.inicializar(
        paths_documentos=[PATH_GDD, PATH_CODIGO],
        force_rebuild=False,
    )
    print()
    print(f"Representación: {memoria}")
