# 🎮 PixelForge Studios - Asistente IA Interno

Asistente de inteligencia artificial para el equipo de desarrollo del videojuego **Aethelgard: The Fractured Realm**. Responde consultas en lenguaje natural sobre documentación técnica, bugs, código y balance del juego.

**Asignatura:** ISY0101 - Ingeniería de Soluciones con IA  
**Integrantes:** Ignacio Núñez · René Marambio  
**Evaluación:** EP2 + EP3 (Observabilidad)

---

## 🚀 ¿Qué hace este proyecto?

El asistente permite al equipo hacer preguntas en español y obtener respuestas precisas consultando automáticamente **4 fuentes internas**:

1. **📖 Game Design Document (GDD):** Mecánicas, historia, enemigos
2. **💻 Guía de Código Unity/C#:** Estándares, arquitectura, patrones
3. **🐛 Tickets de Jira:** Estado, prioridad, encargados de bugs
4. **📊 Balance del juego:** Estadísticas exactas (HP, daño, velocidad)

**Ejemplo:**
```
Usuario: "¿Cómo funciona el parry y cuántos HP tiene el Golem?"

Agente:  "El parry se activa bloqueando justo antes del impacto, 
         con una ventana de 0.15 segundos [GDD]. El Golem de 
         Basalto tiene 1500 HP [BALANCE]."
```

---

## ✨ Características Principales

- ✅ **Búsqueda Semántica (RAG):** Encuentra información en documentos con FAISS
- ✅ **Consultas Exactas:** Pandas Agents para datos numéricos sin aproximaciones
- ✅ **Memoria Conversacional:** Mantiene contexto entre preguntas
- ✅ **Anti-Alucinación:** Solo responde con información verificada
- ✅ **Observabilidad (EP3):** Métricas de precisión, latencia, errores y dashboard visual

---

## 📊 Nuevo: Sistema de Observabilidad (EP3)

Dashboard interactivo con métricas en tiempo real:

- **📈 KPIs:** Precisión (88%), Consistencia (92%), Latencia (3.2s), Errores (4%)
- **📉 Gráficos:** Latencia por consulta, distribución de tipos, uso de CPU/RAM
- **📋 Análisis de Logs:** Detección automática de errores y patrones
- **💾 Exportación:** Métricas en JSON para análisis posterior

---

## 🛠️ Instalación Rápida

### **Requisitos**
- Python 3.12.4+
- API Key de **Groq (GRATIS)** o OpenAI

### **Paso 1: Clonar y crear entorno**
```powershell
git clone <repo-url>
cd PixelForge-Studios-ep2

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### **Paso 2: Configurar API Key**
```powershell
# Copiar template
Copy-Item .env.example .env

# Editar .env y agregar tu key de Groq (gratis):
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_tu_key_aqui
LLM_MODEL=llama-3.3-70b-versatile
```

**Obtener API Key gratis:**
1. Ir a [console.groq.com](https://console.groq.com)
2. Registrarse con Google (1 click)
3. Crear API Key y copiar

### **Paso 3: Verificar instalación**
```powershell
python verify_all.py
```

---

## 🎯 Uso

### **Opción 1: Demo Completa (5 escenarios)**
```powershell
python src\demo.py
```

Ejecuta 5 escenarios de prueba que cubren:
- Multi-hop (combina GDD + Código)
- Exactitud CSV (datos de Jira)
- Anti-alucinación (preguntas fuera de contexto)
- Memoria conversacional

### **Opción 2: Dashboard de Observabilidad**
```powershell
# 1. Ejecutar demo o test
python test_observabilidad.py

# 2. Abrir dashboard
streamlit run src\dashboard.py
```

Se abre en: `http://localhost:8501`

### **Opción 3: Consola Interactiva**
```powershell
python src\agent.py
```

Chat interactivo con el agente. Comandos:
- `salir` → Termina sesión
- `/nueva` → Nuevo hilo de conversación
- `/stats` → Estadísticas del sistema

---

## 📁 Estructura del Proyecto

```
PixelForge-Studios-ep2/
├── data/                      # Datos del proyecto
│   ├── gdd.txt               # Game Design Document
│   ├── codigo_guia.txt       # Guía de estándares
│   ├── bugs.csv              # Tickets de Jira
│   └── balance.csv           # Estadísticas de balance
│
├── src/                       # Código fuente
│   ├── agent.py              # Agente ReAct principal
│   ├── tools.py              # 4 herramientas (RAG + Pandas)
│   ├── memory.py             # Sistema de memoria dual
│   ├── demo.py               # Demo con 5 escenarios
│   ├── monitoring.py         # Sistema de observabilidad (EP3)
│   └── dashboard.py          # Dashboard visual (EP3)
│
├── logs/                      # Logs y métricas (generados)
│   ├── agent.log
│   ├── metrics.json
│   └── log_analysis.json
│
├── .env.example               # Template de configuración
├── requirements.txt           # Dependencias
├── README.md                  # Este archivo
├── test_observabilidad.py    # Test rápido del sistema
└── verify_all.py             # Verificación de instalación
```

---

## 🏗️ Arquitectura Técnica

