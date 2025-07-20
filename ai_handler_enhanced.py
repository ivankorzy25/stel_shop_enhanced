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
            if not pdf_url.startswith('http'):
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
                "page_count": len(pdf_reader.pages)
            }
            
        except Exception as e:
            print(f"⚠️ Error extrayendo PDF: {e}")
            return {
                "success": False,
                "text": "",
                "specifications": {}
            }

    def _extract_specifications(self, text: str) -> Dict[str, str]:
        """Extrae especificaciones técnicas del texto"""
        specs = {}
        
        # Patrones comunes en fichas técnicas
        patterns = {
            'potencia': r'(?:potencia|power).*?(\d+\.?\d*)\s*(?:kva|kw)',
            'voltaje': r'(?:voltaje|voltage|tensión).*?(\d+)\s*v',
            'frecuencia': r'(?:frecuencia|frequency).*?(\d+)\s*hz',
            'motor': r'(?:motor|engine).*?([A-Za-z0-9\s\-]+)',
            'consumo': r'(?:consumo|consumption).*?(\d+\.?\d*)\s*(?:l/h|lph)',
            'dimensiones': r'(?:dimensiones|dimensions).*?(\d+)\s*x\s*(\d+)\s*x\s*(\d+)',
            'peso': r'(?:peso|weight).*?(\d+\.?\d*)\s*(?:kg|kilos)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specs[key] = match.group(1) if key != 'dimensiones' else f"{match.group(1)}x{match.group(2)}x{match.group(3)}"
        
        return specs

    def generate_enhanced_description(self, product_info: Dict, config: Dict = None) -> str:
        """Genera una descripción HTML mejorada y vistosa"""
        
        # Extraer contenido del PDF si está disponible
        pdf_content = {"success": False, "text": "", "specifications": {}}
        if product_info.get('pdf_url'):
            pdf_content = self.extract_pdf_content(product_info['pdf_url'])
        
        # Combinar especificaciones del PDF con las existentes
        combined_specs = {**product_info, **pdf_content.get('specifications', {})}
        
        # Generar descripción con IA si está disponible
        if self.model:
            description_html = self._generate_with_ai(combined_specs, pdf_content, config)
        else:
            description_html = self._generate_fallback_enhanced(combined_specs, config)
        
        return description_html

    def _generate_with_ai(self, product_info: Dict, pdf_content: Dict, config: Dict) -> str:
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
            html = re.sub(r'^```html\s*', '', html)
            html = re.sub(r'\s*```$', '', html)
            
            # Agregar información de contacto
            html = self._add_contact_section(html, config)
            
            return html
            
        except Exception as e:
            print(f"⚠️ Error generando con IA: {e}")
            return self._generate_fallback_enhanced(product_info, config)

    def _generate_fallback_enhanced(self, product_info: Dict, config: Dict) -> str:
        """Genera una descripción HTML atractiva sin IA"""
        
        nombre = product_info.get('nombre', 'Producto')
        marca = product_info.get('marca', '')
        modelo = product_info.get('modelo', '')
        precio = product_info.get('precio', 0)
        
        # Especificaciones disponibles
        specs_html = ""
        spec_fields = {
            'potencia': 'Potencia',
            'voltaje': 'Voltaje',
            'frecuencia': 'Frecuencia',
            'motor': 'Motor',
            'consumo': 'Consumo',
            'peso': 'Peso',
            'dimensiones': 'Dimensiones'
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
                "website": "www.generadores.ar"
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
        html = html.replace('</div>', contact_section + '</div>', 1)
        
        return html

    def generate_seo_metadata(self, product_info: Dict) -> Dict[str, str]:
        """Genera metadata SEO optimizada"""
        
        nombre = product_info.get('nombre', 'Producto')
        marca = product_info.get('marca', '')
        modelo = product_info.get('modelo', '')
        familia = product_info.get('familia', '')
        
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
        seo_description += "Envío inmediato, garantía oficial y soporte técnico especializado. "
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
        keywords.extend(['comprar', 'precio', 'oferta', 'venta'])
        
        return {
            "title": seo_title,
            "description": seo_description,
            "keywords": ", ".join(keywords)
        }