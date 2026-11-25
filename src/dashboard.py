"""
dashboard.py - Dashboard Visual de Observabilidad
==================================================

Interfaz visual interactiva con Streamlit para visualizar
métricas del agente PixelForge EP2.

Patrón de diseño: MVC (Model-View-Controller)
- Model: Carga y procesa datos JSON
- View: Renderiza componentes visuales
- Controller: Coordina modelo y vista

Tecnologías:
- Streamlit: Framework web
- Plotly Express: Gráficos interactivos
- Pandas: Procesamiento de datos

Autor: [Tu nombre]
Fecha: 2026-11-25
Evaluación: EP3 - Dashboard Visual (IE4)
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, Any

# Solo importar plotly si está disponible
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly no disponible. Instala con: pip install plotly")


# ================================================================
# MODELO (Model) - Carga y procesamiento de datos
# ================================================================

class DashboardModel:
    """
    Modelo del dashboard: carga y procesa datos de métricas.
    
    Responsabilidades:
    - Cargar archivos JSON
    - Procesar datos para visualización
    - Validar integridad de datos
    """
    
    @staticmethod
    def cargar_metricas() -> Dict[str, Any]:
        """
        Carga el archivo de métricas JSON.
        
        Returns:
            dict: Datos de métricas o dict vacío si falla
        """
        path = "logs/metrics.json"
        
        if not os.path.exists(path):
            return {
                "error": f"Archivo no encontrado: {path}",
                "resumen": {},
                "historial": []
            }
        
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {
                "error": f"Error al cargar {path}: {e}",
                "resumen": {},
                "historial": []
            }
    
    @staticmethod
    def cargar_analisis_logs() -> Dict[str, Any]:
        """Carga el análisis de logs si existe."""
        path = "logs/log_analysis.json"
        
        if not os.path.exists(path):
            return {"error": "Análisis de logs no disponible"}
        
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"error": "Error al cargar análisis de logs"}
    
    @staticmethod
    def cargar_historial() -> pd.DataFrame:
        """
        Carga el historial de consultas como DataFrame.
        
        Returns:
            DataFrame: Historial de consultas procesado
        """
        metricas = DashboardModel.cargar_metricas()
        historial = metricas.get("historial", [])
        
        if not historial:
            # Retornar DataFrame vacío con columnas esperadas
            return pd.DataFrame(columns=[
                "tipo", "latencia", "tools_usadas", 
                "cpu_percent", "ram_mb", "timestamp"
            ])
        
        df = pd.DataFrame(historial)
        
        # Agregar columna de índice de consulta
        df["consulta_num"] = range(1, len(df) + 1)
        
        return df
    
    @staticmethod
    def validar_datos() -> bool:
        """Valida que existan los archivos necesarios."""
        return os.path.exists("logs/metrics.json")


# ================================================================
# VISTA (View) - Componentes visuales
# ================================================================

class DashboardView:
    """
    Vista del dashboard: renderiza componentes visuales.
    
    Responsabilidades:
    - Configurar página de Streamlit
    - Renderizar KPIs
    - Renderizar gráficos interactivos
    - Renderizar tablas
    """
    
    @staticmethod
    def configurar_pagina():
        """Configura la página de Streamlit."""
        st.set_page_config(
            page_title="PixelForge Observability",
            page_icon="🎮",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @staticmethod
    def render_header():
        """Renderiza el encabezado del dashboard."""
        st.title("🎮 Dashboard de Observabilidad")
        st.markdown("**Proyecto:** PixelForge Studios EP2 - Asistente de IA Interno")
        st.markdown("**Evaluación:** EP3 - Implementación de Observabilidad")
        st.divider()
    
    @staticmethod
    def render_kpis(metricas: Dict[str, Any]):
        """
        Renderiza los KPIs principales en tarjetas.
        
        Args:
            metricas: Diccionario con resumen de métricas
        """
        st.subheader("📊 Indicadores Clave de Desempeño (KPIs)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # KPI 1: Precisión
        precision = metricas.get("precision", 0)
        delta_precision = "↑ Excelente" if precision > 80 else "↓ Mejorar"
        col1.metric(
            label="Precisión",
            value=f"{precision:.1f}%",
            delta=delta_precision,
            help="Porcentaje de respuestas exitosas del agente"
        )
        
        # KPI 2: Consistencia
        consistencia = metricas.get("consistencia", 0)
        delta_consistencia = "↑ Estable" if consistencia > 70 else "↓ Variable"
        col2.metric(
            label="Consistencia",
            value=f"{consistencia:.1f}%",
            delta=delta_consistencia,
            help="Estabilidad del tiempo de respuesta (1 - CV)"
        )
        
        # KPI 3: Latencia Promedio
        latencia = metricas.get("latencia_promedio", 0)
        delta_latencia = "↑ Rápido" if latencia < 3 else "↓ Lento"
        col3.metric(
            label="Latencia Promedio",
            value=f"{latencia:.2f}s",
            delta=delta_latencia,
            help="Tiempo promedio de respuesta del agente"
        )
        
        # KPI 4: Tasa de Errores
        errores = metricas.get("tasa_errores", 0)
        delta_errores = "↑ Crítico" if errores > 10 else "↓ Normal"
        col4.metric(
            label="Tasa de Errores",
            value=f"{errores:.1f}%",
            delta=delta_errores,
            delta_color="inverse",
            help="Porcentaje de respuestas con error"
        )
    
    @staticmethod
    def render_grafico_latencia(df: pd.DataFrame):
        """Renderiza gráfico de línea con latencias."""
        st.subheader("⏱️ Latencia por Consulta")
        
        if df.empty:
            st.info("No hay datos de latencia disponibles")
            return
        
        if PLOTLY_AVAILABLE:
            fig = px.line(
                df,
                x="consulta_num",
                y="latencia",
                markers=True,
                title="Tiempo de respuesta del agente"
            )
            fig.update_layout(
                xaxis_title="Consulta #",
                yaxis_title="Latencia (segundos)",
                hovermode="x unified"
            )
            fig.update_traces(
                line_color="#1f77b4",
                marker=dict(size=8)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback: usar line_chart de Streamlit
            st.line_chart(df.set_index("consulta_num")["latencia"])
    
    @staticmethod
    def render_distribucion_tipos(df: pd.DataFrame):
        """Renderiza gráfico de pie con distribución de tipos."""
        st.subheader("📈 Distribución de Tipos de Respuesta")
        
        if df.empty:
            st.info("No hay datos de tipos disponibles")
            return
        
        tipos = df["tipo"].value_counts()
        
        if PLOTLY_AVAILABLE:
            fig = px.pie(
                values=tipos.values,
                names=tipos.index,
                title="Proporción de respuestas por tipo",
                color_discrete_map={
                    "exitosa": "#2ca02c",
                    "sin_info": "#ff7f0e",
                    "error": "#d62728"
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback: mostrar como tabla
            st.bar_chart(tipos)
    
    @staticmethod
    def render_recursos_sistema(df: pd.DataFrame):
        """Renderiza gráficos de uso de CPU y RAM."""
        st.subheader("💻 Uso de Recursos del Sistema")
        
        if df.empty or "cpu_percent" not in df.columns:
            st.info("No hay datos de recursos disponibles")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**CPU (%)**")
            if PLOTLY_AVAILABLE:
                fig = px.line(df, x="consulta_num", y="cpu_percent", markers=True)
                fig.update_layout(yaxis_title="CPU %", xaxis_title="Consulta #")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.line_chart(df.set_index("consulta_num")["cpu_percent"])
        
        with col2:
            st.markdown("**RAM (MB)**")
            if PLOTLY_AVAILABLE:
                fig = px.line(df, x="consulta_num", y="ram_mb", markers=True)
                fig.update_layout(yaxis_title="RAM (MB)", xaxis_title="Consulta #")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.line_chart(df.set_index("consulta_num")["ram_mb"])
    
    @staticmethod
    def render_tabla_consultas(df: pd.DataFrame):
        """Renderiza tabla interactiva con historial de consultas."""
        st.subheader("🔍 Historial de Consultas")
        
        if df.empty:
            st.info("No hay consultas registradas")
            return
        
        # Seleccionar columnas relevantes
        columnas_display = ["consulta_num", "tipo", "latencia", "cpu_percent", "ram_mb"]
        columnas_disponibles = [col for col in columnas_display if col in df.columns]
        
        df_display = df[columnas_disponibles].copy()
        
        # Renombrar columnas para mejor presentación
        nombres_columnas = {
            "consulta_num": "# Consulta",
            "tipo": "Tipo",
            "latencia": "Latencia (s)",
            "cpu_percent": "CPU %",
            "ram_mb": "RAM (MB)"
        }
        df_display = df_display.rename(columns=nombres_columnas)
        
        # Aplicar formato condicional con estilo
        def highlight_errors(row):
            if row.get("Tipo") == "error":
                return ["background-color: #ffcccc"] * len(row)
            elif row.get("Tipo") == "exitosa":
                return ["background-color: #ccffcc"] * len(row)
            else:
                return [""] * len(row)
        
        st.dataframe(
            df_display.style.apply(highlight_errors, axis=1),
            use_container_width=True,
            height=400
        )
    
    @staticmethod
    def render_analisis_logs(analisis: Dict[str, Any]):
        """Renderiza resumen del análisis de logs."""
        st.subheader("📋 Análisis de Logs")
        
        if "error" in analisis:
            st.warning(analisis["error"])
            return
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric(
            "Total Líneas",
            analisis.get("total_lineas", 0),
            help="Líneas totales en agent.log"
        )
        
        eventos = analisis.get("eventos", {})
        col2.metric(
            "Errores Detectados",
            eventos.get("errores", 0),
            delta="⚠️ Revisar" if eventos.get("errores", 0) > 0 else "✅ OK",
            help="Errores encontrados en los logs"
        )
        
        col3.metric(
            "Tasa de Éxito",
            f"{analisis.get('tasa_exito', 0):.1f}%",
            help="Respuestas / Consultas"
        )
        
        # Mostrar errores críticos si existen
        errores = analisis.get("errores_criticos", [])
        if errores:
            with st.expander(f"⚠️ Ver {len(errores)} errores críticos"):
                for i, error in enumerate(errores[:5], 1):  # Mostrar primeros 5
                    st.text(f"{i}. [{error.get('timestamp', 'N/A')}] {error.get('mensaje', 'Sin mensaje')}")
    
    @staticmethod
    def render_sidebar(metricas: Dict[str, Any], timestamp: float):
        """Renderiza la barra lateral con información del proyecto."""
        st.sidebar.title("ℹ️ Información del Proyecto")
        
        st.sidebar.markdown("""
        **Proyecto:** PixelForge Studios EP2  
        **Asignatura:** ISY0101  
        **Evaluación:** EP3 - Observabilidad  
        """)
        
        st.sidebar.divider()
        
        st.sidebar.markdown("### 📊 Resumen de Métricas")
        st.sidebar.metric("Total Consultas", metricas.get("total_consultas", 0))
        st.sidebar.metric("Consultas Exitosas", metricas.get("respuestas_exitosas", 0))
        st.sidebar.metric("Consultas con Error", metricas.get("respuestas_error", 0))
        
        st.sidebar.divider()
        
        # Timestamp de última actualización
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            st.sidebar.caption(f"Última actualización: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.sidebar.divider()
        
        st.sidebar.markdown("""
        ### 🔄 Actualizar Datos
        Para actualizar el dashboard:
        1. Ejecuta `python src/demo.py`
        2. Refresca esta página (F5)
        """)


# ================================================================
# CONTROLADOR (Controller) - Coordina modelo y vista
# ================================================================

class DashboardController:
    """
    Controlador del dashboard: coordina modelo y vista.
    
    Responsabilidades:
    - Orquestar carga de datos
    - Coordinar renderizado de componentes
    - Manejar errores y estado de la aplicación
    """
    
    def __init__(self):
        self.model = DashboardModel()
        self.view = DashboardView()
    
    def run(self):
        """Ejecuta el dashboard completo."""
        # Configurar página
        self.view.configurar_pagina()
        
        # Renderizar encabezado
        self.view.render_header()
        
        # Validar que existan datos
        if not self.model.validar_datos():
            st.error("""
            ⚠️ **No se encontraron datos de métricas**
            
            Para generar datos:
            1. Ejecuta: `python src/demo.py`
            2. Espera a que termine la demo
            3. Refresca esta página (F5)
            """)
            return
        
        # Cargar datos
        metricas_data = self.model.cargar_metricas()
        
        if "error" in metricas_data:
            st.error(metricas_data["error"])
            return
        
        resumen = metricas_data.get("resumen", {})
        df = self.model.cargar_historial()
        analisis_logs = self.model.cargar_analisis_logs()
        timestamp = metricas_data.get("timestamp", None)
        
        # Renderizar componentes principales
        self.view.render_kpis(resumen)
        
        st.divider()
        
        # Gráficos en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            self.view.render_grafico_latencia(df)
        
        with col2:
            self.view.render_distribucion_tipos(df)
        
        st.divider()
        
        # Recursos del sistema
        self.view.render_recursos_sistema(df)
        
        st.divider()
        
        # Análisis de logs
        self.view.render_analisis_logs(analisis_logs)
        
        st.divider()
        
        # Tabla de consultas
        self.view.render_tabla_consultas(df)
        
        # Sidebar
        self.view.render_sidebar(resumen, timestamp)


# ================================================================
# PUNTO DE ENTRADA
# ================================================================

if __name__ == "__main__":
    dashboard = DashboardController()
    dashboard.run()
