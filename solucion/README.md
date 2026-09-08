# PixelForge Studios - Agente de Inteligencia Artificial (Evaluación Parcial 1)

Este repositorio contiene la implementación del proyecto del Agente de Inteligencia Artificial y el pipeline RAG para *PixelForge Studios*, diseñado para optimizar el flujo de trabajo del equipo de desarrollo, reduciendo los tiempos de búsqueda de información en la documentación interna (GDD, Guía de Estándares, Jira y Balance).

## 🛠️ Tecnologías Utilizadas

- **Python 3.10+**
- **LangChain**: Framework principal para orquestar los agentes y cadenas RAG.
- **FAISS**: Base de datos vectorial utilizada para la recuperación semántica (RAG) rápida y local.
- **OpenAI (GPT-4 / Embeddings)**: Motor LLM (requiere API Key).
- **Pandas**: Para el procesamiento avanzado de los archivos CSV (Bugs y Balance).

## 📂 Estructura del Proyecto

```text
solucion/
│
├── data/                       # Repositorio de Documentos Simulados (Fuentes de Datos)
│   ├── gdd.txt                 # Game Design Document (Lore, mecánicas, reglas)
│   ├── codigo_guia.txt         # Guía de estándares de arquitectura y código (Unity)
│   ├── bugs.csv                # Extracción simulada de tickets de Jira
│   └── balance.csv             # Tabla de atributos y balance de entidades
│
├── src/                        # Código Fuente del Agente
│   └── agent.py                # Script principal (Enrutador, RAG, Herramientas)
│
└── README.md                   # Instrucciones de ejecución
```

## ⚙️ Instrucciones de Instalación y Ejecución

Sigue estos pasos para probar la solución en tu entorno local.

### 1. Clonar o extraer el proyecto
Asegúrate de estar en el directorio raíz del proyecto (`solucion/`).

### 2. Instalar dependencias
Se recomienda el uso de un entorno virtual (`venv` o `conda`). Instala las librerías necesarias con:

```bash
pip install langchain langchain-openai langchain-community langchain-experimental faiss-cpu pandas
```

### 3. Configurar API Key de OpenAI
El agente utiliza los modelos de OpenAI tanto para procesar las consultas (GPT-4) como para crear los vectores de los documentos (OpenAIEmbeddings).

Puedes configurar tu llave de dos formas:

**Opción A (Terminal):**
- En Windows (PowerShell): `$env:OPENAI_API_KEY="TU_CLAVE"`
- En Mac/Linux: `export OPENAI_API_KEY="TU_CLAVE"`

**Opción B (En el código):**
- Abre `src/agent.py` y descomenta la línea 16. Reemplaza `'TU_API_KEY'` por tu clave real.

### 4. Ejecutar el Agente
Navega a la carpeta `src/` y corre el script:

```bash
cd src
python agent.py
```

Deberías ver cómo el sistema carga los documentos, los vectoriza y luego abre la "Terminal de Desarrollo" donde podrás interactuar con el agente.

## 🧪 Ejemplos de Pruebas (Preguntas sugeridas)

Una vez que la terminal esté corriendo, puedes hacerle preguntas complejas para validar el cruce de datos:

1. **Cruce Código + Bugs:** *"Hay un bug sobre un freeze del personaje saltando (PF-1001). Según la guía de código, ¿cómo debería solucionarse para que no pase este glitch?"*
2. **Consulta estructurada (CSV):** *"¿Quién tiene asignado el bug PF-1003 y qué prioridad tiene?"*
3. **Cruce GDD + CSV Balance:** *"¿Cuánto daño base hace un Golem de Basalto y cuál es la estrategia para derrotarlo según el GDD?"*
4. **Validación Anti-Alucinaciones:** *"¿Cuál es la historia del Rey Pálido en el mundo de Aethelgard?"* (Debería responder que no tiene esa información).