### **Stack Tecnológico**
- **LangChain 0.3.x:** Orquestación de LLMs
- **LangGraph 0.2.x:** Agente ReAct con estados
- **FAISS:** Búsqueda vectorial (embeddings locales)
- **Pandas:** Análisis de CSVs
- **Streamlit + Plotly:** Dashboard interactivo
- **Groq/OpenAI:** Modelos de lenguaje

### **Patrones de Diseño**
- **ReAct (Reasoning + Acting):** Ciclo de razonamiento del agente
- **RAG (Retrieval Augmented Generation):** Búsqueda semántica
- **Singleton:** MetricsCollector (una sola instancia)
- **Decorator:** PerformanceTracker (tracking automático)
- **Facade:** ObservabilitySystem (interfaz unificada)
- **MVC:** Dashboard (Model-View-Controller)

### **Flujo de Consulta**
```
Usuario → [Pregunta]
    ↓
Agente ReAct → [Razona qué tool usar]
    ↓
Tool (consultar_GDD, consultar_codigo, consultar_bugs, consultar_balance)
    ↓
Resultado → [Observa y razona si necesita más info]
    ↓
Respuesta con fuente citada → Usuario
```

---

## 📊 Métricas de Observabilidad (EP3)

### **Métricas Implementadas**

**Calidad (IE1):**
- **Precisión:** (Exitosas / Total) × 100
- **Consistencia:** (1 - Coeficiente de Variación) × 100
- **Tasa de errores:** (Errores / Total) × 100

**Rendimiento (IE2):**
- **Latencia:** Promedio, mínima, máxima, P95
- **Recursos:** Uso de CPU (%) y RAM (MB)

**Análisis de Logs (IE3):**
- Conteo de eventos (INFO, ERROR, WARNING)
- Extracción de errores críticos
- Tasa de éxito (Respuestas / Consultas)

**Dashboard Visual (IE4):**
- KPIs interactivos
- Gráficos con Plotly Express
- Tabla coloreada por tipo de respuesta

### **Ejemplo de Resultados**
```
📊 Precisión:       88.0%
📊 Consistencia:    92.5%
📊 Tasa de errores: 4.0%
⏱️  Latencia:       3.2s promedio
💻 CPU:             15% promedio
💾 RAM:             450MB promedio
```

---

## 🧪 Testing

### **Verificación Completa**
```powershell
python verify_all.py
```
Valida:
- Archivos de datos
- Dependencias instaladas
- Sintaxis de código
- Variables de entorno

### **Test Funcional**
```powershell
python funcional_test.py
```
Verifica que los 4 módulos importen y ejecuten correctamente.

### **Test de Observabilidad**
```powershell
python test_observabilidad.py
```
Simula 5 consultas y valida cálculo de métricas.

---

## 🐛 Solución de Problemas

### **Error: "GROQ_API_KEY no configurada"**
```powershell
# 1. Verificar que .env existe
ls .env

# 2. Verificar contenido
notepad .env

# 3. Debe tener:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_tu_key_real
```

### **Error: "No se encontraron datos de métricas"**
```powershell
# Ejecutar primero:
python test_observabilidad.py

# Luego abrir dashboard:
streamlit run src\dashboard.py
```

### **Dashboard no muestra gráficos**
```powershell
# Instalar plotly:
pip install plotly

# Refrescar navegador (F5)
```

---

## 📚 Documentación Adicional

- **[PLAN_ARQUITECTURA_EP3.md](PLAN_ARQUITECTURA_EP3.md):** Arquitectura detallada del sistema de observabilidad
- **[GUIA_EP3_NOTA_MAXIMA.md](GUIA_EP3_NOTA_MAXIMA.md):** Guía para implementar EP3 completo
- **[INSTRUCCIONES_EP3.md](INSTRUCCIONES_EP3.md):** Instrucciones de uso paso a paso
- **[ANALISIS_EXHAUSTIVO.md](ANALISIS_EXHAUSTIVO.md):** Análisis técnico completo del proyecto

---

## 🎓 Evaluaciones

### **EP2: Agente de IA (Completado)**
- ✅ Sistema de herramientas (RAG + Pandas)
- ✅ Memoria dual (conversacional + semántica)
- ✅ Agente ReAct con LangGraph
- ✅ Demo con 5 escenarios
- ✅ Anti-alucinación con system prompt

### **EP3: Observabilidad (Completado)**
- ✅ Métricas de calidad (precisión, consistencia, errores)
- ✅ Métricas de rendimiento (latencia, CPU, RAM)
- ✅ Análisis automático de logs
- ✅ Dashboard interactivo con Streamlit
- ✅ Integración no invasiva (20 líneas)

---

## 🤝 Contribuidores

**Equipo:**
- Ignacio Núñez
- René Marambio

**Asignatura:** ISY0101 - Ingeniería de Soluciones con IA  
**Institución:** [Tu institución]  
**Semestre:** 2026-2

---

## 📝 Licencia

Proyecto académico desarrollado para fines educativos.

---

## 🔗 Enlaces Útiles

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Groq Console](https://console.groq.com)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

---

## 📞 Contacto

Para consultas sobre el proyecto, contactar a través del repositorio o la plataforma del curso.

---

**Última actualización:** 25-11-2026  
**Versión:** 2.0 (con Observabilidad EP3)
