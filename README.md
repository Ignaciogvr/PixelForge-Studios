# PixelForge Studios — EP2
## Agente de IA con Frameworks, Memoria y Planificación

**Asignatura:** Ingeniería de Soluciones con Inteligencia Artificial (ISY0101)  
**Estudiantes:** Ignacio Núñez · Rene Marambio  
**Evaluación:** Parcial 2 — 30% de la nota final

---

## ✅ PASO 1 COMPLETADO — Estructura del proyecto

Este README documenta exactamente qué se hizo en el Paso 1 y qué queda por hacer en los pasos siguientes.

### Auditoría del Paso 1 — qué se hizo y qué se corrigió

**Acciones realizadas:**
1. Estructura de carpetas creada: `data/`, `src/`, `faiss_index/`, `logs/`
2. Los 4 archivos de datos copiados de EP1 y verificados con sus tamaños reales
3. `.env.example` con variables separadas por proveedor (OpenAI / Groq) y parámetros de RAG configurables
4. `.gitignore` que protege `.env`, `faiss_index/`, `logs/`, `__pycache__/`, entornos virtuales e IDEs
5. `requirements.txt` con versiones probadas contra PyPI real (no versiones inventadas)
6. `src/__init__.py` que convierte `src/` en m# PixelForge Studios — Asistente Interno con IA

Asistente de inteligencia artificial desarrollado para centralizar y responder consultas sobre el desarrollo del videojuego *Aethelgard*. El sistema combina lectura de documentos, análisis de datos exactos y memoria conversacional mediante arquitectura RAG y LangGraph.

**Asignatura:** Ingeniería de Soluciones con Inteligencia Artificial (ISY0101)  
**Integrantes:** Ignacio Núñez · René Marambio  
**Evaluación:** Evaluación Parcial 2  

---

## 🚀 ¿Qué hace este proyecto?

El asistente permite al equipo de desarrollo realizar preguntas en lenguaje natural y obtener respuestas precisas con la fuente citada, consultando automáticamente 4 fuentes internas:

1. **Game Design Document (GDD):** Mecánicas, historia y diseño de enemigos.
2. **Guía de Código Unity:** Estándares de programación, patrones y arquitectura C#.
3. **Tickets de Jira (`bugs.csv`):** Estado, prioridad y encargados de fallas reportadas.
4. **Tabla de Balance (`balance.csv`):** Estadísticas exactas de personajes y enemigos (HP, daño, velocidad).

---

## ✨ Características Principales

* **Búsqueda Semántica (RAG):** Encuentra información relevante en documentos de texto usando índices vectoriales (FAISS) y embeddings locales.
* **Consulta Exacta de Datos:** Utiliza agentes de datos (Pandas) para filtrar y responder con exactitud sobre números e identificadores sin aproximaciones.
* **Memoria Conversacional Dual:** Mantiene el hilo de la conversación para responder a referencias como *"el bug que mencionamos antes"*.
* **Respuestas Anti-Alucinación:** Solo responde con información fundamentada en los archivos del proyecto y rechaza preguntas ajenas al estudio.

---

## 📁 Estructura del Repositorio

