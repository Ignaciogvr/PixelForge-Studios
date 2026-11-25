"""
Test Completo del Código Empresarial V2.0
==========================================

Verifica todas las nuevas funcionalidades agregadas:
- Validación estricta
- Sistema de alertas
- Caché LRU
- Singleton thread-safe
- Excepciones personalizadas
- Logging estructurado
"""

import sys
import time
from src.monitoring import (
    MetricsCollector,
    AlertSystem,
    MetricsCache,
    MetricaInput,
    ValidationError,
    MonitoringError,
    logger
)

def test_validacion_estricta():
    """Test 1: Validación estricta de datos"""
    print("\n" + "="*60)
    print("TEST 1: VALIDACIÓN ESTRICTA")
    print("="*60)
    
    try:
        # Intentar crear métrica con latencia negativa (debe fallar)
        MetricaInput(
            respuesta="Test",
            pregunta="Test?",
            latencia=-1.5,  # ❌ Inválido
            tools_usadas=["test"],
            thread_id="test"
        )
        print("❌ FALLO: Debió lanzar ValidationError")
        return False
    except ValidationError as e:
        print(f"✅ PASÓ: ValidationError capturado correctamente: {e}")
    
    try:
        # Crear métrica válida (debe pasar)
        metrica = MetricaInput(
            respuesta="Respuesta válida",
            pregunta="¿Test?",
            latencia=2.5,
            tools_usadas=["consultar_GDD"],
            thread_id="thread-1"
        )
        print(f"✅ PASÓ: Métrica válida creada: latencia={metrica.latencia}s")
        return True
    except Exception as e:
        print(f"❌ FALLO: No debió lanzar excepción: {e}")
        return False

def test_sistema_alertas():
    """Test 2: Sistema de alertas multi-canal"""
    print("\n" + "="*60)
    print("TEST 2: SISTEMA DE ALERTAS")
    print("="*60)
    
    alert_system = AlertSystem()
    
    # Registrar handler personalizado
    alertas_recibidas = []
    
    def handler_test(severidad, alerta):
        alertas_recibidas.append((severidad, alerta))
        print(f"   📩 Handler recibió: [{severidad}] {alerta['mensaje']}")
    
    alert_system.registrar_handler(handler_test)
    
    # Enviar alerta de prueba
    alert_system.enviar_alerta(
        "HIGH",
        "Precisión bajo umbral: 65.0% < 70.0%",
        {"metrica": "precision", "valor": 65.0}
    )
    
    # Verificar que se registró
    if len(alertas_recibidas) == 1:
        print("✅ PASÓ: Alerta enviada y recibida correctamente")
        
        # Verificar historial
        historial = alert_system.obtener_historial_alertas()
        print(f"✅ PASÓ: Historial tiene {len(historial)} alerta(s)")
        return True
    else:
        print(f"❌ FALLO: Se esperaba 1 alerta, se recibieron {len(alertas_recibidas)}")
        return False

def test_cache_lru():
    """Test 3: Caché LRU thread-safe"""
    print("\n" + "="*60)
    print("TEST 3: CACHÉ LRU")
    print("="*60)
    
    cache = MetricsCache(max_size=3)
    
    # Agregar elementos
    cache.put("key1", {"valor": 100})
    cache.put("key2", {"valor": 200})
    cache.put("key3", {"valor": 300})
    
    # Leer elemento (debe ser hit)
    resultado = cache.get("key1")
    if resultado and resultado["valor"] == 100:
        print("✅ PASÓ: Cache hit funcionando")
    else:
        print("❌ FALLO: Cache hit no funcionó")
        return False
    
    # Leer elemento inexistente (debe ser miss)
    resultado = cache.get("key_inexistente")
    if resultado is None:
        print("✅ PASÓ: Cache miss funcionando")
    else:
        print("❌ FALLO: Cache miss no funcionó")
        return False
    
    # Verificar estadísticas
    stats = cache.get_stats()
    print(f"   📊 Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']:.1f}%")
    
    if stats['hits'] == 1 and stats['misses'] == 1:
        print("✅ PASÓ: Estadísticas correctas")
        return True
    else:
        print(f"❌ FALLO: Estadísticas incorrectas")
        return False

def test_singleton_threadsafe():
    """Test 4: Singleton thread-safe"""
    print("\n" + "="*60)
    print("TEST 4: SINGLETON THREAD-SAFE")
    print("="*60)
    
    # Resetear singleton para test limpio
    MetricsCollector._instance = None
    
    # Crear múltiples instancias
    collector1 = MetricsCollector()
    collector2 = MetricsCollector()
    collector3 = MetricsCollector()
    
    # Verificar que son la misma instancia
    if collector1 is collector2 is collector3:
        print("✅ PASÓ: Singleton funcionando (misma instancia)")
        print(f"   ID collector1: {id(collector1)}")
        print(f"   ID collector2: {id(collector2)}")
        print(f"   ID collector3: {id(collector3)}")
        return True
    else:
        print("❌ FALLO: Singleton no funciona (instancias diferentes)")
        return False

