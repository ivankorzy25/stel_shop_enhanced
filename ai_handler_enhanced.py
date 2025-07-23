"""
Módulo de Generación con IA Mejorado para STEL Shop
Incluye procesamiento de PDFs y generación de HTML enriquecido
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from pathlib import Path
import PyPDF2
import requests
import base64
from io import BytesIO


class EnhancedAIHandler:
    """Maneja la generación mejorada de descripciones con IA y PDFs"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.model = None
        self.module_path = Path(__file__).parent

        if api_key:
            self.initialize_model(api_key)

    def initialize_model(self, api_key: str):
        """Inicializa el modelo de Google Gemini"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.api_key = api_key
            return True
        except Exception as e:
            print(f"❌ Error inicializando modelo: {e}")
            return False

    def extract_pdf_content(self, pdf_url: str) -> Dict[str, Any]:
        """Extrae contenido relevante del PDF"""
        try:
            # Si es una URL relativa, construir la URL completa
            if not pdf_url.startswith("http"):
                pdf_url = f"https://storage.googleapis.com/fichas_tecnicas/{pdf_url}"

            # Descargar PDF
            response = requests.get(pdf_url, timeout=30)
            pdf_file = BytesIO(response.content)

            # Extraer texto
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""

            for page in pdf_reader.pages[:5]:  # Primeras 5 páginas
                text_content += page.extract_text() + "\n"

            # Buscar especificaciones técnicas
            specs = self._extract_specifications(text_content)

            return {
                "success": True,
                "text": text_content[:3000],  # Limitar para el prompt
                "specifications": specs,
                "page_count": len(pdf_reader.pages),
            }

        except Exception as e:
            print(f"⚠️ Error extrayendo PDF: {e}")
            return {"success": False, "text": "", "specifications": {}}

    def _extract_specifications(self, text: str) -> Dict[str, str]:
        """Extrae especificaciones técnicas del texto"""
        specs = {}

        # Patrones comunes en fichas técnicas
        patterns = {
            "potencia": r"(?:potencia|power).*?(\d+\.?\d*)\s*(?:kva|kw)",
            "voltaje": r"(?:voltaje|voltage|tensión).*?(\d+)\s*v",
            "frecuencia": r"(?:frecuencia|frequency).*?(\d+)\s*hz",
            "motor": r"(?:motor|engine).*?([A-Za-z0-9\s\-]+)",
            "consumo": r"(?:consumo|consumption).*?(\d+\.?\d*)\s*(?:l/h|lph)",
            "dimensiones": r"(?:dimensiones|dimensions).*?(\d+)\s*x\s*(\d+)\s*x\s*(\d+)",
            "peso": r"(?:peso|weight).*?(\d+\.?\d*)\s*(?:kg|kilos)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specs[key] = (
                    match.group(1)
                    if key != "dimensiones"
                    else f"{match.group(1)}x{match.group(2)}x{match.group(3)}"
                )

        return specs

    def generar_descripcion_detallada_html_premium_con_ia(
        self, product_info: Dict, config: Dict
    ) -> Dict:
        """
        Genera TODAS las descripciones usando IA obligatoriamente
        Retorna un diccionario con todo el contenido necesario
        """

        # Paso 1: Extraer contenido del PDF
        pdf_url = product_info.get("pdf_url", "")
        texto_pdf = ""
        especificaciones_pdf = {}

        if pdf_url:
            if not pdf_url.startswith("http"):
                pdf_url = f"https://storage.googleapis.com/fichas_tecnicas/{pdf_url}"

            contenido_pdf = self.extract_pdf_content(pdf_url)
            texto_pdf = contenido_pdf.get("text", "")
            especificaciones_pdf = contenido_pdf.get("specifications", {})

        # Paso 2: Combinar toda la información
        info_completa = {**product_info, **especificaciones_pdf}

        # Valores de contacto por defecto
        whatsapp = config.get("whatsapp", "541139563099")
        email = config.get("email", "info@generadores.ar")
        telefono_display = config.get("telefono_display", "+54 11 3956-3099")
        website = config.get("website", "www.generadores.ar")

        # Paso 3: Crear prompt detallado para la IA
        prompt = f"""
        Eres un experto en marketing de equipos industriales y desarrollo web.
        
        PRODUCTO: {info_completa.get('nombre', 'Producto')}
        
        ESPECIFICACIONES TÉCNICAS:
        - SKU: {info_completa.get('sku', '')}
        - Marca: {info_completa.get('marca', '')}
        - Modelo: {info_completa.get('modelo', '')}
        - Familia: {info_completa.get('familia', '')}
        - Potencia: {info_completa.get('potencia_kva', '')} KVA
        - Motor: {info_completa.get('motor', '')}
        - Consumo: {info_completa.get('consumo', '')} L/h
        - Tanque: {info_completa.get('tanque', '')} L
        - Voltaje: {info_completa.get('voltaje', '')} V
        - Frecuencia: {info_completa.get('frecuencia', '')} Hz
        - Dimensiones: {info_completa.get('largo', '')}x{info_completa.get('ancho', '')}x{info_completa.get('alto', '')} mm
        - Peso: {info_completa.get('peso', '')} kg
        
        INFORMACIÓN ADICIONAL DEL PDF:
        {texto_pdf[:1500]}
        
        DATOS DE CONTACTO A USAR:
        - WhatsApp: {whatsapp}
        - Email: {email}
        - Teléfono: {telefono_display}
        - Website: {website}
        
        GENERA UN JSON con estos 4 elementos:
        
        1. "descripcion": Descripción técnica en texto plano (8-10 líneas) siguiendo este formato EXACTO:
           ========================================
           [MARCA] [MODELO]
           ========================================
           
           [ CAPACIDAD NOMINAL ]
           - Potencia: [X] KVA / [Y] KW
           - Tensión: [V] V
           - Frecuencia: [Hz] Hz
           
           [ CONJUNTO MOTOR-GENERADOR ]
           - Motor: [Marca y modelo]
           - Alternador: [Tipo]
           
           [ CONSUMO Y AUTONOMÍA ]
           - Consumo al 75%: [X] L/h
           - Capacidad tanque: [X] L
           - Autonomía estimada: [X] horas
           
           [ APLICACIONES ]
           - [Lista de aplicaciones principales]
        
        2. "descripcion_html": HTML COMPLETO con este diseño EXACTO (IMPORTANTE: todos los estilos deben ser inline):
           
           <div style="font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; background: #fafafa; padding: 20px;">
               
               <!-- HEADER HERO -->
               <div style="background: linear-gradient(135deg, #ff6600, #ff8833); border-radius: 15px; padding: 30px; text-align: center; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(255,102,0,0.3);">
                   <h1 style="color: white; font-size: 32px; margin: 0 0 10px 0; text-transform: uppercase; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                       [NOMBRE COMPLETO DEL PRODUCTO]
                   </h1>
                   <p style="color: white; font-size: 18px; margin: 0; opacity: 0.95;">
                       Solucion energetica profesional de ultima generacion
                   </p>
               </div>
               
               <!-- ESPECIFICACIONES PRINCIPALES EN CARDS -->
               <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;">
                   
                   <!-- Card Potencia -->
                   <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                       <div style="display: flex; align-items: center; gap: 15px;">
                           <div style="width: 50px; height: 50px; background: #ffe8cc; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                               <svg width="28" height="28" viewBox="0 0 24 24" fill="#ff6600"><path d="M7 2v11h3v9l7-12h-4l4-8z"/></svg>
                           </div>
                           <div>
                               <h4 style="margin: 0; color: #666; font-size: 14px; text-transform: uppercase;">Potencia</h4>
                               <p style="margin: 5px 0 0 0; font-size: 22px; font-weight: bold; color: #ff6600;">[POTENCIA] KVA</p>
                           </div>
                       </div>
                   </div>
                   
                   <!-- Card Motor -->
                   <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                       <div style="display: flex; align-items: center; gap: 15px;">
                           <div style="width: 50px; height: 50px; background: #ffe8cc; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                               <svg width="28" height="28" viewBox="0 0 24 24" fill="#ff6600"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg>
                           </div>
                           <div>
                               <h4 style="margin: 0; color: #666; font-size: 14px; text-transform: uppercase;">Motor</h4>
                               <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold; color: #333;">[MOTOR]</p>
                           </div>
                       </div>
                   </div>
                   
                   <!-- Card Combustible -->
                   <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                       <div style="display: flex; align-items: center; gap: 15px;">
                           <div style="width: 50px; height: 50px; background: #ffe8cc; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                               <svg width="28" height="28" viewBox="0 0 24 24" fill="#333"><path d="M12 2C8.13 2 5 5.13 5 9c0 1.88.79 3.56 2 4.78V22h10v-8.22c1.21-1.22 2-2.9 2-4.78 0-3.87-3.13-7-7-7zm0 2c2.76 0 5 2.24 5 5s-2.24 5-5 5-5-2.24-5-5 2.24-5 5-5z"/></svg>
                           </div>
                           <div>
                               <h4 style="margin: 0; color: #666; font-size: 14px; text-transform: uppercase;">Combustible</h4>
                               <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold; color: #333;">Diesel</p>
                               <p style="margin: 0; font-size: 14px; color: #999;">[CONSUMO] L/h</p>
                           </div>
                       </div>
                   </div>
                   
               </div>
               
               <!-- TABLA DE ESPECIFICACIONES -->
               <div style="background-color: #FFC107; border: 3px solid #000000; border-radius: 10px; padding: 25px; margin-bottom: 30px;">
                   <h2 style="color: #000000; font-size: 24px; margin: 0 0 20px 0; text-align: center;">
                       ESPECIFICACIONES TECNICAS COMPLETAS
                   </h2>
                   <table style="width: 100%; background-color: white; border-radius: 8px; overflow: hidden;">
                       [GENERAR FILAS DE ESPECIFICACIONES CON TODOS LOS DATOS DISPONIBLES]
                       <!-- Ejemplo de fila:
                       <tr style="background-color: #f9f9f9;">
                           <td style="padding: 12px; font-weight: bold; color: #D32F2F;">POTENCIA</td>
                           <td style="padding: 12px; font-weight: bold;">[VALOR] KVA</td>
                       </tr>
                       -->
                   </table>
               </div>
               
               <!-- SECCIONES DEL SPEECH DE VENTA -->
               <div style="background: white; border-radius: 10px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #FFC107;">
                   <h3 style="color: #D32F2F; font-size: 22px; margin: 0 0 15px 0;">POTENCIA Y RENDIMIENTO SUPERIOR</h3>
                   <p style="font-size: 16px; line-height: 1.8; color: #333;">
                       [Descripción persuasiva sobre la potencia y rendimiento del equipo]
                   </p>
               </div>
               
               <div style="background: white; border-radius: 10px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #FFC107;">
                   <h3 style="color: #D32F2F; font-size: 22px; margin: 0 0 15px 0;">ECONOMIA OPERATIVA GARANTIZADA</h3>
                   <p style="font-size: 16px; line-height: 1.8; color: #333;">
                       [Descripción sobre el consumo y autonomía]
                   </p>
               </div>
               
               <div style="background: white; border-radius: 10px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 5px solid #FFC107;">
                   <h3 style="color: #D32F2F; font-size: 22px; margin: 0 0 15px 0;">APLICACIONES IDEALES</h3>
                   <ul style="font-size: 16px; line-height: 1.8; color: #333; margin: 0; padding-left: 20px;">
                       <li>Industrias y fabricas que requieren energia constante</li>
                       <li>Comercios y centros de atencion al publico</li>
                       <li>Hospitales y centros de salud</li>
                       <li>Eventos y espectaculos al aire libre</li>
                       <li>Respaldo para sistemas criticos</li>
                   </ul>
               </div>
               
               <!-- VENTAJAS EN CARDS -->
               <div style="margin: 30px 0;">
                   <h3 style="text-align: center; font-size: 28px; color: #333; margin-bottom: 30px;">
                       POR QUE ELEGIR ESTE GENERADOR
                   </h3>
                   <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                       
                       <div style="background: white; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #ff6600;">
                           <h4 style="margin: 0 0 10px 0; color: #333;">GARANTIA OFICIAL</h4>
                           <p style="margin: 0; color: #666; font-size: 14px;">Respaldo total del fabricante con garantia extendida</p>
                       </div>
                       
                       <div style="background: white; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #ff6600;">
                           <h4 style="margin: 0 0 10px 0; color: #333;">CALIDAD CERTIFICADA</h4>
                           <p style="margin: 0; color: #666; font-size: 14px;">Cumple con todas las normas internacionales</p>
                       </div>
                       
                       <div style="background: white; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #ff6600;">
                           <h4 style="margin: 0 0 10px 0; color: #333;">SERVICIO TECNICO</h4>
                           <p style="margin: 0; color: #666; font-size: 14px;">Red nacional de servicio y repuestos originales</p>
                       </div>
                       
                       <div style="background: white; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #ff6600;">
                           <h4 style="margin: 0 0 10px 0; color: #333;">FINANCIACION</h4>
                           <p style="margin: 0; color: #666; font-size: 14px;">Multiples opciones de pago y financiacion a medida</p>
                       </div>
                       
                   </div>
               </div>
               
               <!-- BOTONES DE ACCION -->
               <div style="background: linear-gradient(135deg, #000000, #333333); padding: 40px; border-radius: 15px; text-align: center; margin: 40px 0; box-shadow: 0 5px 20px rgba(0,0,0,0.3);">
                   <h3 style="color: #FFC107; font-size: 28px; margin-bottom: 10px; text-transform: uppercase;">
                       TOME ACCION AHORA
                   </h3>
                   <p style="color: white; font-size: 16px; margin-bottom: 30px; opacity: 0.9;">
                       No pierda esta oportunidad. Consulte con nuestros especialistas hoy mismo.
                   </p>
                   
                   <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">
                       
                       <a href="https://wa.me/{whatsapp}?text=Hola%2C%20vengo%20de%20ver%20el%20[NOMBRE_PRODUCTO]%20en%20la%20tienda%20de%20Stelorder%20y%20quisiera%20mas%20informacion%20sobre%20este%20producto" target="_blank" 
                          style="display: inline-flex; align-items: center; gap: 10px; background-color: #25d366; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px;">
                           CONSULTAR POR WHATSAPP
                       </a>
                       
                       <a href="{pdf_url}" target="_blank" 
                          style="display: inline-flex; align-items: center; gap: 10px; background-color: #FFC107; color: #000000; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px;">
                           DESCARGAR FICHA TECNICA
                       </a>
                       
                       <a href="mailto:{email}?subject=Consulta%20desde%20Stelorder%20-%20[NOMBRE_PRODUCTO]&body=Hola%2C%0A%0AVengo%20de%20ver%20el%20[NOMBRE_PRODUCTO]%20en%20la%20tienda%20de%20Stelorder%20y%20quisiera%20mas%20informacion%20sobre%20este%20producto.%0A%0AQuedo%20a%20la%20espera%20de%20su%20respuesta.%0A%0ASaludos" 
                          style="display: inline-flex; align-items: center; gap: 10px; background-color: #D32F2F; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px;">
                           SOLICITAR COTIZACION
                       </a>
                       
                   </div>
               </div>
               
               <!-- INFORMACION DE CONTACTO -->
               <div style="background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;">
                   <h4 style="color: #333; font-size: 24px; margin-bottom: 20px;">CONTACTO DIRECTO</h4>
                   
                   <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 30px;">
                       
                       <div style="display: flex; align-items: center; gap: 10px;">
                           <div style="text-align: left;">
                               <p style="margin: 0; color: #666; font-size: 12px;">Telefono / WhatsApp</p>
                               <a href="https://wa.me/{whatsapp}" style="color: #ff6600; text-decoration: none; font-weight: bold;">{telefono_display}</a>
                           </div>
                       </div>
                       
                       <div style="display: flex; align-items: center; gap: 10px;">
                           <div style="text-align: left;">
                               <p style="margin: 0; color: #666; font-size: 12px;">Email</p>
                               <a href="mailto:{email}" style="color: #ff6600; text-decoration: none; font-weight: bold;">{email}</a>
                           </div>
                       </div>
                       
                       <div style="display: flex; align-items: center; gap: 10px;">
                           <div style="text-align: left;">
                               <p style="margin: 0; color: #666; font-size: 12px;">Sitio Web</p>
                               <a href="https://{website}" target="_blank" style="color: #ff6600; text-decoration: none; font-weight: bold;">{website}</a>
                           </div>
                       </div>
                       
                   </div>
               </div>
               
           </div>
        
        3. "seo_titulo": Título SEO optimizado (máximo 60 caracteres)
           Ejemplo: "Generador [MARCA] [POTENCIA]KVA - Mejor Precio | Stelorder"
        
        4. "seo_descripcion": Meta descripción SEO (máximo 160 caracteres)
           Ejemplo: "Grupo electrógeno [MARCA] de [POTENCIA]KVA. Motor [MOTOR], consumo [X]L/h. Garantía oficial. Consulte precio y financiación."
        
        IMPORTANTE:
        - Reemplaza TODOS los placeholders [CAMPO] con los datos reales
        - El HTML debe estar completo y listo para usar
        - NO uses emojis
        - Mantén EXACTAMENTE la estructura mostrada
        
        Responde SOLO con el JSON, sin explicaciones adicionales.
        """

        try:
            # Llamar a la IA
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 8000,
                },
            )

            # Parsear respuesta
            texto_respuesta = response.text.strip()
            # Limpiar posibles marcadores de código
            texto_respuesta = re.sub(r"^```json\s*", "", texto_respuesta)
            texto_respuesta = re.sub(r"\s*```$", "", texto_respuesta)

            resultado = json.loads(texto_respuesta)

            # Validar que tenga todos los campos
            campos_requeridos = [
                "descripcion",
                "descripcion_html",
                "seo_titulo",
                "seo_descripcion",
            ]
            for campo in campos_requeridos:
                if campo not in resultado:
                    raise ValueError(f"Falta el campo {campo} en la respuesta de IA")

            return resultado

        except Exception as e:
            print(f"❌ Error generando con IA: {e}")
            raise Exception(f"Error crítico en generación IA: {e}")

    def _generate_with_ai(
        self, product_info: Dict, pdf_content: Dict, config: Dict
    ) -> str:
        """Genera descripción usando IA con contexto del PDF"""

        prompt = f"""
        Eres un experto en marketing de productos industriales. Genera una descripción HTML COMPLETA y ATRACTIVA para el siguiente producto.
        
        INFORMACIÓN DEL PRODUCTO:
        - Nombre: {product_info.get('nombre', 'Producto')}
        - Marca: {product_info.get('marca', '')}
        - Modelo: {product_info.get('modelo', '')}
        - Familia: {product_info.get('familia', '')}
        
        ESPECIFICACIONES TÉCNICAS:
        {json.dumps(product_info, indent=2, ensure_ascii=False)}
        
        INFORMACIÓN ADICIONAL DEL PDF:
        {pdf_content.get('text', '')[:1500]}
        
        INSTRUCCIONES:
        1. Crea una descripción HTML completa con estas secciones:
           - Header atractivo con el nombre del producto
           - Descripción general (2-3 párrafos persuasivos)
           - Características destacadas (lista visual)
           - Especificaciones técnicas (tabla organizada)
           - Aplicaciones principales
           - Beneficios clave
           - Call to action
        
        2. Usa este estilo moderno:
           - Colores: #ff6600 (naranja), #333 (texto), #f8f9fa (fondos)
           - Íconos con emojis relevantes
           - Diseño con cards y sombras suaves
           - Tipografía clara y jerarquizada
        
        3. El HTML debe ser autónomo con estilos inline
        4. Hazlo visualmente atractivo y profesional
        5. Resalta los beneficios y valor del producto
        
        IMPORTANTE: Devuelve SOLO el código HTML, sin explicaciones.
        """

        try:
            response = self.model.generate_content(prompt)
            html = response.text.strip()

            # Limpiar respuesta
            html = re.sub(r"^```html\s*", "", html)
            html = re.sub(r"\s*```$", "", html)

            # Agregar información de contacto
            html = self._add_contact_section(html, config)

            return html

        except Exception as e:
            print(f"⚠️ Error generando con IA: {e}")
            return self._generate_fallback_enhanced(product_info, config)

    def _generate_fallback_enhanced(self, product_info: Dict, config: Dict) -> str:
        """Genera una descripción HTML atractiva sin IA"""

        nombre = product_info.get("nombre", "Producto")
        marca = product_info.get("marca", "")
        modelo = product_info.get("modelo", "")
        precio = product_info.get("precio", 0)

        # Especificaciones disponibles
        specs_html = ""
        spec_fields = {
            "potencia": "Potencia",
            "voltaje": "Voltaje",
            "frecuencia": "Frecuencia",
            "motor": "Motor",
            "consumo": "Consumo",
            "peso": "Peso",
            "dimensiones": "Dimensiones",
        }

        for field, label in spec_fields.items():
            if product_info.get(field):
                specs_html += f"""
                <tr>
                    <td style="font-weight: bold; padding: 10px; border-bottom: 1px solid #eee;">{label}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{product_info[field]}</td>
                </tr>
                """

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; background: #fff;">
            
            <!-- Header del Producto -->
            <div style="background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%); color: white; padding: 30px; border-radius: 15px 15px 0 0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1 style="margin: 0; font-size: 2.5em; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                    {nombre.upper()}
                </h1>
                {f'<p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.95;">{marca} - {modelo}</p>' if marca or modelo else ''}
            </div>
            
            <!-- Descripción Principal -->
            <div style="padding: 30px; background: #f8f9fa; border-radius: 0 0 15px 15px;">
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h2 style="color: #ff6600; margin-bottom: 15px; font-size: 1.8em;">
                        <span style="margin-right: 10px;">🎯</span>Descripción General
                    </h2>
                    <p style="line-height: 1.8; color: #555; font-size: 1.1em; margin-bottom: 15px;">
                        El <strong>{nombre}</strong> es un equipo de alta calidad diseñado para satisfacer las necesidades más exigentes del mercado. 
                        Con tecnología de vanguardia y construcción robusta, este producto garantiza un rendimiento excepcional y durabilidad superior.
                    </p>
                    <p style="line-height: 1.8; color: #555; font-size: 1.1em;">
                        Fabricado por <strong>{marca}</strong>, líder reconocido en el sector, este modelo combina innovación, 
                        eficiencia y confiabilidad para brindar una solución integral a sus requerimientos.
                    </p>
                </div>
                
                <!-- Características Destacadas -->
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h2 style="color: #ff6600; margin-bottom: 20px; font-size: 1.8em;">
                        <span style="margin-right: 10px;">⭐</span>Características Destacadas
                    </h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        <div style="padding: 15px; background: #fff3e0; border-radius: 8px; border-left: 4px solid #ff6600;">
                            <strong style="color: #ff6600;">✓ Alta Eficiencia</strong>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.95em;">Optimización máxima de recursos</p>
                        </div>
                        <div style="padding: 15px; background: #fff3e0; border-radius: 8px; border-left: 4px solid #ff6600;">
                            <strong style="color: #ff6600;">✓ Durabilidad Garantizada</strong>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.95em;">Construcción robusta y confiable</p>
                        </div>
                        <div style="padding: 15px; background: #fff3e0; border-radius: 8px; border-left: 4px solid #ff6600;">
                            <strong style="color: #ff6600;">✓ Fácil Mantenimiento</strong>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.95em;">Diseño accesible y práctico</p>
                        </div>
                        <div style="padding: 15px; background: #fff3e0; border-radius: 8px; border-left: 4px solid #ff6600;">
                            <strong style="color: #ff6600;">✓ Soporte Técnico</strong>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.95em;">Asistencia profesional garantizada</p>
                        </div>
                    </div>
                </div>
                
                <!-- Especificaciones Técnicas -->
                {f'''
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h2 style="color: #ff6600; margin-bottom: 20px; font-size: 1.8em;">
                        <span style="margin-right: 10px;">📊</span>Especificaciones Técnicas
                    </h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        {specs_html}
                    </table>
                </div>
                ''' if specs_html else ''}
                
                <!-- Aplicaciones -->
                <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h2 style="color: #ff6600; margin-bottom: 20px; font-size: 1.8em;">
                        <span style="margin-right: 10px;">🏭</span>Aplicaciones Principales
                    </h2>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <span style="color: #ff6600; font-size: 1.2em; margin-right: 10px;">▸</span>
                            <strong>Industria:</strong> Ideal para procesos productivos continuos
                        </li>
                        <li style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <span style="color: #ff6600; font-size: 1.2em; margin-right: 10px;">▸</span>
                            <strong>Comercio:</strong> Perfecto para aplicaciones comerciales exigentes
                        </li>
                        <li style="padding: 10px 0; border-bottom: 1px solid #eee;">
                            <span style="color: #ff6600; font-size: 1.2em; margin-right: 10px;">▸</span>
                            <strong>Servicios:</strong> Solución confiable para el sector servicios
                        </li>
                        <li style="padding: 10px 0;">
                            <span style="color: #ff6600; font-size: 1.2em; margin-right: 10px;">▸</span>
                            <strong>Proyectos Especiales:</strong> Adaptable a requerimientos específicos
                        </li>
                    </ul>
                </div>
                
                <!-- Beneficios -->
                <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 25px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: #ff6600; margin-bottom: 20px; font-size: 1.8em; text-align: center;">
                        ¿Por qué elegir este producto?
                    </h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; text-align: center;">
                        <div>
                            <div style="font-size: 3em; margin-bottom: 10px;">💪</div>
                            <strong style="color: #ff6600;">Máximo Rendimiento</strong>
                        </div>
                        <div>
                            <div style="font-size: 3em; margin-bottom: 10px;">🛡️</div>
                            <strong style="color: #ff6600;">Garantía Extendida</strong>
                        </div>
                        <div>
                            <div style="font-size: 3em; margin-bottom: 10px;">💰</div>
                            <strong style="color: #ff6600;">Mejor Precio-Calidad</strong>
                        </div>
                        <div>
                            <div style="font-size: 3em; margin-bottom: 10px;">🚀</div>
                            <strong style="color: #ff6600;">Entrega Inmediata</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

        # Agregar sección de contacto
        html = self._add_contact_section(html, config)

        return html

    def _add_contact_section(self, html: str, config: Dict) -> str:
        """Agrega sección de contacto al HTML"""

        if not config:
            config = {
                "whatsapp": "541139563099",
                "email": "info@generadores.ar",
                "telefono_display": "+54 11 3956-3099",
                "website": "www.generadores.ar",
            }

        contact_section = f"""
        <!-- Sección de Contacto -->
        <div style="background: #333; color: white; padding: 30px; text-align: center; margin-top: 30px; border-radius: 15px;">
            <h2 style="margin-bottom: 20px; font-size: 2em;">¡Contáctanos Ahora!</h2>
            <p style="font-size: 1.2em; margin-bottom: 25px; opacity: 0.9;">
                Nuestro equipo de expertos está listo para asesorarte
            </p>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                <a href="https://wa.me/{config['whatsapp']}" 
                   style="background: #25D366; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-weight: bold; transition: transform 0.3s;">
                    <span style="font-size: 1.5em;">📱</span> WhatsApp
                </a>
                <a href="mailto:{config['email']}" 
                   style="background: #ff6600; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-weight: bold; transition: transform 0.3s;">
                    <span style="font-size: 1.5em;">✉️</span> Email
                </a>
                <a href="tel:{config['whatsapp']}" 
                   style="background: #0066cc; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-weight: bold; transition: transform 0.3s;">
                    <span style="font-size: 1.5em;">📞</span> {config['telefono_display']}
                </a>
            </div>
        </div>
        """

        # Insertar antes del cierre del div principal
        html = html.replace("</div>", contact_section + "</div>", 1)

        return html

    def generate_seo_metadata(self, product_info: Dict) -> Dict[str, str]:
        """Genera metadata SEO optimizada"""

        nombre = product_info.get("nombre", "Producto")
        marca = product_info.get("marca", "")
        modelo = product_info.get("modelo", "")
        familia = product_info.get("familia", "")

        # Título SEO
        title_parts = [nombre]
        if marca:
            title_parts.append(marca)
        if modelo:
            title_parts.append(modelo)
        title_parts.append("Mejor Precio")

        seo_title = " - ".join(title_parts)[:60]  # Límite de 60 caracteres

        # Descripción SEO
        seo_description = f"Compra {nombre} al mejor precio. "
        if marca:
            seo_description += f"Producto original {marca}. "
        seo_description += (
            "Envío inmediato, garantía oficial y soporte técnico especializado. "
        )
        seo_description += "¡Consulta ofertas especiales!"
        seo_description = seo_description[:160]  # Límite de 160 caracteres

        # Keywords
        keywords = []
        keywords.append(nombre.lower())
        if marca:
            keywords.append(marca.lower())
        if modelo:
            keywords.append(modelo.lower())
        if familia:
            keywords.append(familia.lower())
        keywords.extend(["comprar", "precio", "oferta", "venta"])

        return {
            "title": seo_title,
            "description": seo_description,
            "keywords": ", ".join(keywords),
        }