```text
PixelForge-Studios/
├── data/                  ← Documentos y planillas del estudio (GDD, código, CSVs)
├── src/                   ← Código fuente de la solución
│   ├── tools.py           ← Herramientas de consulta (RAG y Pandas)
│   ├── memory.py          ← Gestión de memoria conversacional y vectorial
│   ├── agent.py           ← Flujo principal del agente con LangGraph
│   └── demo.py            ← Script para ejecución de pruebas y demostración
├── .env.example           ← Plantilla para variables de entorno (API Keys)
├── requirements.txt       ← Librerías y dependencias necesarias
└── README.md              ← Documentación del proyectoódulo Python importable
7. `src/tools.py` con el wrapper `_safe_run()` ya implementado y las 4 tools pre-escritas como comentario guía para Paso 2
8. `src/memory.py` con tipado compatible con Python 3.8+, constantes de configuración y documentación de flujo completa
9. `src/agent.py` y `src/demo.py` como esqueletos con firmas y contratos definidos

**Correcciones realizadas durante auditoría:**
- `requirements.txt`: versión de `faiss-cpu` verificada contra PyPI (existe desde 1.7.4 hasta 1.11.0)
- `tools.py`: se agregó `from __future__ import annotations`, import correcto y `_safe_run()` funcional
- `memory.py`: tipado cambiado de `list[str]` a `List[str]` (compatible Python 3.8+), path de FAISS y constantes definidas
- Todos los archivos `.py` validados con `ast.parse()` — 0 errores de sintaxis

---

## ✅ PASO 2 COMPLETADO — `src/tools.py` — Las 4 herramientas

### Qué se implementó

| Bloque | Función | Propósito |
|--------|---------|----------|
| 1 | `_safe_run()` | Wrapper try/except diferenciado: `ValueError` (pandas ambiguo) vs `Exception` genérico |
| 2a | `_crear_retriever_faiss()` | `.txt` → chunking (500/100) → embeddings → FAISS → cadena LCEL |
| 2b | `_run_rag()` | Extrae el campo `"answer"` del dict LCEL |
| 2c | `_crear_agente_pandas()` | CSV → DataFrame → agente Python (`max_iterations=8`) |
| 3 | `build_tools()` | 4 Tools con descripciones `USAR CUANDO` / `NO usar para` |
| 4 | `build_tools_desde_datos()` | Factory: valida API key y archivos antes de llamar a OpenAI |
| 5 | `test_tools()` | Smoke test: llama `tool.func()` y verifica respuesta no vacía |

### Bugs reales encontrados y corregidos

| Bug | Evidencia | Corrección |
|-----|-----------|------------|
| `RetrievalQA` rota en LangChain 0.3.x (importa `pydantic_v1` eliminado) | `ImportError` real en traza de ejecución | Reemplazada por LCEL: `create_retrieval_chain` + `create_stuff_documents_chain` |
| Versiones incompatibles en el sistema global | `pip show` reveló 6 conflictos; `pydantic_v1` crash real | Creado `venv/` aislado con todas las dependencias |
| `requirements.txt` con versiones fijadas incompatibles | `pip install` retornó `ResolutionImpossible` | Reemplazado por rangos `>=` que pip resuelve solo |
| `_safe_run` sin diferenciación de errores | Una sola clausula `except` no da contexto al LLM | Separado en `ValueError` y `Exception` con mensajes distintos |

### Verificación del código

```
OK  Sintaxis válida (ast.parse)
OK  API moderna presente: create_retrieval_chain
OK  API moderna presente: create_stuff_documents_chain  
OK  API moderna presente: ChatPromptTemplate
OK  RetrievalQA deprecated: NO importada
OK  7/7 funciones definidas y callables
OK  4/4 archivos de datos en disco
```

**Nota sobre el ambiente:** El Python global del sistema tiene múltiples versiones de
LangChain mezcladas e incompatibles. El `venv/` fue creado para aislar el proyecto.
Para correr el código, activar el venv primero:
```bash
venv\Scripts\activate          # Windows
python src\tools.py            # test aislado
python verify_step2.py         # verificación completa
```

---

## 📁 Estructura del proyecto

```
PixelForge-EP2/
│
├── .env.example          ← Copiar como ".env" y poner las API keys reales
├── .env                  ← (NO subir a GitHub — está en .gitignore)
├── .gitignore            ← Protege .env, faiss_index/ y logs/
├── requirements.txt      ← Instalar con: pip install -r requirements.txt
│
├── data/                 ← Fuentes de datos internas de PixelForge (copiadas de EP1)
│   ├── gdd.txt           ← Game Design Document — mecánicas, lore, enemigos
│   ├── codigo_guia.txt   ← Guía de estándares de código Unity
│   ├── bugs.csv          ← Tickets de Jira (6 bugs simulados)
│   └── balance.csv       ← Stats de personajes y enemigos (HP, daño, velocidad...)
│
├── faiss_index/          ← Índice vectorial FAISS (se genera en Paso 3, no subir a GitHub)
├── logs/                 ← Logs del agente (se generan en Paso 4)
│
└── src/                  ← Código fuente del agente
    ├── __init__.py       ← Convierte src/ en módulo Python importable
    ├── tools.py          ← ✅ Las 4 herramientas del agente (Paso 2 COMPLETADO)
    ├── memory.py         ← Sistema de memoria dual (implementar en Paso 3)
    ├── agent.py          ← Agente principal con LangGraph (implementar en Paso 4)
    └── demo.py           ← Demo en vivo con 5 escenarios (implementar en Paso 5)
```

---

## ⚙️ Instalación (hacer UNA sola vez)

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/PixelForge-EP2.git
cd PixelForge-EP2
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar el template
copy .env.example .env    # Windows
# cp .env.example .env    # Mac/Linux

# Abrir .env y pegar las API keys reales
```

---

## 🗺️ Hoja de ruta — Los 8 pasos

| Paso | Archivo | Estado | Descripción |
|------|---------|--------|-------------|
| ✅ 1 | Estructura | **COMPLETADO** | Carpetas, datos, configs, esqueletos |
| ✅ 2 | `src/tools.py` | **COMPLETADO + AUDITADO** | 4 tools + factory + smoke test — verificado en venv limpio |
| ⬜ 3 | `src/memory.py` | Pendiente | Buffer Memory + FAISS vectorial |
| ⬜ 4 | `src/agent.py` | Pendiente | Agente ReAct con LangGraph |
| ⬜ 5 | `src/demo.py` | Pendiente | Demo con 5 escenarios robustos |
| ⬜ 6 | `README.md` | Pendiente | Diagrama de orquestación Mermaid |
| ⬜ 7 | Informe técnico | Pendiente | Word/PDF con todas las secciones |
| ⬜ 8 | Presentación | Pendiente | PPT + práctica de frases técnicas |

---

## 📦 Dependencias principales

| Librería | Para qué sirve |
|----------|---------------|
| `langchain` | Framework base del agente |
| `langgraph` | Agente como grafo de estados (ReAct moderno) |
| `langchain-openai` | LLM GPT + embeddings de OpenAI |
| `faiss-cpu` | Base de datos vectorial para RAG real |
| `pandas` | Consulta de datos estructurados (CSV) |
| `python-dotenv` | Carga de variables de entorno desde `.env` |

---

## ⚠️ Errores de EP1 que este proyecto corrige

| Error de EP1 | Solución en EP2 |
|-------------|----------------|
| Demo usaba context stuffing (falso RAG) | `memory.py` implementa FAISS real con embeddings |
| `initialize_agent` deprecado | `agent.py` usa LangGraph StateGraph moderno |
| Solo 1 tipo de memoria | 2 tipos explícitos: Buffer + FAISS semántica |
| Sin estrategia de planificación documentada | ReAct implementado y diagramado en Paso 6 |
| Informe con reflexiones vacías | Sección de reflexiones obligatoria en Paso 7 |
| Presentación sin lenguaje técnico | Frases técnicas preparadas de memoria en Paso 8 |
