# Evaluación Parcial N°1: Diseño de Solución con LLM y RAG
**Caso Organizacional:** PixelForge Studios  
**Estudiantes:** Ignacio Núñez, Rene Marambio  
**Asignatura:** Ingeniería de Soluciones con IA (ISY0101)  

---

## 1. Análisis del Caso Organizacional (IE1)
**Organización:** PixelForge Studios (Estudio de desarrollo de videojuegos, 120 empleados).  
**Desafío Principal:** Pérdida de tiempo productivo (30-40 minutos diarios por desarrollador) debido a la búsqueda ineficiente de información en fuentes desconectadas. Los programadores, diseñadores y testers deben cruzar manualmente datos entre el Game Design Document (GDD), la Guía de Estándares de Código, los reportes de bugs en Jira y los balances estadísticos.  
**Requerimientos Específicos:** 
- Disminuir el tiempo de consulta a segundos mediante un sistema centralizado.
- Garantizar **0% de alucinaciones**; el sistema debe basarse estrictamente en la documentación interna.
- Proveer trazabilidad (citar la fuente en cada respuesta).
- Capacidad de enrutamiento: decidir autónomamente si una pregunta técnica requiere consultar el GDD, el CSV de Jira o la Guía de Código (o una combinación de estos).

---

## 2. Formulación y Justificación de Prompts (IE2)
Para satisfacer las estrictas restricciones organizacionales, se diseñó un *System Prompt* robusto para el Agente Enrutador, priorizando las directrices de trazabilidad y limitación (Zero-Shot ReAct).

**Prompt Implementado:**
> "Eres el asistente técnico de Inteligencia Artificial para PixelForge Studios. Tu objetivo es ayudar a programadores, diseñadores y testers a resolver dudas operativas combinando información del GDD, Código, Bugs y Balance.
> 
> REGLAS ESTRICTAS DE RESPUESTA:
> 1. CERO ALUCINACIONES: Si la respuesta no está en tus herramientas, debes decir exactamente: 'La información solicitada no se encuentra en la documentación actual del proyecto.'
> 2. TRAZABILIDAD: Siempre cita la fuente de tu respuesta indicando qué documento o base de datos usaste (ej: 'Según el GDD...').
> 3. ESTRUCTURA: Responde de forma técnica, directa, y usando viñetas.
> 4. SÍNTESIS: Si te preguntan por un bug que involucra diseño y código, debes usar ambas herramientas [...] y combinar la respuesta."

**Justificación:** 
- La **regla 1** bloquea de inmediato la tendencia de los LLM (como GPT-4) a rellenar vacíos de información, protegiendo al estudio de mecánicas falsas generadas por IA. 
- La **regla 2** resuelve el requerimiento de trazabilidad organizacional.
- La **regla 4** induce el comportamiento de análisis cruzado (Multi-hop QA), indispensable para solucionar bugs que mezclan diseño (GDD) y programación (Guía de Código).

---

## 3. Diseño e Implementación de Pipeline RAG (IE3)
El flujo de información se estructuró separando el procesamiento de datos no estructurados y datos estructurados:

1. **Datos No Estructurados (GDD y Guía de Código - Texto):**
   - **Ingesta y Fragmentación (Chunking):** Se utiliza `RecursiveCharacterTextSplitter` (chunks de 1000 caracteres, overlap de 150) para preservar el contexto semántico sin exceder el límite de tokens del LLM.
   - **Vectorización:** Los fragmentos se convierten a vectores mediante `OpenAIEmbeddings` y se almacenan en la base de datos vectorial local **FAISS**.
   - **Recuperación:** Cadenas `RetrievalQA` extraen los 3 nodos más relevantes (`k=3`) frente a una consulta.
2. **Datos Estructurados (Jira Bugs y Balance - CSV):**
   - En lugar de vectorizarlos (lo cual merma la exactitud de los datos tabulares), se ingestan como DataFrames de Pandas.
   - Se instancian agentes especializados (`create_pandas_dataframe_agent`) que actúan como sub-herramientas, capaces de ejecutar lógica de filtrado exacto sobre columnas y filas.

