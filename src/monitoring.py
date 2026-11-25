"""
monitoring.py - Sistema de Observabilidad Profesional
======================================================

Implementa métricas de calidad, rendimiento y análisis de logs
para el agente PixelForge EP2.

Patrones de diseño utilizados:
- Singleton: MetricsCollector (una sola instancia global)
- Decorator: PerformanceTracker (decorador para funciones)
- Facade: ObservabilitySystem (interfaz unificada)
- Strategy: LogAnalyzer (diferentes estrategias de análisis)

Autor: [Tu nombre]
Fecha: 2026-11-25
Evaluación: EP3 - Observabilidad
"""

import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import psutil


# ================================================================
# MÉTRICAS DE CALIDAD (IE1 - 15%)
# ================================================================

class MetricsCollector:
    """
    Recolector centralizado de métricas de calidad del agente.
    
    Implementa patrón Singleton para garantizar una única instancia
    en toda la aplicación.
    
    Métricas implementadas:
    - Precisión: % de respuestas exitosas
    - Consistencia: Estabilidad de latencias (1 - CV)
    - Tasa de errores: % de respuestas con error
    
    Example:
        >>> collector = MetricsCollector()
        >>> collector.registrar("Respuesta exitosa", {"latencia": 2.5})
        >>> print(f"Precisión: {collector.calcular_precision():.1f}%")
        Precisión: 100.0%
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        
        self.metrics = {
            "total": 0,
            "exitosas": 0,
            "errores": 0,
            "sin_info": 0
        }
        self.historial = []
        self.initialized = True
    
    def registrar(self, respuesta: str, metadata: Dict[str, Any]):
        """
        Registra una consulta con sus métricas asociadas.
        
        Args:
            respuesta: Texto de la respuesta del agente
            metadata: Diccionario con datos adicionales:
                - pregunta (str): Pregunta del usuario
                - latencia (float): Tiempo de respuesta en segundos
                - tools_usadas (List[str]): Tools llamadas por el agente
                - thread_id (str): ID del hilo de conversación
                - escenario (int, optional): ID del escenario de prueba
        """
        self.metrics["total"] += 1
        tipo = self._clasificar_respuesta(respuesta)
        
        # Actualizar contadores
        if tipo == "exitosa":
            self.metrics["exitosas"] += 1
        elif tipo == "error":
            self.metrics["errores"] += 1
        elif tipo == "sin_info":
            self.metrics["sin_info"] += 1
        
        # Guardar en historial
        self.historial.append({
            "tipo": tipo,
            "latencia": round(metadata.get("latencia", 0), 2),
            "tools_usadas": metadata.get("tools_usadas", []),
            "thread_id": metadata.get("thread_id", "unknown"),
            "escenario": metadata.get("escenario", None),
            "timestamp": time.time(),
            "longitud_respuesta": len(respuesta)
        })
    
    def _clasificar_respuesta(self, respuesta: str) -> str:
        """
        Clasifica el tipo de respuesta del agente.
        
        Returns:
            "exitosa", "sin_info" o "error"
        """
        respuesta_lower = respuesta.lower()
        
        if "no tengo información" in respuesta_lower:
            return "sin_info"
        elif "error" in respuesta_lower or "no pude" in respuesta_lower:
            return "error"
        else:
            return "exitosa"
    
    # --- MÉTRICA 1: PRECISIÓN ---
    def calcular_precision(self) -> float:
        """
        Calcula la precisión del agente.
        
        Precisión = (Respuestas exitosas / Total consultas) × 100
        
        Interpretación:
        - >80%: Excelente
        - 60-80%: Bueno
        - <60%: Requiere mejora
        
        Returns:
            float: Porcentaje de precisión (0-100)
        """
        if self.metrics["total"] == 0:
            return 0.0
        return (self.metrics["exitosas"] / self.metrics["total"]) * 100
    
    # --- MÉTRICA 2: CONSISTENCIA ---
    def calcular_consistencia(self) -> float:
        """
        Calcula la consistencia del agente basada en variabilidad de latencias.
        
        Consistencia = (1 - Coeficiente de Variación) × 100
        CV = Desviación Estándar / Media
        
        Interpretación:
        - >90%: Muy consistente
        - 70-90%: Consistente
        - <70%: Variable
        
        Returns:
            float: Porcentaje de consistencia (0-100)
        """
        latencias = [h["latencia"] for h in self.historial]
        
        if len(latencias) < 2:
            return 100.0  # Con 1 dato, es perfectamente consistente
        
        # Calcular media
        media = sum(latencias) / len(latencias)
        
        if media == 0:
            return 100.0
        
        # Calcular desviación estándar
        varianza = sum((x - media) ** 2 for x in latencias) / len(latencias)
        desv_std = varianza ** 0.5
        
        # Coeficiente de variación
        cv = desv_std / media
        
        # Consistencia (invertido)
        consistencia = (1 - cv) * 100
        
        # Garantizar rango [0, 100]
        return max(0, min(100, consistencia))
    
    # --- MÉTRICA 3: TASA DE ERRORES ---
    def calcular_tasa_errores(self) -> float:
        """
        Calcula la tasa de errores del agente.
        
        Tasa de Errores = (Respuestas con error / Total consultas) × 100
        
        Interpretación:
        - <5%: Excelente
        - 5-10%: Aceptable
        - >10%: Crítico
        
        Returns:
            float: Porcentaje de errores (0-100)
        """
        if self.metrics["total"] == 0:
            return 0.0
        return (self.metrics["errores"] / self.metrics["total"]) * 100
    
    def generar_reporte(self) -> Dict[str, Any]:
        """
        Genera un reporte completo con todas las métricas.
        
        Returns:
            dict: Reporte estructurado con métricas y estadísticas
        """
        return {
            "total_consultas": self.metrics["total"],
            "respuestas_exitosas": self.metrics["exitosas"],
            "respuestas_sin_info": self.metrics["sin_info"],
            "respuestas_error": self.metrics["errores"],
            "precision": round(self.calcular_precision(), 2),
            "consistencia": round(self.calcular_consistencia(), 2),
            "tasa_errores": round(self.calcular_tasa_errores(), 2),
            "latencia_promedio": self._calcular_latencia_promedio(),
            "latencia_minima": self._calcular_latencia_min(),
            "latencia_maxima": self._calcular_latencia_max(),
            "latencia_p95": self._calcular_latencia_p95(),
        }
    
    def _calcular_latencia_promedio(self) -> float:
        if not self.historial:
            return 0.0
        latencias = [h["latencia"] for h in self.historial]
        return round(sum(latencias) / len(latencias), 2)
    
    def _calcular_latencia_min(self) -> float:
        if not self.historial:
            return 0.0
        return round(min(h["latencia"] for h in self.historial), 2)
    
    def _calcular_latencia_max(self) -> float:
        if not self.historial:
            return 0.0
        return round(max(h["latencia"] for h in self.historial), 2)
    
    def _calcular_latencia_p95(self) -> float:
        """Percentil 95: 95% de las consultas son más rápidas"""
        if not self.historial:
            return 0.0
        latencias = sorted([h["latencia"] for h in self.historial])
        idx = int(len(latencias) * 0.95)
        return round(latencias[min(idx, len(latencias)-1)], 2)
    
    def exportar_json(self, path: str = "logs/metrics.json"):
        """
        Exporta métricas a archivo JSON.
        
        Args:
            path: Ruta del archivo de salida
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "resumen": self.generar_reporte(),
                "historial": self.historial,
                "timestamp": time.time()
            }, f, indent=2, ensure_ascii=False)


