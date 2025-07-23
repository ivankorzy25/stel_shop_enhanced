# INSTRUCCIONES PARA CLINE:
# Crear archivo test_selenium_navigation.py en la raíz del proyecto
# Este script probará la navegación paso a paso

from navigation.selenium_handler import SeleniumHandler
import time
import os
from dotenv import load_dotenv

load_dotenv()


def test_navigation():
    """Prueba la navegación paso a paso en Stelorder"""

    handler = SeleniumHandler()

    try:
        # 1. Iniciar navegador
        print("1. Iniciando navegador...")
        if not handler.start_browser(headless=False):  # Visible para debug
            print("Error iniciando navegador")
            return

        # 2. Login
        print("2. Haciendo login...")
        username = os.getenv("STEL_USERNAME") or input("Usuario Stelorder: ")
        password = os.getenv("STEL_PASSWORD") or input("Contraseña: ")

        if not handler.login_to_stelorder(username, password):
            print("Error en login")
            return

        print("✅ Login exitoso")
        time.sleep(2)

        # 3. Navegar al catálogo
        print("3. Navegando al catálogo...")
        handler.driver.get("https://app.stelorder.com/app/#main_catalogo")
        time.sleep(5)

        # 4. Buscar un producto de prueba
        sku_test = input("Ingresa un SKU para probar: ")
        print(f"4. Buscando producto {sku_test}...")

        # Buscar el campo de búsqueda
        try:
            # Intenta diferentes selectores
            search_selectors = [
                "input[placeholder*='Buscar']",
                "input[type='search']",
                "#searchInput",
                ".search-input",
                "input[name='search']",
            ]

            search_field = None
            for selector in search_selectors:
                try:
                    search_field = handler.driver.find_element("css selector", selector)
                    print(f"✅ Campo de búsqueda encontrado con: {selector}")
                    break
                except:
                    continue

            if search_field:
                search_field.clear()
                search_field.send_keys(sku_test)
                search_field.send_keys("\n")  # Enter
                time.sleep(3)
            else:
                print("❌ No se encontró campo de búsqueda")

        except Exception as e:
            print(f"Error buscando: {e}")

        # 5. Esperar y analizar resultados
        print("5. Analizando página...")
        input("Presiona ENTER cuando veas el producto en pantalla...")

        # 6. Buscar pestañas o botones
        print("6. Buscando elementos de navegación...")

        # Buscar pestaña Shop
        shop_selectors = [
            "a[href*='shop']",
            "button:contains('Shop')",
            "li:contains('Shop')",
            "[data-tab='shop']",
            ".tab-shop",
        ]

        for selector in shop_selectors:
            try:
                elements = handler.driver.find_elements("css selector", selector)
                if elements:
                    print(f"✅ Encontrado elemento Shop con: {selector}")
            except:
                pass

        # Mantener abierto para inspección
        input("Presiona ENTER para cerrar el navegador...")

    except Exception as e:
        print(f"Error general: {e}")

    finally:
        handler.close_browser()


if __name__ == "__main__":
    test_navigation()
