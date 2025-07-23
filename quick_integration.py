"""
Script de integración rápida para STEL Shop Manager Mejorado
Conecta con Cloud Function y genera descripciones mejoradas
"""

import json
import requests
import pandas as pd
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sys
import os
import time

# Agregar el path para importar los módulos existentes
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar los handlers
try:
    from ai_handler_enhanced import EnhancedAIHandler

    print("✅ Módulo AI cargado correctamente")
except ImportError as e:
    print(f"⚠️  No se pudo cargar el módulo AI: {e}")
    EnhancedAIHandler = None

try:
    from navigation.selenium_handler import SeleniumHandler

    print("✅ Módulo Selenium cargado correctamente")
except ImportError as e:
    print(f"⚠️  No se pudo cargar el módulo Selenium: {e}")
    SeleniumHandler = None

# Configuración
app = Flask(__name__)
CORS(app)

# Configuración de Cloud Function
CLOUD_FUNCTION_URL = "https://southamerica-east1-lista-precios-2025.cloudfunctions.net/actualizar-precios-v2"

# Configuración de IA
AI_CONFIG = {
    "api_key": "AIzaSyBYjaWimtWtTk3m_4SjFgLQRWPkiu0suiw",
    "whatsapp": "541139563099",
    "email": "info@stelshop.com",
    "telefono_display": "+54 11 3956-3099",
    "website": "www.stelshop.com",
}

# Instancias globales
ai_handler = None
selenium_handler = None
products_cache = []
cache_timestamp = 0


def get_products_from_cloud_function():
    """Obtiene productos desde la Cloud Function con caché de 5 minutos"""
    global products_cache, cache_timestamp

    if products_cache and (time.time() - cache_timestamp) < 300:
        return products_cache

    try:
        print("🔄 Obteniendo productos desde Cloud Function...")
        response = requests.get(CLOUD_FUNCTION_URL, timeout=30)

        if response.status_code == 200:
            data = response.json()
            products = data.get("products", []) if isinstance(data, dict) else data
            products_cache = products
            cache_timestamp = time.time()
            print(f"✅ {len(products)} productos obtenidos")
            return products
        else:
            print(f"❌ Error: Status {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error conectando con Cloud Function: {e}")
        return []


def format_product(product):
    """Formatea un producto al formato estándar"""
    return {
        "sku": product.get("SKU") or product.get("sku") or "",
        "nombre": product.get("Descripción")
        or product.get("descripcion")
        or product.get("nombre")
        or "",
        "marca": product.get("Marca") or product.get("marca") or "",
        "modelo": product.get("Modelo") or product.get("modelo") or "",
        "familia": product.get("Familia") or product.get("familia") or "",
        "precio": product.get("Precio_USD_con_IVA") or product.get("precio") or 0,
        "stock": product.get("Stock") or product.get("stock") or 0,
        "pdf_url": product.get("URL_PDF") or product.get("pdf_url") or "",
        "potencia": product.get("Potencia") or product.get("potencia") or "",
        "voltaje": product.get("Tensión") or product.get("voltaje") or "",
        "motor": product.get("Motor") or product.get("motor") or "",
        "frecuencia": product.get("Frecuencia") or product.get("frecuencia") or "",
        "consumo": product.get("Consumo_L_h") or product.get("consumo") or "",
    }