---

## 4. Arquitectura de la Solución (IE4, IE7)
La solución sigue un patrón de **Agente con Planificación Reactiva (ReAct)**, integrando memoria y herramientas disjuntas.

```mermaid
graph TD
    User([Usuario / Desarrollador]) -->|Consulta (Natural Language)| Agent[Agente Principal ReAct]
    Agent --> |Prompt & Context| LLM((GPT-4))
    Agent <--> Mem[(Buffer Memory)]
    
    Agent -->|Routing / Decision| Tools{Selector de Herramientas}
    
    Tools -->|Texto Libre| T1[Tool: Base GDD]
    Tools -->|Texto Libre| T2[Tool: Base Código]
    Tools -->|Datos Tabulares| T3[Tool: Bugs Jira]
    Tools -->|Datos Tabulares| T4[Tool: Balance]
    
    T1 --> RAG1[FAISS Retriever]
    T2 --> RAG2[FAISS Retriever]
    
    RAG1 -.-> Embeddings[OpenAI Embeddings]
    RAG2 -.-> Embeddings
    
    T3 --> Pandas1[Pandas DataFrame Agent]
    T4 --> Pandas2[Pandas DataFrame Agent]
    
    RAG1 --> |Docs| Agent
    RAG2 --> |Docs| Agent
    Pandas1 --> |Data| Agent
    Pandas2 --> |Data| Agent
    
    Agent -->|Respuesta Sintetizada y Citada| User
```
*Figura 1: Diagrama de arquitectura integrando flujos RAG y herramientas estructuradas.*

---

## 5. Fundamentación de Decisiones y Documentación Técnica (IE5, IE8)
Las decisiones clave de diseño responden directamente a los objetivos de PixelForge:
- **Elección del Motor LLM (GPT-4 con Temp=0):** Para un sistema empresarial de soporte interno, la creatividad no es deseada; la temperatura en 0 fuerza respuestas deterministas y analíticas.
- **División de Herramientas (Enrutador vs RAG unificado):** En lugar de meter todos los documentos en una sola base vectorial, se crearon herramientas separadas. Esto permite al agente de razonamiento discriminar lógicamente dónde buscar (ej: si le preguntan por HP, va directo a Pandas en lugar de hacer una búsqueda semántica ineficiente).
- **Uso de FAISS:** Al ser un estudio de videojuegos que maneja propiedad intelectual (GDD), FAISS permite alojar los vectores localmente en memoria sin depender de servicios Cloud persistentes que comprometan la confidencialidad a largo plazo.

---

## 6. Conclusiones y Reflexiones Personales (IE9)

### Declaración de Uso Ético de IA
*Durante la elaboración de este proyecto, se utilizó asistencia de Inteligencia Artificial (LLMs) con fines de depuración de código en Python, estructuración de archivos de prueba (Mock Data) y generación del formato inicial Markdown/Mermaid. Todas las decisiones arquitectónicas, análisis técnicos y justificaciones contenidas en este informe son de autoría intelectual exclusiva del equipo, siendo validadas en su totalidad respecto a los requerimientos del caso.*

### Reflexión Individual: Ignacio Núñez
[Espacio para que Ignacio redacte su reflexión sobre su aprendizaje, contribución al proyecto, y los desafíos enfrentados con la tecnología de agentes].

### Reflexión Individual: Rene Marambio
[Espacio para que Rene redacte su reflexión sobre su aprendizaje, contribución al diseño de arquitectura, y cómo visualiza la aplicabilidad de estas herramientas en el futuro].

---
**Referencias Bibliográficas**
- LangChain Documentation. (2024). *Agents and Toolkits*. Extraído de https://python.langchain.com/
- PixelForge Studios (Caso Simulado). Documentos internos: GDD v2.1 y Guías de Arquitectura.