# ================================================================
# MÉTRICAS DE RENDIMIENTO (IE2 - 10%)
# ================================================================

class PerformanceTracker:
    """
    Rastreador de métricas de rendimiento (latencia, CPU, RAM).
    
    Implementa patrón Decorator para agregar tracking automático
    a funciones existentes sin modificar su código.
    
    Example:
        >>> @PerformanceTracker.track
        >>> def mi_funcion():
        >>>     time.sleep(1)
        >>>     return "resultado"
        >>> mi_funcion()  # Automáticamente trackeado
    """
    
    @staticmethod
    def obtener_recursos_sistema() -> Dict[str, float]:
        """
        Captura el uso de recursos del proceso actual.
        
        Returns:
            dict: CPU (%), RAM (MB), timestamp
        """
        proceso = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": round(proceso.cpu_percent(interval=0.1), 1),
            "ram_mb": round(proceso.memory_info().rss / 1024 / 1024, 1),
            "timestamp": time.time()
        }
    
    @staticmethod
    def track(func):
        """
        Decorador para trackear automáticamente el rendimiento de una función.
        
        Args:
            func: Función a decorar
        
        Returns:
            Función decorada con tracking
        """
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Capturar recursos antes
            recursos_antes = PerformanceTracker.obtener_recursos_sistema()
            t0 = time.time()
            
            # Ejecutar función
            resultado = func(*args, **kwargs)
            
            # Capturar recursos después
            latencia = time.time() - t0
            recursos_despues = PerformanceTracker.obtener_recursos_sistema()
            
            # Log de rendimiento
            print(f"[Performance] {func.__name__}: {latencia:.2f}s | "
                  f"CPU: {recursos_despues['cpu_percent']:.1f}% | "
                  f"RAM: {recursos_despues['ram_mb']:.1f}MB")
            
            return resultado
        
        return wrapper


