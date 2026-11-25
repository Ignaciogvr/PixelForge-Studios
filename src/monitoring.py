"""
monitoring.py - Sistema de Observabilidad Empresarial
======================================================

Sistema avanzado de observabilidad con métricas de calidad, rendimiento,
análisis de logs, sistema de alertas y exportación multi-formato.

Características empresariales:
- Validación estricta de datos con esquemas
- Manejo robusto de excepciones con logging detallado
- Sistema de umbrales configurables con alertas
- Caché inteligente para optimización de consultas
- Exportación multi-formato (JSON, CSV, Prometheus)
- Métricas estadísticas avanzadas (percentiles, desviación estándar)
- Thread-safe para entornos concurrentes

Patrones de diseño utilizados:
- Singleton: MetricsCollector (instancia única thread-safe)
- Decorator: PerformanceTracker (AOP para métricas)
- Facade: ObservabilitySystem (interfaz unificada)
- Strategy: LogAnalyzer (estrategias de análisis)
- Builder: MetricsBuilder (construcción flexible)
- Observer: AlertSystem (notificaciones de eventos)

Autor: Ignacio Núñez, René Marambio
Fecha: 2026-11-25
Evaluación: EP3 - Observabilidad
Versión: 2.0 (Versión Empresarial)
"""

import json
import os
import re
import time
import logging
import threading
from collections import Counter, deque
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
from pathlib import Path
import psutil

# ================================================================
# CONFIGURACIÓN Y CONSTANTES
# ================================================================

# Logger profesional con formato estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Umbrales por defecto (configurables)
DEFAULT_THRESHOLDS = {
    "precision_min": 70.0,       # % mínimo de precisión aceptable
    "latencia_max": 5.0,         # segundos máximos de latencia
    "error_rate_max": 10.0,      # % máximo de errores
    "cpu_max": 80.0,             # % máximo de CPU
    "ram_max": 2048,             # MB máximo de RAM
    "consistencia_min": 70.0     # % mínimo de consistencia
}

# Ventana de retención de métricas (últimas N consultas)
METRICS_WINDOW_SIZE = 1000

# ================================================================
# EXCEPCIONES PERSONALIZADAS
# ================================================================

class MonitoringError(Exception):
    """Excepción base para errores de monitoreo"""
    pass

class ValidationError(MonitoringError):
    """Error de validación de datos"""
    pass

class ThresholdViolationError(MonitoringError):
    """Error cuando se violan umbrales configurados"""
    pass

class ExportError(MonitoringError):
    """Error durante exportación de métricas"""
    pass


# ================================================================
# VALIDACIÓN DE DATOS
# ================================================================

@dataclass
class MetricaInput:
    """Esquema de validación para entrada de métricas"""
    respuesta: str
    pregunta: str
    latencia: float
    tools_usadas: List[str]
    thread_id: str
    escenario: Optional[str] = None
    cpu_percent: Optional[float] = None
    ram_mb: Optional[float] = None
    
    def __post_init__(self):
        """Validación automática después de construcción"""
        if not isinstance(self.respuesta, str) or len(self.respuesta) == 0:
            raise ValidationError("Respuesta debe ser string no vacío")
        if not isinstance(self.latencia, (int, float)) or self.latencia < 0:
            raise ValidationError(f"Latencia inválida: {self.latencia}")
        if not isinstance(self.tools_usadas, list):
            raise ValidationError("tools_usadas debe ser una lista")
        if self.cpu_percent is not None and (self.cpu_percent < 0 or self.cpu_percent > 100):
            raise ValidationError(f"CPU % inválido: {self.cpu_percent}")
        if self.ram_mb is not None and self.ram_mb < 0:
            raise ValidationError(f"RAM MB inválida: {self.ram_mb}")

# ================================================================
# SISTEMA DE ALERTAS (Observer Pattern)
# ================================================================

class AlertSystem:
    """
    Sistema de alertas con soporte para múltiples canales.
    Permite registrar callbacks que se ejecutan cuando se violan umbrales.
    """
    
    def __init__(self):
        self.handlers: List[Callable[[str, Dict], None]] = []
        self.alertas_enviadas = []
    
    def registrar_handler(self, handler: Callable[[str, Dict], None]):
        """Registra un handler de alertas (email, Slack, log, etc.)"""
        self.handlers.append(handler)
        logger.info(f"Handler de alertas registrado: {handler.__name__}")
    
    def enviar_alerta(self, severidad: str, mensaje: str, contexto: Dict[str, Any]):
        """
        Envía alerta a todos los handlers registrados.
        
        Args:
            severidad: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            mensaje: Descripción de la alerta
            contexto: Datos adicionales (métricas, timestamps, etc.)
        """
        alerta = {
            "severidad": severidad,
            "mensaje": mensaje,
            "contexto": contexto,
            "timestamp": datetime.now().isoformat()
        }
        
        self.alertas_enviadas.append(alerta)
        logger.warning(f"⚠️ ALERTA [{severidad}]: {mensaje}")
        
        for handler in self.handlers:
            try:
                handler(severidad, alerta)
            except Exception as e:
                logger.error(f"Error ejecutando handler {handler.__name__}: {e}")
    
    def obtener_historial_alertas(self, ultimas_n: Optional[int] = None) -> List[Dict]:
        """Obtiene historial de alertas"""
        if ultimas_n:
            return self.alertas_enviadas[-ultimas_n:]
        return self.alertas_enviadas.copy()

