"""
Script de verificacion del Paso 2 - tools.py
Ejecutar con: venv\\Scripts\\python.exe verify_step2.py
"""
import ast
import os
import sys

# Paths absolutos fijos — el script esta en la raiz de PixelForge-EP2/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../PixelForge-EP2
SRC_DIR  = os.path.join(BASE_DIR, "src")
VENV_SP  = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")
TOOLS_PATH = os.path.join(SRC_DIR, "tools.py")

# Limpiar sys.path: quitar site-packages del sistema global, dejar solo el venv
sys.path = [p for p in sys.path if "site-packages" not in p or "venv" in p]
if VENV_SP not in sys.path:
    sys.path.insert(0, VENV_SP)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

print("=" * 60)
print("  VERIFICACION PASO 2 - tools.py")
print("=" * 60)
print(f"Python:    {sys.executable}")
print(f"BASE_DIR:  {BASE_DIR}")
print(f"Venv SP:   {VENV_SP}")
print(f"tools.py:  {TOOLS_PATH}")
print(f"SP existe: {os.path.exists(VENV_SP)}")
print(f"tools existe: {os.path.exists(TOOLS_PATH)}")
print()

errores = []

# 1. Sintaxis
with open(TOOLS_PATH, encoding="utf-8") as f:
    src = f.read()
try:
    ast.parse(src)
    print("OK  Sintaxis valida")
except SyntaxError as e:
    print(f"ERROR  Sintaxis: {e}")
    errores.append("sintaxis")

# 2. APIs modernas presentes
for api in ["create_retrieval_chain", "create_stuff_documents_chain", "ChatPromptTemplate"]:
    if api in src:
        print(f"OK  API moderna: {api}")
    else:
        print(f"ERROR  API moderna FALTANTE: {api}")
        errores.append(f"api_{api}")

# 3. API deprecated ausente
if "from langchain.chains import RetrievalQA" not in src:
    print("OK  API deprecated ausente")
else:
    print("ERROR  RetrievalQA todavia importada")
    errores.append("RetrievalQA")

# 4. Imports criticos (paquetes del venv)
print()
for modulo, nombre in [
    ("pandas",              "pandas"),
    ("faiss",               "faiss-cpu"),
    ("langchain",           "langchain"),
    ("langchain_openai",    "langchain-openai"),
    ("langchain_community", "langchain-community"),
    ("langgraph",           "langgraph"),
]:
    try:
        m = __import__(modulo)
        ver = getattr(m, "__version__", "instalado")
        print(f"OK  {nombre}: {ver}")
    except ImportError as e:
        print(f"ERROR  {nombre}: {e}")
        errores.append(nombre)

# 5. Import real del modulo tools.py
print()
mod = None
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("tools", TOOLS_PATH)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("OK  tools.py importado como modulo")
except Exception as e:
    print(f"ERROR  tools.py import falló: {e}")
    errores.append("import_tools")

# 6. Funciones callables
if mod:
    for fn in ["_safe_run", "_run_rag", "_crear_retriever_faiss",
               "_crear_agente_pandas", "build_tools",
               "build_tools_desde_datos", "test_tools"]:
        obj = getattr(mod, fn, None)
        if callable(obj):
            print(f"OK  {fn}()")
        else:
            print(f"ERROR  {fn} no encontrada o no callable")
            errores.append(f"fn_{fn}")

# 7. Archivos de datos
print()
if mod:
    for attr, label in [("PATH_GDD", "gdd.txt"), ("PATH_CODIGO", "codigo_guia.txt"),
                         ("PATH_BUGS", "bugs.csv"), ("PATH_BALANCE", "balance.csv")]:
        p = getattr(mod, attr, None)
        if p and os.path.exists(p):
            print(f"OK  {label} ({os.path.getsize(p)} bytes)")
        else:
            print(f"ERROR  {label}: no encontrado en {p}")
            errores.append(f"file_{label}")

# Resumen
print()
print("=" * 60)
if errores:
    print(f"FALLO: {len(errores)} error(es): {errores}")
    sys.exit(1)
else:
    print("PASO 2 VERIFICADO - 0 ERRORES")
    print("7/7 funciones | 4/4 archivos | API LangChain 0.3.x | OK")
    sys.exit(0)
print("=" * 60)
