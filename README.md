# 🎮 PixelForge Studios - Asistente IA

Proyecto de inteligencia artificial para ayudar al equipo de desarrollo del videojuego **Aethelgard: The Fractured Realm**. El asistente responde preguntas en español sobre documentación, bugs y balance del juego.

**Asignatura:** ISY0101 - Ingeniería de Soluciones con IA  
**Integrantes:** Ignacio Núñez · René Marambio  
**Evaluación:** EP2 + EP3

---

## 🚀 ¿Qué hace?

El asistente responde preguntas consultando automáticamente **4 fuentes**:

1. **📖 Game Design Document (GDD)** - Mecánicas, historia, enemigos
2. **💻 Guía de Código** - Estándares de programación
3. **🐛 Tickets de Jira** - Bugs reportados
4. **📊 Balance** - Estadísticas del juego (HP, daño, velocidad)

**Ejemplo:**
```
Usuario: "¿Cómo funciona el parry y cuántos HP tiene el Golem?"

Agente:  "El parry se activa bloqueando justo antes del impacto, 
         con ventana de 0.15 segundos [GDD]. El Golem de Basalto 
         tiene 1500 HP [BALANCE]."
```

---

## ✨ Características

- ✅ Búsqueda semántica en documentos (RAG con FAISS)
- ✅ Consultas exactas en CSVs (Pandas)
- ✅ Memoria conversacional
- ✅ Solo responde con información verificada
- ✅ **Sistema de observabilidad (EP3)** con métricas y dashboard

---

## 📊 Sistema de Observabilidad (EP3)

Dashboard con métricas en tiempo real:

- **Métricas:** Precisión, consistencia, latencia, errores
- **Gráficos:** Visualización con Plotly
- **Análisis de logs:** Detección automática de errores
- **Exportación:** JSON para análisis

**Ver dashboard:**
```powershell
streamlit run src\dashboard.py
```

---

## 🛠️ Instalación

### Requisitos
- Python 3.12+
- API Key de **Groq (gratis)** → [console.groq.com](https://console.groq.com)

### Pasos

**1. Clonar y crear entorno:**
```powershell
git clone <repo-url>
cd PixelForge-Studios-ep2

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Configurar API Key:**
```powershell
Copy-Item .env.example .env
# Editar .env y poner tu GROQ_API_KEY
```

**3. Verificar:**
```powershell
python verify_all.py
```

---

## 🎯 Uso

### Demo con 5 escenarios
```powershell
python src\demo.py
```

### Dashboard de métricas
```powershell
# 1. Ejecutar demo primero para generar métricas
python src\demo.py

# 2. Abrir dashboard
streamlit run src\dashboard.py
```

### Chat interactivo
```powershell
python src\agent.py
```

Comandos: `salir`, `/nueva`, `/stats`

---

## 📁 Estructura

```
PixelForge-Studios-ep2/
├── data/              # Documentos y CSVs
├── src/
│   ├── agent.py       # Agente principal
│   ├── tools.py       # 4 herramientas
│   ├── demo.py        # 5 escenarios
│   ├── monitoring.py  # Sistema de observabilidad (EP3)
│   └── dashboard.py   # Dashboard visual (EP3)
├── logs/              # Métricas generadas
├── .env.example
├── requirements.txt
└── README.md
```
---

## 🏗️ Tecnologías

- **LangChain / LangGraph** - Framework para agentes
- **FAISS** - Búsqueda vectorial
- **Pandas** - Análisis de datos
- **Streamlit + Plotly** - Dashboard (EP3)
- **Groq** - LLM gratuito (Llama 3.3 70B)

---

## 🧪 Testing

**Verificar todo:**
```powershell
python verify_all.py
```

**Test funcional:**
```powershell
python funcional_test.py
```

**Test de observabilidad:**
```powershell
python test_observabilidad.py
```

---

## 🐛 Problemas Comunes

**"GROQ_API_KEY no configurada"**
```powershell
# Verificar .env
notepad .env

# Debe tener:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_tu_key
```

**Dashboard sin datos**
```powershell
# Ejecutar demo primero:
python src\demo.py

# Luego abrir dashboard:
streamlit run src\dashboard.py
```

---

## 📚 Evaluaciones

### EP2 - Agente de IA
✅ 4 herramientas (RAG + Pandas)  
✅ Memoria conversacional  
✅ Agente ReAct  
✅ Demo con 5 escenarios

### EP3 - Observabilidad
✅ Métricas de calidad (precisión, consistencia, errores)  
✅ Métricas de rendimiento (latencia, CPU, RAM)  
✅ Análisis de logs  
✅ Dashboard interactivo

---

## 📞 Contacto

Para consultas sobre el proyecto, contactar a través del repositorio.

---

**Última actualización:** 25-11-2026  
**Versión:** 2.0 (con Observabilidad)
