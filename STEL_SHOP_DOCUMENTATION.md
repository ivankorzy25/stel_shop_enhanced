# STEL Shop Manager - Documentación Completa

## 📋 Descripción General

STEL Shop Manager es un sistema automatizado para generar y actualizar descripciones de productos en Stelorder utilizando Inteligencia Artificial (Google Gemini) y automatización web con Selenium.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Frontend (HTML/JavaScript)**
   - Interfaz web para visualizar y seleccionar productos
   - Sistema de filtros y búsqueda
   - Panel de control para procesamiento con Selenium

2. **Backend (Flask/Python)**
   - API REST para gestión de productos
   - Integración con Cloud Function para obtener datos
   - Manejo de sesiones de Selenium

3. **Módulo de IA (Google Gemini)**
   - Generación automática de descripciones HTML
   - Creación de títulos y descripciones SEO
   - Procesamiento de PDFs técnicos

4. **Módulo de Selenium**
   - Automatización de navegación en Stelorder
   - Actualización masiva de productos
   - Sistema de pausar/reanudar procesamiento

## 🚀 Flujo de Trabajo

### 1. Inicio del Sistema
```bash
python start_all.py
```
- Inicia servidor Flask en puerto 5000
- Abre automáticamente el navegador
- Carga productos desde Cloud Function

### 2. Selección de Productos
- Usuario navega al catálogo en http://localhost:5000/showcase
- Aplica filtros según necesidad (familia, marca, stock, etc.)
- Selecciona productos a procesar con checkboxes

### 3. Proceso de Login en Stelorder
1. Usuario hace clic en "Procesar Seleccionados"
2. Sistema verifica si Chrome está abierto
3. Si no está abierto, lo inicia y navega a www.stelorder.com/app
4. **IMPORTANTE**: Usuario debe hacer login MANUALMENTE
5. Una vez logueado, presiona "Confirmar que ya estoy logueado"
6. Sistema verifica la sesión y habilita el procesamiento

### 4. Generación de Descripciones con IA
Para cada producto seleccionado:
- Extrae información del PDF técnico (si está disponible)
- Genera con Gemini AI:
  - Descripción técnica (texto plano)
  - Descripción HTML completa (diseño premium)
  - Título SEO (máx 60 caracteres)
  - Descripción SEO (máx 160 caracteres)

### 5. Actualización en Stelorder
El sistema navega automáticamente:
1. Va al catálogo
2. Busca el producto por SKU
3. Abre la pestaña Shop
4. Hace clic en Editar
5. Actualiza todos los campos:
   - Descripción simple
   - Descripción detallada (HTML)
   - SEO Título
   - SEO Descripción
6. Guarda los cambios

## 📁 Estructura de Archivos

```
stel_shop_enhanced/
├── ai_handler_enhanced.py       # Módulo de IA y procesamiento de PDFs
├── navigation/
│   └── selenium_handler.py      # Automatización con Selenium
├── quick_integration.py         # Servidor Flask y API
├── enhanced_shop/
│   └── config.json             # Configuración (contacto, API keys)
├── start_all.py                # Script de inicio
└── STEL_SHOP_DOCUMENTATION.md  # Este archivo
```

## ⚙️ Configuración

### config.json
```json
{
  "ai": {
    "api_key": "TU_API_KEY_GEMINI"
  },
  "contact": {
    "whatsapp": "541139563099",
    "email": "info@generadores.ar",
    "phone_display": "+54 11 3956-3099",
    "website": "www.generadores.ar"
  }
}
```

### API Key de Gemini
Obtener en: https://makersuite.google.com/app/apikey

## 🔍 Selectores de Selenium para Stelorder

### Navegación Principal
- Catálogo: `//a[@id='ui-id-2']`
- Buscador: `//input[contains(@class, 'buscadorListado')]`
- Primer resultado: `//td[@class='tdTextoLargo tdBold']`

### Edición de Producto
- Pestaña Shop: `//a[@id='ui-id-31']`
- Botón Editar: `//*[@id='editarShop']`
- Modal: `editarObjetoCatalogoConfiguracionShop_dialog`

### Campos del Modal
- Descripción: `descriptionShop`
- Descripción HTML: iframe con clase `cke_wysiwyg_frame`
- SEO Título: `tituloSeoShop`
- SEO Descripción: `descripcionSeoShop`
- Botón Guardar: `button.opcionMenuGuardar.primaryButton`

## 🛠️ Solución de Problemas

### Chrome no se abre
- Verificar que Chrome esté instalado
- Cerrar otras instancias de Chrome con el mismo perfil

### No detecta login
- Asegurarse de estar en la página principal después del login
- Verificar que aparezca el menú del catálogo

### Error de IA
- Verificar API key de Gemini
- Verificar conexión a internet
- El PDF del producto debe ser accesible

### Producto no se actualiza
- Verificar que el SKU sea exacto
- El producto debe existir en Stelorder
- Verificar permisos del usuario

## 📊 Estados del Sistema

### Estado de Selenium (`/api/selenium/status`)
```json
{
    "browser_active": true/false,
    "logged_in": true/false,
    "processing": true/false,
    "current_product": "nombre del producto",
    "progress": 75,
    "processed": 15,
    "errors": 2,
    "total": 20
}
```

## 🔄 Actualizaciones Recientes

### Versión 2.0 (Julio 2025)
- Implementado flujo de login manual obligatorio
- Mejorada la generación de HTML con IA
- Agregado procesamiento de PDFs técnicos
- Sistema de pausar/reanudar procesamiento
- Interfaz mejorada con selección múltiple

### Cambios Críticos
1. **Login Manual**: El sistema ya NO intenta hacer login automático
2. **IA Obligatoria**: No hay fallback, la IA debe estar configurada
3. **Datos desde Cloud Function**: No se usa Excel, todo viene de la nube
4. **HTML Premium**: Las descripciones siguen el diseño de la v5.1

## 📞 Soporte

Para consultas sobre el sistema:
- WhatsApp: +54 11 3956-3099
- Email: info@generadores.ar
- Web: www.generadores.ar

---

**Nota**: Este documento debe actualizarse con cada cambio significativo en el sistema.