# ================================================================
# ANÁLISIS DE LOGS (IE3 - 15%)
# ================================================================

class LogAnalyzer:
    """
    Analizador automático de archivos de log.
    
    Implementa patrón Strategy para diferentes estrategias de análisis.
    
    Capacidades:
    - Contar eventos por tipo (INFO, ERROR, WARNING)
    - Extraer errores críticos con contexto
    - Calcular tasa de éxito
    - Detectar patrones y anomalías
    
    Example:
        >>> analyzer = LogAnalyzer()
        >>> reporte = analyzer.analizar_archivo("logs/agent.log")
        >>> print(f"Errores encontrados: {len(reporte['errores_criticos'])}")
    """
    
    def analizar_archivo(self, path: str) -> Dict[str, Any]:
        """
        Analiza un archivo de log completo.
        
        Args:
            path: Ruta al archivo de log
        
        Returns:
            dict: Reporte estructurado con hallazgos
        """
        if not os.path.exists(path):
            return {
                "error": f"Archivo no encontrado: {path}",
                "total_lineas": 0,
                "eventos": {},
                "errores_criticos": [],
                "tasa_exito": 0.0
            }
        
        with open(path, encoding="utf-8") as f:
            lineas = f.readlines()
        
        # Contadores de eventos
        eventos = Counter()
        errores = []
        warnings = []
        consultas_info = []
        
        for idx, linea in enumerate(lineas):
            # Clasificar por nivel de log
            if "[ERROR]" in linea:
                eventos["errores"] += 1
                errores.append(self._extraer_error(linea, idx + 1))
            elif "[WARNING]" in linea or "[WARN]" in linea:
                eventos["warnings"] += 1
                warnings.append(linea.strip())
            elif "[INFO]" in linea:
                eventos["info"] += 1
            
            # Detectar eventos específicos
            if "Consulta recibida" in linea or "consulta recibida" in linea:
                eventos["consultas"] += 1
                consultas_info.append(self._extraer_consulta_info(linea))
            elif "Respuesta generada" in linea or "respuesta generada" in linea:
                eventos["respuestas"] += 1
        
        return {
            "total_lineas": len(lineas),
            "eventos": dict(eventos),
            "errores_criticos": errores,
            "warnings": warnings[:10],  # Primeros 10
            "consultas_detectadas": eventos.get("consultas", 0),
            "respuestas_detectadas": eventos.get("respuestas", 0),
            "tasa_exito": self._calcular_tasa_exito(eventos),
            "patrones": self._detectar_patrones(consultas_info)
        }
    
    def _extraer_error(self, linea: str, numero_linea: int) -> Dict[str, Any]:
        """Extrae información estructurada de un error."""
        # Regex para timestamp (formato: 2024-11-25 10:30:45)
        match_timestamp = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', linea)
        timestamp = match_timestamp.group(1) if match_timestamp else "unknown"
        
        # Extraer mensaje después de [ERROR]
        match_mensaje = re.search(r'\[ERROR\]\s*(.+)', linea)
        mensaje = match_mensaje.group(1).strip() if match_mensaje else linea.strip()
        
        return {
            "linea": numero_linea,
            "timestamp": timestamp,
            "mensaje": mensaje[:200]  # Primeros 200 caracteres
        }
    
    def _extraer_consulta_info(self, linea: str) -> Dict[str, Any]:
        """Extrae información de una línea de consulta."""
        # Intentar extraer thread_id
        match_thread = re.search(r'thread[=:](\S+)', linea)
        thread_id = match_thread.group(1) if match_thread else "unknown"
        
        return {
            "thread_id": thread_id,
            "linea": linea.strip()[:100]
        }
    
    def _calcular_tasa_exito(self, eventos: Counter) -> float:
        """
        Calcula la tasa de éxito basada en consultas vs respuestas.
        
        Tasa de éxito = (Respuestas / Consultas) × 100
        """
        consultas = eventos.get("consultas", 0)
        respuestas = eventos.get("respuestas", 0)
        
        if consultas == 0:
            return 0.0
        
        return round((respuestas / consultas) * 100, 2)
    
    def _detectar_patrones(self, consultas_info: List[Dict]) -> Dict[str, Any]:
        """Detecta patrones en las consultas."""
        if not consultas_info:
            return {"total": 0}
        
        # Contar threads únicos
        threads = set(c["thread_id"] for c in consultas_info)
        
        return {
            "total_consultas": len(consultas_info),
            "threads_unicos": len(threads),
            "promedio_consultas_por_thread": round(len(consultas_info) / len(threads), 2)
        }
    
    def exportar_reporte(self, path: str = "logs/log_analysis.json"):
        """
        Exporta el análisis a JSON.
        
        Args:
            path: Ruta del archivo de salida
        """
        reporte = self.analizar_archivo("logs/agent.log")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)


