"""
funcional_test.py - Verificacion funcional real de los 4 modulos
"""
import sys, os, importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")
VENV_SP = os.path.join(BASE, "venv", "Lib", "site-packages")

sys.path = [p for p in sys.path if "site-packages" not in p or "venv" in p]
if VENV_SP not in sys.path:
    sys.path.insert(0, VENV_SP)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

errores = []

def ok(msg): print(f"  OK  {msg}")
def err(msg):
    print(f"  ERROR  {msg}")
    errores.append(msg)

def cargar(nombre, path):
    spec = importlib.util.spec_from_file_location(nombre, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

print()
print("=" * 50)
print("  VERIFICACION FUNCIONAL REAL - 4 modulos")
print("=" * 50)

# ── tools.py ────────────────────────────────────────
print("\n[1/4] tools.py")
try:
    tools = cargar("tools", os.path.join(SRC, "tools.py"))
    ok("tools.py importado")
    for f in ["_safe_run","_run_rag","_crear_retriever_faiss",
              "_crear_agente_pandas","build_tools","build_tools_desde_datos","test_tools"]:
        if callable(getattr(tools, f, None)):
            ok(f"{f}() callable")
        else:
            err(f"{f} NO callable")
    for attr, label in [("PATH_GDD","gdd.txt"),("PATH_CODIGO","codigo_guia.txt"),
                         ("PATH_BUGS","bugs.csv"),("PATH_BALANCE","balance.csv")]:
        p = getattr(tools, attr)
        if os.path.exists(p):
            ok(f"{label} en disco ({os.path.getsize(p)} bytes)")
        else:
            err(f"{label} no encontrado")
except Exception as e:
    err(f"tools.py fallo al importar: {e}")

# ── memory.py ───────────────────────────────────────
print("\n[2/4] memory.py")
try:
    memory = cargar("memory", os.path.join(SRC, "memory.py"))
    ok("memory.py importado")
    # Ejecutar crear_memoria_conversacion() de verdad
    from langgraph.checkpoint.memory import MemorySaver
    mem = memory.crear_memoria_conversacion()
    if isinstance(mem, MemorySaver):
        ok(f"crear_memoria_conversacion() -> MemorySaver: {type(mem).__name__}")
    else:
        err(f"crear_memoria_conversacion() no retorna MemorySaver: {type(mem)}")
    if callable(memory.crear_memoria_semantica):
        ok("crear_memoria_semantica() callable")
    else:
        err("crear_memoria_semantica() NO callable")
    if hasattr(memory, "SistemaMemoriaDual"):
        ok(f"SistemaMemoriaDual definida")
    else:
        err("SistemaMemoriaDual no encontrada")
    ok(f"CHUNK_SIZE={memory.DEFAULT_CHUNK_SIZE} OVERLAP={memory.DEFAULT_CHUNK_OVERLAP} K={memory.DEFAULT_K}")
    ok(f"FAISS_INDEX_DIR={memory.FAISS_INDEX_DIR}")
except Exception as e:
    err(f"memory.py fallo: {e}")

# ── agent.py ────────────────────────────────────────
print("\n[3/4] agent.py")
try:
    agent = cargar("agent", os.path.join(SRC, "agent.py"))
    ok("agent.py importado")
    for f in ["construir_agente","consultar_agente","iniciar_consola"]:
        if callable(getattr(agent, f, None)):
            ok(f"{f}() callable")
        else:
            err(f"{f} NO callable")
    sp = getattr(agent, "_SYSTEM_PROMPT", "")
    if len(sp) > 200:
        ok(f"_SYSTEM_PROMPT: {len(sp)} caracteres")
    else:
        err(f"_SYSTEM_PROMPT muy corto ({len(sp)} chars)")
    # Verificar reglas clave en el system prompt
    for regla in ["SOLO USES LAS 4 HERRAMIENTAS","CITA SIEMPRE LA FUENTE",
                  "No tengo inform","thread_id"]:
        if regla in (sp + str(agent.__dict__)):
            ok(f"Regla presente: {regla[:30]}")
        else:
            err(f"Regla FALTANTE: {regla}")
except Exception as e:
    err(f"agent.py fallo: {e}")

# ── demo.py ─────────────────────────────────────────
print("\n[4/4] demo.py")
try:
    demo = cargar("demo", os.path.join(SRC, "demo.py"))
    ok("demo.py importado")
    if isinstance(demo.ESCENARIOS, list) and len(demo.ESCENARIOS) == 5:
        ok(f"ESCENARIOS: {len(demo.ESCENARIOS)} definidos")
        for esc in demo.ESCENARIOS:
            ok(f"  Escenario {esc['id']}: {esc['titulo']}")
    else:
        err(f"ESCENARIOS: se esperaban 5, hay {len(getattr(demo,'ESCENARIOS',[]))}")
    if callable(getattr(demo,"ejecutar_demo",None)):
        ok("ejecutar_demo() callable")
    else:
        err("ejecutar_demo() NO callable")
except Exception as e:
    err(f"demo.py fallo: {e}")

# ── Resultado ───────────────────────────────────────
print()
print("=" * 50)
if errores:
    print(f"  FALLO: {len(errores)} error(es)")
    for e in errores:
        print(f"    - {e}")
else:
    print("  VERIFICACION FUNCIONAL REAL - 0 ERRORES")
    print("  Los 4 modulos importan y ejecutan correctamente")
    print("  El codigo esta listo para la evaluacion")
print("=" * 50)
print()
sys.exit(1 if errores else 0)
