"""
verify_all.py - Verificacion integral del sistema PixelForge EP2
Ejecutar con: venv\\Scripts\\python.exe verify_all.py
"""
import ast
import os
import sys

# Fijar paths absolutos desde la raiz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR  = os.path.join(BASE_DIR, "src")
VENV_SP  = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Aislar el venv del sistema global
sys.path = [p for p in sys.path if "site-packages" not in p or "venv" in p]
if VENV_SP not in sys.path:
    sys.path.insert(0, VENV_SP)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

errores = []
advertencias = []


def ok(msg):
    print(f"  OK  {msg}")


def err(msg):
    print(f"  ERROR  {msg}")
    errores.append(msg)


def warn(msg):
    print(f"  WARN  {msg}")
    advertencias.append(msg)


def check_archivo(path, descripcion):
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{descripcion} ({size} bytes)")
        return True
    else:
        err(f"{descripcion} NO ENCONTRADO: {path}")
        return False


def check_sintaxis(path, nombre):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    try:
        ast.parse(src)
        ok(f"Sintaxis valida: {nombre}")
        return src
    except SyntaxError as e:
        err(f"Error de sintaxis en {nombre}: {e}")
        return None


def check_import(modulo, nombre):
    try:
        m = __import__(modulo)
        ver = getattr(m, "__version__", "OK")
        ok(f"import {nombre}: {ver}")
        return True
    except ImportError as e:
        err(f"import {nombre}: {e}")
        return False


def check_simbolo(src, simbolo, descripcion):
    if simbolo in src:
        ok(f"{descripcion}: {simbolo}")
        return True
    else:
        err(f"FALTANTE {descripcion}: {simbolo}")
        return False


# ================================================================
print()
print("=" * 60)
print("  PIXELFORGE EP2 — Verificacion Integral de los 5 Pasos")
print("=" * 60)

# ──────────────────────────────────────────────────────────────
print("\n[PASO 1] Estructura y archivos de datos")
print("-" * 40)
check_archivo(os.path.join(DATA_DIR, "gdd.txt"),           "gdd.txt")
check_archivo(os.path.join(DATA_DIR, "codigo_guia.txt"),   "codigo_guia.txt")
check_archivo(os.path.join(DATA_DIR, "bugs.csv"),          "bugs.csv")
check_archivo(os.path.join(DATA_DIR, "balance.csv"),       "balance.csv")
check_archivo(os.path.join(BASE_DIR, ".env.example"),      ".env.example")
check_archivo(os.path.join(BASE_DIR, ".gitignore"),        ".gitignore")
check_archivo(os.path.join(BASE_DIR, "requirements.txt"),  "requirements.txt")
check_archivo(os.path.join(BASE_DIR, "README.md"),         "README.md")
# venv
if os.path.exists(VENV_SP):
    ok(f"venv/Lib/site-packages/ existe")
else:
    err(f"venv no encontrado en {VENV_SP}")

# ──────────────────────────────────────────────────────────────
print("\n[DEPENDENCIAS] Paquetes del venv")
print("-" * 40)
deps_ok = True
for modulo, nombre in [
    ("pandas",              "pandas"),
    ("faiss",               "faiss-cpu"),
    ("langchain",           "langchain"),
    ("langchain_openai",    "langchain-openai"),
    ("langchain_community", "langchain-community"),
    ("langchain_experimental", "langchain-experimental"),
    ("langchain_text_splitters", "langchain-text-splitters"),
    ("langgraph",           "langgraph"),
    ("dotenv",              "python-dotenv"),
]:
    if not check_import(modulo, nombre):
        deps_ok = False

# ──────────────────────────────────────────────────────────────
print("\n[PASO 2] src/tools.py")
print("-" * 40)
tools_path = os.path.join(SRC_DIR, "tools.py")
src_tools = check_sintaxis(tools_path, "tools.py")
if src_tools:
    # API moderna
    check_simbolo(src_tools, "create_retrieval_chain",      "API moderna LCEL")
    check_simbolo(src_tools, "create_stuff_documents_chain","API moderna LCEL")
    check_simbolo(src_tools, "ChatPromptTemplate",          "Prompt template")
    # API deprecated ausente
    if "from langchain.chains import RetrievalQA" not in src_tools:
        ok("RetrievalQA deprecated: NO importada")
    else:
        err("RetrievalQA deprecated todavia importada")
    # Funciones
    fns = [n.name for n in ast.walk(ast.parse(src_tools))
           if isinstance(n, ast.FunctionDef)]
    for fn in ["_safe_run", "_run_rag", "_crear_retriever_faiss",
               "_crear_agente_pandas", "build_tools",
               "build_tools_desde_datos", "test_tools"]:
        if fn in fns:
            ok(f"funcion {fn}()")
        else:
            err(f"FALTANTE funcion {fn}()")