@app.route("/")
def index():
    """Página principal - redirige al showcase"""
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/showcase">
    </head>
    <body>
        <p>Redirigiendo al catálogo...</p>
    </body>
    </html>
    """


@app.route("/showcase")
def showcase():
    """Página de visualización de productos"""
    return render_template("showcase.html")


@app.route("/api/products")
def get_products():
    """Obtiene todos los productos de la Cloud Function"""
    try:
        products = get_products_from_cloud_function()
        formatted_products = [format_product(p) for p in products]

        return jsonify(
            {
                "success": True,
                "count": len(formatted_products),
                "products": formatted_products,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/products/<sku>")
def get_product_detail(sku):
    """Obtiene detalle de un producto específico"""
    try:
        products = get_products_from_cloud_function()

        product = None
        for p in products:
            if p.get("SKU") == sku or p.get("sku") == sku:
                product = p
                break

        if not product:
            return jsonify({"error": "Producto no encontrado"}), 404

        formatted_product = format_product(product)

        # Generar descripción si hay IA
        if ai_handler and product:
            try:
                formatted_product["descripcion_html"] = (
                    ai_handler.generate_enhanced_description(product, AI_CONFIG)
                )
                formatted_product["seo"] = ai_handler.generate_seo_metadata(product)
            except Exception as e:
                print(f"Error generando descripción: {e}")

        return jsonify({"success": True, "product": formatted_product})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/selenium/start", methods=["POST"])
def start_selenium():
    """Inicia el navegador Chrome"""
    if not selenium_handler:
        return jsonify({"success": False, "error": "Selenium no disponible"}), 500

    try:
        data = request.json or {}
        success = selenium_handler.start_browser(data.get("headless", False))
        return jsonify({"success": success, "status": selenium_handler.get_status()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/selenium/status")
def selenium_status():
    """Obtiene el estado de Selenium"""
    if not selenium_handler:
        return jsonify({"success": False, "error": "Selenium no disponible"}), 500

    return jsonify(selenium_handler.get_status())


@app.route("/api/selenium/login", methods=["POST"])
def selenium_login():
    """Realiza login en Stelorder"""
    if not selenium_handler:
        return jsonify({"success": False, "error": "Selenium no disponible"}), 500

    try:
        data = request.json or {}
        success = selenium_handler.login_to_stelorder(
            data.get("username"), data.get("password")
        )
        return jsonify({"success": success, "status": selenium_handler.get_status()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/selenium/confirm-login", methods=["POST"])
def confirm_selenium_login():
    """Confirma que el usuario ya realizó login manualmente"""
    if not selenium_handler:
        return jsonify({"success": False, "error": "Selenium no disponible"}), 500

    try:
        success = selenium_handler.confirm_login()
        return jsonify(
            {
                "success": success,
                "status": selenium_handler.get_status(),
                "message": (
                    "Login confirmado" if success else "No se detectó sesión activa"
                ),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/process-products", methods=["POST"])
def process_products():
    """Procesa productos con Selenium"""
    if not selenium_handler or not ai_handler:
        return jsonify({"success": False, "error": "Selenium o IA no disponibles"}), 500

    try:
        data = request.json
        products = data.get("products", [])

        if not products:
            return jsonify({"error": "No hay productos para procesar"}), 400

        if not selenium_handler.is_logged_in:
            return jsonify({"error": "Debes iniciar sesión en Stelorder primero"}), 400

        # Función para generar descripciones
        def generate_description(product):
            return ai_handler.generate_enhanced_description(product, AI_CONFIG)

        selenium_handler.process_products(products, generate_description)

        return jsonify(
            {
                "success": True,
                "message": f"Procesando {len(products)} productos",
                "status": selenium_handler.get_status(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def initialize_app():
    """Inicializa la aplicación"""
    global ai_handler, selenium_handler

    print("🚀 Inicializando STEL Shop Manager Mejorado...")

    # Inicializar IA
    if EnhancedAIHandler:
        try:
            ai_handler = EnhancedAIHandler(AI_CONFIG["api_key"])
            print("✅ IA inicializada correctamente")
        except Exception as e:
            print(f"⚠️ Error inicializando IA: {e}")

    # Inicializar Selenium
    if SeleniumHandler:
        try:
            selenium_handler = SeleniumHandler()
            print("✅ Selenium inicializado correctamente")
        except Exception as e:
            print(f"⚠️ Error inicializando Selenium: {e}")

    # Verificar conexión a Cloud Function
    print("🔍 Verificando conexión a Cloud Function...")
    products = get_products_from_cloud_function()
    if products:
        print(f"✅ Cloud Function conectada - {len(products)} productos disponibles")
    else:
        print("⚠️ No se pudieron obtener productos de Cloud Function")


if __name__ == "__main__":
    initialize_app()

    print("\n🌐 Servidor iniciando en http://127.0.0.1:5000")
    print("🎨 Showcase de productos en http://127.0.0.1:5000/showcase")

    app.run(debug=False, port=5000, host="127.0.0.1")
