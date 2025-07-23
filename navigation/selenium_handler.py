"""
Manejador de Selenium para STEL Shop Manager
Automatiza la actualización de productos en Stelorder
"""

import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import threading


class SeleniumHandler:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.is_processing = False
        self.current_product = None
        self.processed_count = 0
        self.error_count = 0
        self.total_products = 0
        self.processing_thread = None
        self.stop_processing = False
        self.pause_processing = False

        # Configuración
        self.config = {
            "login_url": "https://stelorder.com/login",
            "products_url": "https://stelorder.com/products",
            "timeout": 30,
            "delay_between_products": 2,
        }

        # Estado para UI
        self.status = {
            "browser_active": False,
            "logged_in": False,
            "processing": False,
            "current_product": None,
            "progress": 0,
            "processed": 0,
            "errors": 0,
            "total": 0,
        }

    def start_browser(self, headless=False):
        """Inicia el navegador Chrome"""
        try:
            print("🌐 Iniciando Chrome...")

            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Perfil persistente para mantener login
            profile_dir = os.path.join(os.getcwd(), "chrome_profile")
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile_dir}")

            if headless:
                options.add_argument("--headless")

            # Ventana de tamaño específico
            options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)

            self.status["browser_active"] = True
            print("✅ Chrome iniciado correctamente")

            return True

        except Exception as e:
            print(f"❌ Error iniciando Chrome: {e}")
            self.status["browser_active"] = False
            return False

    def login_to_stelorder(self, username=None, password=None):
        """Realiza login en Stelorder"""
        try:
            print("🔐 Navegando a Stelorder...")
            self.driver.get(self.config["login_url"])
            time.sleep(2)

            # Verificar si ya está logueado
            if self.check_login_status():
                print("✅ Ya está logueado")
                self.is_logged_in = True
                self.status["logged_in"] = True
                return True

            if not username or not password:
                print("⚠️ Credenciales no proporcionadas")
                print("   Por favor, realiza el login manualmente")
                return False

            # Buscar campos de login
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(
                By.XPATH, "//button[@type='submit']"
            )

            # Completar y enviar
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            login_button.click()
            time.sleep(3)

            # Verificar login exitoso
            if self.check_login_status():
                print("✅ Login exitoso")
                self.is_logged_in = True
                self.status["logged_in"] = True
                return True
            else:
                print("❌ Login fallido")
                return False

        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False

    def check_login_status(self):
        """Verifica si está logueado"""
        try:
            # Buscar elemento que solo aparece cuando está logueado
            self.driver.find_element(By.CLASS_NAME, "user-menu")
            return True
        except:
            return False

    def navigate_to_product(self, sku):
        """Navega a la página de edición de un producto"""
        try:
            # Ir a lista de productos
            self.driver.get(f"{self.config['products_url']}/edit/{sku}")
            time.sleep(2)

            # Verificar que cargó la página correcta
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "product-form"))
            )

            return True

        except Exception as e:
            print(f"❌ Error navegando al producto {sku}: {e}")
            return False

    def navigate_to_catalog(self):
        """Navega al catálogo con la lógica específica de Stelorder"""
        try:
            self.log("🔄 NAVEGACIÓN FORZADA al catálogo...")

            # 1. Limpiar completamente la sesión
            self.driver.get("about:blank")
            time.sleep(1)

            # 2. Navegar directamente al catálogo
            self.driver.get("https://app.stelorder.com/app/#main_catalogo")
            time.sleep(5)

            # 3. Forzar refresco
            self.driver.refresh()
            time.sleep(3)

            # 4. Hacer clic en la pestaña Catálogo
            catalogo_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@id='ui-id-2']"))
            )
            self.driver.execute_script("arguments[0].click();", catalogo_btn)
            time.sleep(3)

            # 5. Verificar que el buscador está disponible
            buscador = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[contains(@class, 'buscadorListado')]")
                )
            )

            # Limpiar buscador
            self.driver.execute_script("arguments[0].value = '';", buscador)
            buscador.clear()

            return True

        except Exception as e:
            print(f"❌ Error navegando al catálogo: {e}")
            return False

    def search_product(self, codigo_producto):
        """Busca un producto específico en el catálogo"""
        try:
            # Encontrar buscador
            buscador = self.driver.find_element(
                By.XPATH, "//input[contains(@class, 'buscadorListado')]"
            )

            # Limpiar con doble método
            buscador.clear()
            self.driver.execute_script("arguments[0].value = '';", buscador)
            time.sleep(0.5)

            # Escribir letra por letra
            for letra in str(codigo_producto):
                buscador.send_keys(letra)
                time.sleep(0.05)

            time.sleep(2)  # Esperar resultados

            # Hacer clic en el primer resultado
            primer_fila = self.driver.find_element(
                By.XPATH, "//td[@class='tdTextoLargo tdBold']"
            )
            self.driver.execute_script("arguments[0].click();", primer_fila)
            time.sleep(3)

            return True

        except Exception as e:
            print(f"❌ Error buscando producto {codigo_producto}: {e}")
            return False

    def navigate_to_shop_tab(self):
        """Navega a la pestaña Shop del producto"""
        try:
            shop_tab = self.driver.find_element(By.XPATH, "//a[@id='ui-id-31']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", shop_tab)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", shop_tab)
            time.sleep(3)
            return True

        except Exception as e:
            print(f"❌ Error navegando a pestaña Shop: {e}")
            return False

    def click_edit_shop(self):
        """Hace clic en el botón Editar Shop"""
        try:
            editar_btn = self.driver.find_element(By.XPATH, "//*[@id='editarShop']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", editar_btn)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", editar_btn)
            time.sleep(3)
            return True

        except Exception as e:
            print(f"❌ Error haciendo clic en Editar Shop: {e}")
            return False

    def update_product_description(self, product_data, description_html):
        """Actualiza la descripción de un producto en el modal de Stelorder"""
        try:
            # Esperar que aparezca el modal
            modal = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.ID, "editarObjetoCatalogoConfiguracionShop_dialog")
                )
            )

            # Mostrar campos SEO si están ocultos
            try:
                mostrar_seo = modal.find_element(
                    By.ID, "trMostrarOcultarCamposSeoShopTable"
                )
                self.driver.execute_script("arguments[0].click();", mostrar_seo)
                time.sleep(1)
            except:
                pass

            # 1. Actualizar Descripción simple
            try:
                desc_input = modal.find_element(By.ID, "descriptionShop")
                desc_input.clear()
                self.driver.execute_script("arguments[0].value = '';", desc_input)

                # Si hay descripción simple en product_data
                descripcion_simple = product_data.get(
                    "descripcion", product_data.get("nombre", "")
                )
                for linea in descripcion_simple.split("\n"):
                    desc_input.send_keys(linea)
                    desc_input.send_keys(Keys.SHIFT + Keys.ENTER)
                    time.sleep(0.05)

            except Exception as e:
                print(f"⚠️ Error actualizando descripción simple: {e}")

            # 2. Actualizar Descripción Detallada (HTML en CKEditor)
            try:
                iframe = modal.find_element(By.CSS_SELECTOR, "iframe.cke_wysiwyg_frame")
                self.driver.switch_to.frame(iframe)

                body = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Limpiar contenido existente
                self.driver.execute_script("arguments[0].innerHTML = '';", body)
                time.sleep(0.5)

                # Insertar nuevo HTML
                self.driver.execute_script(
                    "arguments[0].innerHTML = arguments[1];", body, description_html
                )

                # Disparar eventos para que CKEditor registre el cambio
                self.driver.execute_script(
                    """
                    var event = new Event('input', { bubbles: true });
                    arguments[0].dispatchEvent(event);
                    var changeEvent = new Event('change', { bubbles: true });
                    arguments[0].dispatchEvent(changeEvent);
                """,
                    body,
                )

                time.sleep(1)
                self.driver.switch_to.default_content()

            except Exception as e:
                print(f"⚠️ Error actualizando descripción detallada: {e}")
                self.driver.switch_to.default_content()

            # 3. Actualizar campos SEO
            self.update_seo_fields(product_data)

            # 4. Actualizar Destacado
            try:
                destacado = product_data.get("destacado", "no").lower()
                if destacado in ["si", "sí", "yes", "1", "true"]:
                    checkbox = modal.find_element(By.ID, "destacadoShop")
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
                else:
                    checkbox = modal.find_element(By.ID, "destacadoShop")
                    if checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
            except:
                pass

            # 5. Guardar cambios
            try:
                # Buscar botón guardar con múltiples selectores
                guardar_btn = None
                for selector in [
                    "button.opcionMenuGuardar.primaryButton",
                    "button[onclick*='guardar']",
                    "button:contains('Guardar')",
                ]:
                    try:
                        if selector == "button:contains('Guardar')":
                            buttons = modal.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if "Guardar" in btn.text:
                                    guardar_btn = btn
                                    break
                        else:
                            guardar_btn = modal.find_element(By.CSS_SELECTOR, selector)
                        if guardar_btn:
                            break
                    except:
                        continue

                if guardar_btn:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", guardar_btn
                    )
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", guardar_btn)

                    # Esperar que el modal se cierre
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element_located(
                            (By.ID, "editarObjetoCatalogoConfiguracionShop_dialog")
                        )
                    )
                    time.sleep(3)
                    return True
                else:
                    print("❌ No se encontró el botón Guardar")
                    return False

            except Exception as e:
                print(f"❌ Error al guardar: {e}")
                return False

        except Exception as e:
            print(f"❌ Error en update_product_description: {e}")
            return False

    def update_seo_fields(self, product_data):
        """Actualiza campos SEO en el modal"""
        try:
            modal = self.driver.find_element(
                By.ID, "editarObjetoCatalogoConfiguracionShop_dialog"
            )
            seo_data = product_data.get("seo", {})

            # SEO Título
            try:
                seo_titulo_input = modal.find_element(By.ID, "tituloSeoShop")
                seo_titulo_input.clear()
                self.driver.execute_script("arguments[0].value = '';", seo_titulo_input)
                seo_titulo = seo_data.get("title", "") or product_data.get(
                    "seo_titulo", ""
                )
                if seo_titulo:
                    seo_titulo_input.send_keys(seo_titulo)
            except:
                pass

            # SEO Descripción
            try:
                seo_desc_input = modal.find_element(By.ID, "descripcionSeoShop")
                seo_desc_input.clear()
                self.driver.execute_script("arguments[0].value = '';", seo_desc_input)
                seo_desc = seo_data.get("description", "") or product_data.get(
                    "seo_descripcion", ""
                )
                if seo_desc:
                    seo_desc_input.send_keys(seo_desc)
            except:
                pass

        except Exception as e:
            print(f"⚠️ Error actualizando campos SEO: {e}")

    def navigate_to_product(self, sku):
        """MÉTODO ANTIGUO - Redirige al nuevo flujo"""
        # Navegar al catálogo
        if not self.navigate_to_catalog():
            return False

        # Buscar producto
        if not self.search_product(sku):
            return False

        # Ir a pestaña Shop
        if not self.navigate_to_shop_tab():
            return False

        # Hacer clic en Editar
        return self.click_edit_shop()

    def _process_products_thread(self, products, generate_description_callback):
        """Thread de procesamiento usando la navegación específica de Stelorder"""
        print(f"🚀 Iniciando procesamiento de {len(products)} productos")

        for index, product in enumerate(products):
            if self.stop_processing:
                print("🛑 Procesamiento detenido por el usuario")
                break

            while self.pause_processing:
                time.sleep(1)

            try:
                self.current_product = product
                self.status["current_product"] = product.get("nombre", "")
                self.status["progress"] = int((index / self.total_products) * 100)

                print(
                    f"\n📦 Procesando {index + 1}/{self.total_products}: {product.get('nombre')}"
                )

                # PASO 1: Navegar al catálogo (siempre para cada producto)
                print("   🔄 Navegando al catálogo...")
                if not self.navigate_to_catalog():
                    self.error_count += 1
                    continue

                # PASO 2: Buscar el producto
                sku = product.get("sku") or product.get("codigo")
                print(f"   🔍 Buscando producto: {sku}")
                if not self.search_product(sku):
                    self.error_count += 1
                    continue

                # PASO 3: Ir a pestaña Shop
                print("   📑 Abriendo pestaña Shop...")
                if not self.navigate_to_shop_tab():
                    self.error_count += 1
                    continue

                # PASO 4: Hacer clic en Editar Shop
                print("   ✏️ Abriendo editor...")
                if not self.click_edit_shop():
                    self.error_count += 1
                    continue

                # PASO 5: Generar descripción con IA
                print("   🤖 Generando descripción con IA...")
                description_data = generate_description_callback(product)

                if not description_data:
                    print("   ❌ No se pudo generar descripción")
                    self.error_count += 1
                    continue

                # PASO 6: Actualizar los campos
                print("   💾 Actualizando campos...")
                product_update = {
                    **product,
                    "descripcion": description_data.get("descripcion"),
                    "descripcion_detallada": description_data.get(
                        "descripcion_detallada"
                    ),
                    "seo": description_data.get("seo"),
                    "seo_titulo": description_data.get("seo", {}).get("title"),
                    "seo_descripcion": description_data.get("seo", {}).get(
                        "description"
                    ),
                }

                success = self.update_product_description(
                    product_update, description_data.get("descripcion_detallada")
                )

                if success:
                    self.processed_count += 1
                    self.status["processed"] = self.processed_count
                    print(f"   ✅ Producto actualizado exitosamente")
                else:
                    self.error_count += 1
                    self.status["errors"] = self.error_count

                # Volver al catálogo para el siguiente producto
                print("   🔄 Volviendo al catálogo...")
                self.driver.get("about:blank")
                time.sleep(1)

                # Delay entre productos
                time.sleep(self.config["delay_between_products"])

            except Exception as e:
                print(f"   ❌ Error procesando producto: {e}")
                self.error_count += 1
                self.status["errors"] = self.error_count

        # Finalizar
        self.is_processing = False
        self.status["processing"] = False
        self.current_product = None

        print(f"\n✅ Procesamiento completado:")
        print(f"   - Procesados: {self.processed_count}")
        print(f"   - Errores: {self.error_count}")
        print(f"   - Total: {self.total_products}")

    def log(self, message):
        """Método auxiliar para logging"""
        print(message)