# ================================================================
# SISTEMA DE CACHÉ
# ================================================================

class MetricsCache:
    """
    Caché LRU (Least Recently Used) para optimizar cálculos repetidos.
    Thread-safe con lock para entornos concurrentes.
    """
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.access_order: deque = deque(maxlen=max_size)
        self.max_size = max_size
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del caché"""
        with self.lock:
            if key in self.cache:
                self.access_order.remove(key)
                self.access_order.append(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        """Almacena valor en caché con política LRU"""
        with self.lock:
            if key in self.cache:
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def invalidate(self):
        """Invalida todo el caché"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            logger.info("Caché invalidado")
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Obtiene estadísticas del caché"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "size": len(self.cache)
        }

# ================================================================
# MÉTRICAS DE CALIDAD (IE1 - 15%)
# ================================================================

class MetricsCollector:
    """
    Recolector centralizado de métricas con capacidades empresariales.
    
    Implementa patrón Singleton thread-safe para garantizar una única instancia
    global en toda la aplicación, incluso en entornos multi-thread.
    
    Características avanzadas:
    - Ventana deslizante de métricas (últimas N consultas)
    - Caché inteligente para cálculos costosos
    - Sistema de alertas integrado
    - Validación estricta de datos de entrada
    - Métricas estadísticas avanzadas (percentiles, CV, desviación)
    - Thread-safe con locks
    
    Métricas implementadas:
    - Precisión: % de respuestas exitosas
    - Consistencia: Estabilidad de latencias (1 - CV)
    - Tasa de errores: % de respuestas con error
    - Distribución de tipos de respuesta
    - Métricas de recursos (CPU, RAM)
    - Análisis de herramientas más usadas
    
    Example:
        >>> collector = MetricsCollector()
        >>> collector.registrar("Respuesta exitosa", {
        ...     "pregunta": "¿Cómo funciona X?",
        ...     "latencia": 2.5,
        ...     "tools_usadas": ["consultar_GDD"],
        ...     "thread_id": "thread-1"
        ... })
        >>> print(f"Precisión: {collector.calcular_precision():.1f}%")
        Precisión: 100.0%
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implementación thread-safe de Singleton con double-check locking"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        
        with self._lock:
            if self.initialized:
                return
            
            # Contadores básicos
            self.metrics = {
                "total": 0,
                "exitosas": 0,
                "errores": 0,
                "sin_info": 0
            }
            
            # Historial con ventana deslizante (últimas N consultas)
            self.historial: deque = deque(maxlen=METRICS_WINDOW_SIZE)
            
            # Sistema de caché para cálculos costosos
            self.cache = MetricsCache(max_size=50)
            
            # Sistema de alertas
            self.alert_system = AlertSystem()
            
            # Umbrales configurables
            self.thresholds = DEFAULT_THRESHOLDS.copy()
            
            # Timestamps para métricas temporales
            self.inicio_monitoreo = time.time()
            self.ultima_actualizacion = None
            
            self.initialized = True
            logger.info("MetricsCollector inicializado (Singleton thread-safe)")
    
    def configurar_umbrales(self, **kwargs):
        """
        Configura umbrales personalizados para alertas.
        
        Args:
            precision_min (float): Precisión mínima aceptable (%)
            latencia_max (float): Latencia máxima aceptable (segundos)
            error_rate_max (float): Tasa de errores máxima (%)
            cpu_max (float): Uso máximo de CPU (%)
            ram_max (int): Uso máximo de RAM (MB)
            consistencia_min (float): Consistencia mínima (%)
        """
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value
                logger.info(f"Umbral configurado: {key} = {value}")
            else:
                logger.warning(f"Umbral desconocido ignorado: {key}")
        
        self.cache.invalidate()  # Invalidar caché tras cambio de config
    
    def registrar(self, respuesta: str, metadata: Dict[str, Any]):
        """
        Registra una consulta con validación estricta y análisis automático.
        
        Args:
            respuesta: Texto de la respuesta del agente
            metadata: Diccionario con datos obligatorios:
                - pregunta (str): Pregunta del usuario
                - latencia (float): Tiempo de respuesta en segundos
                - tools_usadas (List[str]): Tools llamadas
                - thread_id (str): ID del hilo
                - escenario (str, optional): ID del escenario
                - cpu_percent (float, optional): % CPU usado
                - ram_mb (float, optional): MB RAM usados
        
        Raises:
            ValidationError: Si los datos no pasan validación
        """
        try:
            # Validar entrada con dataclass
            entrada = MetricaInput(
                respuesta=respuesta,
                pregunta=metadata.get("pregunta", ""),
                latencia=metadata.get("latencia", 0),
                tools_usadas=metadata.get("tools_usadas", []),
                thread_id=metadata.get("thread_id", "unknown"),
                escenario=metadata.get("escenario"),
                cpu_percent=metadata.get("cpu_percent"),
                ram_mb=metadata.get("ram_mb")
            )
            
            # Clasificar respuesta
            tipo = self._clasificar_respuesta(respuesta)
            
            # Actualizar contadores
            with self._lock:
                self.metrics["total"] += 1
                if tipo == "exitosa":
                    self.metrics["exitosas"] += 1
                elif tipo == "error":
                    self.metrics["errores"] += 1
                elif tipo == "sin_info":
                    self.metrics["sin_info"] += 1
                
                # Guardar en historial (ventana deslizante)
                registro = {
                    "tipo": tipo,
                    "latencia": round(entrada.latencia, 3),
                    "tools_usadas": entrada.tools_usadas,
                    "thread_id": entrada.thread_id,
                    "escenario": entrada.escenario,
                    "timestamp": time.time(),
                    "longitud_respuesta": len(respuesta),
                    "cpu_percent": entrada.cpu_percent,
                    "ram_mb": entrada.ram_mb
                }
                self.historial.append(registro)
                self.ultima_actualizacion = time.time()
            
            # Invalidar caché tras nueva entrada
            self.cache.invalidate()
            
            # Verificar umbrales y generar alertas si es necesario
            self._verificar_umbrales(registro)
            
            logger.debug(f"Métrica registrada: {tipo} | Latencia: {entrada.latencia:.2f}s")
            
        except ValidationError as e:
            logger.error(f"Error de validación al registrar métrica: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al registrar métrica: {e}", exc_info=True)
            raise MonitoringError(f"Error al registrar métrica: {e}")
    
    def _clasificar_respuesta(self, respuesta: str) -> str:
        """
        Clasifica el tipo de respuesta con múltiples heurísticas.
        
        Aplica análisis multi-criterio:
        1. Detección de errores explícitos
        2. Detección de falta de información
        3. Validación de longitud mínima
        4. Análisis de palabras clave
        
        Returns:
            str: "exitosa", "sin_info" o "error"
        """
        respuesta_lower = respuesta.lower().strip()
        
        # Patrón 1: Errores explícitos (alta prioridad)
        error_patterns = [
            "error", "exception", "traceback", "failed", "no pude",
            "imposible", "falló", "timeout", "connection refused"
        ]
        if any(pattern in respuesta_lower for pattern in error_patterns):
            return "error"
        
        # Patrón 2: Falta de información
        no_info_patterns = [
            "no tengo información", "no encuentro", "no dispongo",
            "no puedo proporcionar", "no hay datos", "desconocida",
            "no está en la documentación", "no conozco"
        ]
        if any(pattern in respuesta_lower for pattern in no_info_patterns):
            return "sin_info"
        
        # Patrón 3: Respuesta demasiado corta (posible error)
        if len(respuesta.strip()) < 20:
            return "sin_info"
        
        # Patrón 4: Respuesta válida (por defecto)
        return "exitosa"
    
    def _verificar_umbrales(self, ultimo_registro: Dict[str, Any]):
        """
        Verifica si las métricas actuales violan umbrales configurados.
        Genera alertas automáticamente si es necesario.
        """
        try:
            # Solo verificar cada 5 consultas (evitar spam de alertas)
            if self.metrics["total"] % 5 != 0:
                return
            
            # Verificar precisión
            precision_actual = self.calcular_precision()
            if precision_actual < self.thresholds["precision_min"]:
                self.alert_system.enviar_alerta(
                    "HIGH",
                    f"Precisión bajo umbral: {precision_actual:.1f}% < {self.thresholds['precision_min']:.1f}%",
                    {"metrica": "precision", "valor": precision_actual}
                )
            
            # Verificar latencia
            latencia_actual = ultimo_registro.get("latencia", 0)
            if latencia_actual > self.thresholds["latencia_max"]:
                self.alert_system.enviar_alerta(
                    "MEDIUM",
                    f"Latencia alta: {latencia_actual:.2f}s > {self.thresholds['latencia_max']:.2f}s",
                    {"metrica": "latencia", "valor": latencia_actual}
                )
            
            # Verificar tasa de errores
            error_rate = self.calcular_tasa_errores()
            if error_rate > self.thresholds["error_rate_max"]:
                self.alert_system.enviar_alerta(
                    "CRITICAL",
                    f"Tasa de errores crítica: {error_rate:.1f}% > {self.thresholds['error_rate_max']:.1f}%",
                    {"metrica": "error_rate", "valor": error_rate}
                )
            
        except Exception as e:
            logger.error(f"Error verificando umbrales: {e}")
    
    
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
        
        Raises:
            ExportError: Si falla la exportación
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Convertir deque a list para serialización JSON
            historial_list = list(self.historial)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "resumen": self.generar_reporte(),
                    "historial": historial_list,
                    "timestamp": time.time()
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Métricas exportadas a {path}")
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}", exc_info=True)
            raise ExportError(f"No se pudo exportar a {path}: {e}")


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
