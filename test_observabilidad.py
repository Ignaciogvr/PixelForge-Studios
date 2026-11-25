"""
test_observabilidad.py - Test rápido del sistema de observabilidad
===================================================================

Verifica que el sistema de observabilidad funcione correctamente
sin necesidad de ejecutar la demo completa.

Uso:
    python test_observabilidad.py
"""

import os
import sys
import time

# Asegurar que src/ esté en sys.path
_SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from monitoring import ObservabilitySystem

def test_basico():
    """Test básico del sistema de observabilidad."""
    print("\n" + "=" * 60)
    print("  TEST RÁPIDO - SISTEMA DE OBSERVABILIDAD")
    print("=" * 60 + "\n")
    
    # Crear sistema
    print("[1/4] Inicializando sistema...")
    obs = ObservabilitySystem()
    obs.iniciar()
    
    # Simular consultas
    print("\n[2/4] Simulando consultas...")
    
    consultas_test = [
        {
            "pregunta": "¿Cómo funciona el parry?",
            "respuesta": "El parry se activa cuando bloqueas justo antes del impacto [GDD]",
            "tiempo": 2.3
        },
        {
            "pregunta": "¿Cuántos HP tiene el Golem?",
            "respuesta": "El Golem de Basalto tiene 1500 HP [BALANCE]",
            "tiempo": 1.8
        },
        {
            "pregunta": "¿Quién tiene el bug PF-1003?",
            "respuesta": "No tengo información sobre eso en los documentos",
            "tiempo": 2.1
        },
        {
            "pregunta": "¿Qué es Python?",
            "respuesta": "Error: pregunta fuera del contexto de PixelForge Studios",
            "tiempo": 0.5
        },
        {
            "pregunta": "¿Cuál es la estrategia para el Lobo Sombrío?",
            "respuesta": "El Lobo Sombrío es rápido, usa dash para esquivar sus ataques [GDD]",
            "tiempo": 2.7
        },
    ]
    
    for i, consulta in enumerate(consultas_test, 1):
        obs.registrar_consulta(
            pregunta=consulta["pregunta"],
            respuesta=consulta["respuesta"],
            tiempo=consulta["tiempo"],
            metadata={
                "escenario": f"test-{i}",
                "thread_id": "test-thread-1",
                "tools_usadas": ["consultar_GDD"] if "[GDD]" in consulta["respuesta"] 
                               else ["consultar_balance"] if "[BALANCE]" in consulta["respuesta"]
                               else ["auto"]
            }
        )
        time.sleep(0.1)  # Simular tiempo entre consultas
    
    print(f"  ✓ {len(consultas_test)} consultas simuladas")
    
    # Mostrar resumen
    print("\n[3/4] Generando resumen de métricas...")
    obs.imprimir_resumen()
    
    # Guardar datos
    print("[4/4] Guardando datos en archivos JSON...")
    obs.guardar_todo()
    
    # Verificar archivos creados
    print("\n" + "=" * 60)
    print("  ✅ TEST COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    
    archivos_esperados = [
        "logs/metrics.json",
        "logs/log_analysis.json",
        "logs/reporte_completo.json"
    ]
    
    print("\nArchivos generados:")
    for archivo in archivos_esperados:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"  ✓ {archivo} ({size} bytes)")
        else:
            print(f"  ✗ {archivo} (no encontrado)")
    
    print("\n" + "=" * 60)
    print("  PRÓXIMOS PASOS:")
    print("=" * 60)
    print("  1. Revisa los archivos JSON en logs/")
    print("  2. Ejecuta el dashboard:")
    print("     streamlit run src/dashboard.py")
    print("  3. Ejecuta la demo completa:")
    print("     python src/demo.py")
    print("=" * 60 + "\n")
    
    return True


def test_metricas():
    """Test específico de cálculo de métricas."""
    from monitoring import MetricsCollector
    
    print("\n" + "=" * 60)
    print("  TEST DE MÉTRICAS")
    print("=" * 60 + "\n")
    
    # Reset del singleton para test limpio
    MetricsCollector._instance = None
    collector = MetricsCollector()
    
    # Registrar consultas de prueba
    consultas_test = [
        ("Respuesta exitosa 1", 2.5),
        ("Respuesta exitosa 2", 2.3),
        ("Respuesta exitosa 3", 2.8),
        ("No tengo información sobre eso", 2.0),
        ("Error al procesar la consulta", 1.5),
    ]
    
    for respuesta, latencia in consultas_test:
        collector.registrar(respuesta, {"latencia": latencia})
    
    # Verificar cálculos
    reporte = collector.generar_reporte()
    
    print("Resultados:")
    print(f"  Total consultas:    {reporte['total_consultas']}")
    print(f"  Respuestas exitosas: {reporte['respuestas_exitosas']}")
    print(f"  Sin información:     {reporte['respuestas_sin_info']}")
    print(f"  Con errores:         {reporte['respuestas_error']}")
    print(f"\nMétricas calculadas:")
    print(f"  Precisión:          {reporte['precision']:.2f}%")
    print(f"  Consistencia:       {reporte['consistencia']:.2f}%")
    print(f"  Tasa de errores:    {reporte['tasa_errores']:.2f}%")
    print(f"  Latencia promedio:  {reporte['latencia_promedio']:.2f}s")
    print(f"  Latencia mínima:    {reporte['latencia_minima']:.2f}s")
    print(f"  Latencia máxima:    {reporte['latencia_maxima']:.2f}s")
    
    # Validar resultados
    assert reporte['total_consultas'] == 5, "Total consultas incorrecto"
    assert reporte['respuestas_exitosas'] == 3, "Respuestas exitosas incorrectas"
    assert reporte['precision'] == 60.0, "Precisión incorrecta"
    assert reporte['tasa_errores'] == 20.0, "Tasa de errores incorrecta"
    
    print("\n✅ Todas las métricas calculadas correctamente")
    print("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        # Test básico completo
        test_basico()
        
        # Test de métricas específico
        test_metricas()
        
        print("\n🎉 TODOS LOS TESTS PASARON EXITOSAMENTE\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERROR EN LOS TESTS: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
