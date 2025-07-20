"""
Archivo principal que inicia todo automáticamente
Ejecutar este archivo para lanzar el sistema completo
"""

import webbrowser
import time
import os
import sys
import threading

def open_browser():
    """Abre el navegador después de un delay"""
    time.sleep(3)
    print("🌐 Abriendo navegador...")
    webbrowser.open("http://localhost:5000/showcase")

def main():
    print("🚀 Iniciando STEL Shop Enhanced...")
    
    # Cambiar al directorio correcto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Iniciar thread para abrir navegador
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Importar y ejecutar la aplicación directamente
    print("📦 Iniciando servidor Flask...")
    
    try:
        import quick_integration
        quick_integration.initialize_app()
        
        print("\n✅ Sistema iniciado!")
        print("📋 Presiona Ctrl+C para detener\n")
        
        # Ejecutar Flask directamente (esto bloqueará hasta Ctrl+C)
        quick_integration.app.run(debug=False, port=5000, host='127.0.0.1')
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