# ──────────────────────────────────────────────────────────────
print("\n[PASO 3] src/memory.py")
print("-" * 40)
memory_path = os.path.join(SRC_DIR, "memory.py")
src_memory = check_sintaxis(memory_path, "memory.py")
if src_memory:
    check_simbolo(src_memory, "MemorySaver",                    "API LangGraph")
    check_simbolo(src_memory, "FAISS",                          "Vector store")
    check_simbolo(src_memory, "SistemaMemoriaDual",             "Clase dual")
    check_simbolo(src_memory, "allow_dangerous_deserialization","Flag FAISS load")
    check_simbolo(src_memory, "force_rebuild",                  "Param rebuild")
    check_simbolo(src_memory, "save_local",                     "Persistencia disco")
    check_simbolo(src_memory, "load_local",                     "Carga desde disco")
    fns = [n.name for n in ast.walk(ast.parse(src_memory))
           if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    for fn in ["crear_memoria_conversacion", "crear_memoria_semantica",
               "SistemaMemoriaDual"]:
        if fn in fns:
            ok(f"definicion {fn}")
        else:
            err(f"FALTANTE definicion {fn}")

# ──────────────────────────────────────────────────────────────
print("\n[PASO 4] src/agent.py")
print("-" * 40)
agent_path = os.path.join(SRC_DIR, "agent.py")
src_agent = check_sintaxis(agent_path, "agent.py")
if src_agent:
    check_simbolo(src_agent, "create_react_agent",          "API prebuilt ReAct")
    check_simbolo(src_agent, "SistemaMemoriaDual",          "Memoria dual")
    check_simbolo(src_agent, "build_tools_desde_datos",     "Factory tools")
    check_simbolo(src_agent, "_SYSTEM_PROMPT",              "System prompt")
    check_simbolo(src_agent, "SOLO USES LAS 4 HERRAMIENTAS","Regla anti-aluc 1")
    check_simbolo(src_agent, "CITA SIEMPRE LA FUENTE",      "Regla anti-aluc 2")
    check_simbolo(src_agent, "No tengo inform",             "Regla sin inventar")
    check_simbolo(src_agent, "thread_id",                   "Multi-hilo")
    check_simbolo(src_agent, "logging",                     "Logging a archivo")
    fns = [n.name for n in ast.walk(ast.parse(src_agent))
           if isinstance(n, ast.FunctionDef)]
    for fn in ["construir_agente", "consultar_agente", "iniciar_consola"]:
        if fn in fns:
            ok(f"funcion {fn}()")
        else:
            err(f"FALTANTE funcion {fn}()")

# ──────────────────────────────────────────────────────────────
print("\n[PASO 5] src/demo.py")
print("-" * 40)
demo_path = os.path.join(SRC_DIR, "demo.py")
src_demo = check_sintaxis(demo_path, "demo.py")
if src_demo:
    # Los 5 escenarios presentes
    for escenario in [
        ("Multi-hop",           "Escenario 1 multi-hop"),
        ("Exactitud CSV",       "Escenario 2 exactitud CSV"),
        ("GDD + Balance",       "Escenario 3 multi-hop GDD+balance"),
        ("Anti-alucinacion",    "Escenario 4 anti-alucinacion"),
        ("Memoria Conversacional","Escenario 5 memoria"),
    ]:
        if escenario[0] in src_demo:
            ok(f"Presente: {escenario[1]}")
        else:
            err(f"FALTANTE: {escenario[1]}")
    check_simbolo(src_demo, "construir_agente",   "Uso de construir_agente")
    check_simbolo(src_demo, "consultar_agente",   "Uso de consultar_agente")
    check_simbolo(src_demo, "ejecutar_demo",      "Funcion principal")
    check_simbolo(src_demo, "thread_id",          "Soporte multi-hilo")
    check_simbolo(src_demo, "demo.log",           "Log de demo")
    fns = [n.name for n in ast.walk(ast.parse(src_demo))
           if isinstance(n, ast.FunctionDef)]
    for fn in ["ejecutar_demo"]:
        if fn in fns:
            ok(f"funcion {fn}()")
        else:
            err(f"FALTANTE funcion {fn}()")

# ──────────────────────────────────────────────────────────────
print("\n[ENV] Variables de entorno")
print("-" * 40)
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key and not api_key.startswith("sk-...") and len(api_key) > 10:
    ok("OPENAI_API_KEY configurada (la demo esta lista para ejecutar)")
else:
    warn("OPENAI_API_KEY no configurada — configura .env antes de la demo")

# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
total_checks = len(errores) + len(advertencias)
if errores:
    print(f"  RESULTADO: {len(errores)} ERROR(ES) — revisar antes de la demo")
    for e in errores:
        print(f"    - {e}")
else:
    print("  RESULTADO: TODOS LOS PASOS VERIFICADOS — 0 ERRORES")
    print(f"  {len(advertencias)} advertencia(s): {advertencias if advertencias else 'ninguna'}")
    print()
    print("  El sistema esta listo para ejecutar la demo.")
    print("  Pasos para correr la demo:")
    print("    1. Configura .env con tu OPENAI_API_KEY real")
    print("    2. venv\\Scripts\\activate")
    print("    3. python src\\demo.py")
print("=" * 60)
print()

sys.exit(1 if errores else 0)