# ================================================================
# SISTEMA UNIFICADO DE OBSERVABILIDAD (Patrón Facade)
# ================================================================

class ObservabilitySystem:
    """
    Sistema unificado de observabilidad.
    
    Implementa patrón Facade: proporciona una interfaz simple
    para un sistema complejo de múltiples componentes.
    
    Responsabilidades:
    - Inicializar todos los subsistemas
    - Proporcionar punto único de registro
    - Generar reportes consolidados
    - Exportar datos para dashboard
    
    Example:
        >>> obs = ObservabilitySystem()
        >>> obs.iniciar()
        >>> obs.registrar_consulta("¿Pregunta?", "Respuesta", 2.5, {...})
        >>> obs.guardar_todo()
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.tracker = PerformanceTracker()
        self.analyzer = LogAnalyzer()
        self._iniciado = False
    
    def iniciar(self):
        """Inicializa el sistema de observabilidad."""
        if self._iniciado:
            print("[Observability] Sistema ya iniciado")
            return
        
        print("\n" + "=" * 60)
        print("  SISTEMA DE OBSERVABILIDAD - PixelForge EP2")
        print("=" * 60)
        print("[Observability] Inicializando componentes...")
        print("  ✓ MetricsCollector: Métricas de calidad")
        print("  ✓ PerformanceTracker: Métricas de rendimiento")
        print("  ✓ LogAnalyzer: Análisis de logs")
        print("[Observability] Sistema listo para registrar métricas")
        print("=" * 60 + "\n")
        
        self._iniciado = True
    
    def registrar_consulta(self, pregunta: str, respuesta: str, 
                          tiempo: float, metadata: Optional[Dict] = None):
        """
        Punto único de registro para todas las consultas.
        
        Args:
            pregunta: Pregunta del usuario
            respuesta: Respuesta del agente
            tiempo: Latencia en segundos
            metadata: Metadatos adicionales (escenario, thread_id, etc.)
        """
        if not self._iniciado:
            self.iniciar()
        
        # Preparar metadatos completos
        meta = metadata or {}
        meta["pregunta"] = pregunta[:100]  # Primeros 100 chars
        meta["latencia"] = tiempo
        
        # Agregar recursos del sistema
        recursos = self.tracker.obtener_recursos_sistema()
        meta["cpu_percent"] = recursos["cpu_percent"]
        meta["ram_mb"] = recursos["ram_mb"]
        
        # Registrar en métricas
        self.metrics.registrar(respuesta, meta)
    
    def generar_reporte_completo(self) -> Dict[str, Any]:
        """
        Genera un reporte consolidado con todas las métricas.
        
        Returns:
            dict: Reporte completo con métricas de calidad, 
                  rendimiento y análisis de logs
        """
        return {
            "metricas_calidad": self.metrics.generar_reporte(),
            "analisis_logs": self.analyzer.analizar_archivo("logs/agent.log"),
            "recursos_sistema": self.tracker.obtener_recursos_sistema(),
            "timestamp": time.time()
        }
    
    def guardar_todo(self):
        """Persiste todas las métricas y análisis en disco."""
        print("\n[Observability] Guardando métricas...")
        
        # Crear directorio logs si no existe
        os.makedirs("logs", exist_ok=True)
        
        # Guardar métricas
        self.metrics.exportar_json("logs/metrics.json")
        print("  ✓ Métricas guardadas en: logs/metrics.json")
        
        # Guardar análisis de logs
        self.analyzer.exportar_reporte("logs/log_analysis.json")
        print("  ✓ Análisis de logs guardado en: logs/log_analysis.json")
        
        # Guardar reporte completo
        reporte = self.generar_reporte_completo()
        with open("logs/reporte_completo.json", "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        print("  ✓ Reporte completo guardado en: logs/reporte_completo.json")
        
        print("[Observability] ✅ Todos los datos guardados correctamente\n")
    
    def imprimir_resumen(self):
        """Imprime un resumen de las métricas en consola."""
        reporte = self.metrics.generar_reporte()
        
        print("\n" + "=" * 60)
        print("  RESUMEN DE MÉTRICAS - PixelForge EP2")
        print("=" * 60)
        print(f"\n📊 MÉTRICAS DE CALIDAD:")
        print(f"  • Precisión:       {reporte['precision']:.1f}%")
        print(f"  • Consistencia:    {reporte['consistencia']:.1f}%")
        print(f"  • Tasa de errores: {reporte['tasa_errores']:.1f}%")
        print(f"\n⏱️  MÉTRICAS DE RENDIMIENTO:")
        print(f"  • Latencia promedio: {reporte['latencia_promedio']:.2f}s")
        print(f"  • Latencia mínima:   {reporte['latencia_minima']:.2f}s")
        print(f"  • Latencia máxima:   {reporte['latencia_maxima']:.2f}s")
        print(f"  • Latencia P95:      {reporte['latencia_p95']:.2f}s")
        print(f"\n📈 CONSULTAS:")
        print(f"  • Total:         {reporte['total_consultas']}")
        print(f"  • Exitosas:      {reporte['respuestas_exitosas']}")
        print(f"  • Sin info:      {reporte['respuestas_sin_info']}")
        print(f"  • Con errores:   {reporte['respuestas_error']}")
        print("=" * 60 + "\n")


# ================================================================
# PUNTO DE ENTRADA PARA PRUEBAS
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  TEST DEL SISTEMA DE OBSERVABILIDAD")
    print("=" * 60)
    
    # Crear sistema
    obs = ObservabilitySystem()
    obs.iniciar()
    
    # Simular algunas consultas
    consultas_test = [
        ("¿Cómo funciona el parry?", "El parry se activa...", 2.3),
        ("¿Cuántos HP tiene el Golem?", "El Golem tiene 1500 HP [BALANCE]", 1.8),
        ("¿Quién tiene el bug PF-1003?", "No tengo información sobre eso", 2.1),
        ("¿Qué es Python?", "Error: pregunta fuera de contexto", 0.5),
    ]
    
    for i, (preg, resp, tiempo) in enumerate(consultas_test, 1):
        obs.registrar_consulta(
            pregunta=preg,
            respuesta=resp,
            tiempo=tiempo,
            metadata={"escenario": i, "thread_id": "test-1"}
        )
    
    # Imprimir resumen
    obs.imprimir_resumen()
    
    # Guardar datos
    obs.guardar_todo()
    
    print("✅ Test completado. Revisa los archivos en logs/")