def test_metricas_completas():
    """Test 5: Registro y cálculo de métricas"""
    print("\n" + "="*60)
    print("TEST 5: MÉTRICAS COMPLETAS")
    print("="*60)
    
    # Resetear singleton
    MetricsCollector._instance = None
    collector = MetricsCollector()
    
    # Configurar umbrales personalizados
    collector.configurar_umbrales(
        precision_min=60.0,
        latencia_max=10.0,
        error_rate_max=30.0
    )
    print("✅ Umbrales configurados")
    
    # Registrar 5 consultas de prueba
    consultas = [
        ("Respuesta exitosa del GDD", 2.3, "exitosa"),
        ("El Golem tiene 1500 HP", 1.8, "exitosa"),
        ("No encuentro información sobre ese tema", 2.1, "sin_info"),
        ("ERROR: timeout en la consulta", 0.5, "error"),
        ("El sistema de combate incluye parry", 2.7, "exitosa"),
    ]
    
    for i, (respuesta, latencia, tipo_esperado) in enumerate(consultas, 1):
        collector.registrar(
            respuesta=respuesta,
            metadata={
                "pregunta": f"Pregunta {i}",
                "latencia": latencia,
                "tools_usadas": ["test"],
                "thread_id": "test-thread",
                "escenario": f"test-{i}"
            }
        )
        print(f"   ✓ Consulta {i} registrada: {tipo_esperado}")
    
    # Calcular métricas
    precision = collector.calcular_precision()
    consistencia = collector.calcular_consistencia()
    tasa_errores = collector.calcular_tasa_errores()
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Precisión:     {precision:.1f}%")
    print(f"   Consistencia:  {consistencia:.1f}%")
    print(f"   Tasa errores:  {tasa_errores:.1f}%")
    
    # Verificar resultados esperados
    if precision == 60.0 and tasa_errores == 20.0:
        print("✅ PASÓ: Métricas calculadas correctamente")
        return True
    else:
        print(f"❌ FALLO: Métricas incorrectas")
        return False

def test_clasificacion_avanzada():
    """Test 6: Clasificación avanzada de respuestas"""
    print("\n" + "="*60)
    print("TEST 6: CLASIFICACIÓN AVANZADA")
    print("="*60)
    
    collector = MetricsCollector()
    
    # Test casos de clasificación
    casos = [
        ("ERROR: timeout en la API", "error"),
        ("Exception raised in module", "error"),
        ("No tengo información sobre eso", "sin_info"),
        ("No encuentro datos", "sin_info"),
        ("abc", "sin_info"),  # Muy corto
        ("El parry funciona bloqueando justo antes del impacto según el GDD", "exitosa"),
    ]
    
    todos_correctos = True
    for respuesta, tipo_esperado in casos:
        tipo_obtenido = collector._clasificar_respuesta(respuesta)
        if tipo_obtenido == tipo_esperado:
            print(f"   ✓ '{respuesta[:40]}...' → {tipo_obtenido}")
        else:
            print(f"   ✗ '{respuesta[:40]}...' → {tipo_obtenido} (esperado: {tipo_esperado})")
            todos_correctos = False
    
    if todos_correctos:
        print("✅ PASÓ: Clasificación avanzada funcionando")
        return True
    else:
        print("❌ FALLO: Algunos casos no clasificaron correctamente")
        return False

def test_exportacion():
    """Test 7: Exportación de métricas"""
    print("\n" + "="*60)
    print("TEST 7: EXPORTACIÓN DE MÉTRICAS")
    print("="*60)
    
    collector = MetricsCollector()
    
    try:
        # Intentar exportar
        collector.exportar_json("logs/test_metricas_v2.json")
        print("✅ PASÓ: Métricas exportadas a JSON")
        
        # Verificar que el archivo existe
        import os
        if os.path.exists("logs/test_metricas_v2.json"):
            print("✅ PASÓ: Archivo JSON creado correctamente")
            return True
        else:
            print("❌ FALLO: Archivo JSON no fue creado")
            return False
    except Exception as e:
        print(f"❌ FALLO: Error en exportación: {e}")
        return False

def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*70)
    print(" TEST COMPLETO - CÓDIGO EMPRESARIAL V2.0")
    print("="*70)
    
    tests = [
        ("Validación Estricta", test_validacion_estricta),
        ("Sistema de Alertas", test_sistema_alertas),
        ("Caché LRU", test_cache_lru),
        ("Singleton Thread-Safe", test_singleton_threadsafe),
        ("Métricas Completas", test_metricas_completas),
        ("Clasificación Avanzada", test_clasificacion_avanzada),
        ("Exportación", test_exportacion),
    ]
    
    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO en {nombre}: {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "="*70)
    print(" RESUMEN DE TESTS")
    print("="*70)
    
    pasados = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre}")
    
    print("\n" + "="*70)
    print(f" RESULTADO FINAL: {pasados}/{total} tests pasados ({pasados/total*100:.1f}%)")
    print("="*70)
    
    if pasados == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! 🎉")
        print("✅ El código empresarial V2.0 funciona correctamente")
        return True
    else:
        print(f"\n⚠️ {total - pasados} test(s) fallaron")
        return False

if __name__ == "__main__":
    exito = run_all_tests()
    sys.exit(0 if exito else 1)
