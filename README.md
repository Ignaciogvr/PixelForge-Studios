# PixelForge Studios — Asistente Interno con IA

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
└── README.md              ← Documentación del proyecto
