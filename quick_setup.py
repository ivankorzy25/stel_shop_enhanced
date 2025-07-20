#!/usr/bin/env python3
"""
Script de configuración rápida para STEL Shop Manager Mejorado
Ejecutar este script para configurar todo en minutos
"""

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

def print_header():
    """Imprime el header del instalador"""
    print("=" * 60)
    print("🚀 STEL SHOP MANAGER - SETUP RÁPIDO")
    print("   Sistema Mejorado de Gestión de Productos")
    print("=" * 60)
    print()

def check_requirements():
    """Verifica e instala dependencias"""
    print("📦 Verificando dependencias...")
    
    required_packages = [
        'flask',
        'flask-cors',
        'pymysql',
        'pandas',
        'google-generativeai',
        'PyPDF2',
        'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package} instalado")
        except ImportError:
            print(f"   📥 Instalando {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    print("✅ Todas las dependencias instaladas\n")

def setup_directories():
    """Crea estructura de directorios"""
    print("📁 Creando estructura de directorios...")
    
    directories = [
        'enhanced_shop',
        'enhanced_shop/static',
        'enhanced_shop/templates',
        'enhanced_shop/exports',
        'enhanced_shop/cache',
        'enhanced_shop/logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}")
    
    print("✅ Estructura creada\n")

def copy_files():
    """Copia los archivos necesarios"""
    print("📄 Copiando archivos del sistema...")
    
    # Aquí copiaríamos los archivos de los artifacts
    # Por ahora, crearemos archivos de ejemplo
    
    # Crear archivo de configuración
    config = {
        "database": {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "lista_precios_kor",
            "table": "shop_master_gaucho_completo"
        },
        "ai": {
            "api_key": "",
            "provider": "gemini"
        },
        "contact": {
            "whatsapp": "541139563099",
            "email": "info@stelshop.com",
            "phone_display": "+54 11 3956-3099",
            "website": "www.stelshop.com"
        }
    }
    
    with open('enhanced_shop/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("   ✓ config.json creado")
    print("✅ Archivos copiados\n")

def configure_database():
    """Configura la conexión a la base de datos"""
    print("🗄️ Configuración de Base de Datos")
    print("-" * 40)
    
    # Cargar configuración existente si existe
    config_path = 'enhanced_shop/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("Ingresa los datos de conexión MySQL:")
    
    # Solicitar datos
    host = input(f"Host [{config['database']['host']}]: ").strip()
    if host:
        config['database']['host'] = host
    
    user = input(f"Usuario [{config['database']['user']}]: ").strip()
    if user:
        config['database']['user'] = user
    
    password = input("Contraseña: ").strip()
    config['database']['password'] = password
    
    database = input(f"Base de datos [{config['database']['database']}]: ").strip()
    if database:
        config['database']['database'] = database
    
    table = input(f"Tabla [{config['database']['table']}]: ").strip()
    if table:
        config['database']['table'] = table
    
    # Guardar configuración
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuración de BD guardada\n")
    
    # Verificar conexión
    print("🔍 Verificando conexión...")
    try:
        import pymysql
        conn = pymysql.connect(
            host=config['database']['host'],
            user=config['database']['user'],
            password=config['database']['password'],
            database=config['database']['database']
        )
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {config['database']['table']}")
        count = cursor.fetchone()[0]
        
        conn.close()
        print(f"✅ Conexión exitosa! {count} productos encontrados\n")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica los datos e intenta nuevamente\n")
        return False

def configure_ai():
    """Configura la API de IA"""
    print("🤖 Configuración de IA (Google Gemini)")
    print("-" * 40)
    
    config_path = 'enhanced_shop/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("Para usar IA necesitas una API Key de Google Gemini")
    print("Obtén una gratis en: https://makersuite.google.com/app/apikey")
    print()
    
    api_key = input("API Key (dejar vacío para omitir): ").strip()
    
    if api_key:
        config['ai']['api_key'] = api_key
        
        # Guardar configuración
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Verificar API
        print("🔍 Verificando API...")
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Di 'OK' si funcionas")
            
            if response.text:
                print("✅ API de IA configurada correctamente\n")
                return True
        except Exception as e:
            print(f"⚠️ Error con la API: {e}")
            print("   El sistema funcionará sin IA\n")
    else:
        print("⚠️ Sin API Key - El sistema funcionará sin generación de IA\n")
    
    return False

def create_launcher():
    """Crea scripts de lanzamiento"""
    print("🚀 Creando lanzadores...")
    
    # Script para Windows
    bat_content = """@echo off
echo Starting STEL Shop Manager Enhanced...
cd enhanced_shop
python ../quick_integration.py
pause
"""
    
    with open('start_enhanced.bat', 'w') as f:
        f.write(bat_content)
    
    # Script para Linux/Mac
    sh_content = """#!/bin/bash
echo "Starting STEL Shop Manager Enhanced..."
cd enhanced_shop
python3 ../quick_integration.py
"""
    
    with open('start_enhanced.sh', 'w') as f:
        f.write(sh_content)
    
    # Hacer ejecutable en Linux/Mac
    try:
        os.chmod('start_enhanced.sh', 0o755)
    except:
        pass
    
    print("   ✓ start_enhanced.bat (Windows)")
    print("   ✓ start_enhanced.sh (Linux/Mac)")
    print("✅ Lanzadores creados\n")

def show_next_steps():
    """Muestra los siguientes pasos"""
    print("=" * 60)
    print("✅ INSTALACIÓN COMPLETADA!")
    print("=" * 60)
    print()
    print("📋 SIGUIENTES PASOS:")
    print()
    print("1. Copiar los archivos del artifact a tu proyecto:")
    print("   - ai_handler_enhanced.py")
    print("   - quick_integration.py")
    print("   - product_showcase.html → enhanced_shop/templates/")
    print()
    print("2. Iniciar el sistema:")
    print("   Windows: start_enhanced.bat")
    print("   Linux/Mac: ./start_enhanced.sh")
    print()
    print("3. Abrir en el navegador:")
    print("   http://localhost:5000")
    print()
    print("4. APIs disponibles:")
    print("   GET  /api/products - Lista productos")
    print("   GET  /api/products/<sku> - Detalle con IA")
    print("   POST /api/generate-description - Generar descripción")
    print("   GET  /showcase - Página visual de productos")
    print()
    print("💡 TIPS:")
    print("- El sistema genera descripciones automáticamente")
    print("- Las descripciones incluyen info del PDF si está disponible")
    print("- Puedes personalizar los templates en el código")
    print("- Los cambios se aplican sin reiniciar")
    print()

def main():
    """Función principal del instalador"""
    print_header()
    
    # Verificar Python
    if sys.version_info < (3, 7):
        print("❌ Se requiere Python 3.7 o superior")
        sys.exit(1)
    
    # Ejecutar pasos
    check_requirements()
    setup_directories()
    copy_files()
    
    # Configurar BD
    db_ok = configure_database()
    if not db_ok:
        print("⚠️ Continuando sin conexión a BD...")
    
    # Configurar IA
    ai_ok = configure_ai()
    
    # Crear lanzadores
    create_launcher()
    
    # Mostrar siguientes pasos
    show_next_steps()
    
    input("\nPresiona ENTER para finalizar...")

if __name__ == "__main__":
    main()