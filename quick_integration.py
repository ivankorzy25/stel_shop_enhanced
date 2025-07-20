"""
Script de integración rápida para STEL Shop Manager Mejorado
Conecta con Cloud Function y genera descripciones mejoradas
"""

import json
import requests
import pandas as pd
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sys
import os

# Agregar el path para importar los módulos existentes
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el handler mejorado
try:
    from ai_handler_enhanced import EnhancedAIHandler
    print("✅ Módulo AI cargado correctamente")
except ImportError as e:
    print(f"⚠️  No se pudo cargar el módulo AI: {e}")
    print("   El sistema funcionará sin generación de IA")
    EnhancedAIHandler = None

# Agregar esta función auxiliar para logging en selenium_handler
def create_log_function(prefix=""):
    """Crea una función de log con prefijo opcional"""
    def log(message):
        print(f"{prefix}{message}")
    return log

# Importar el handler de Selenium
from navigation.selenium_handler import SeleniumHandler

app = Flask(__name__)
CORS(app)

# Instancia global
selenium_handler = SeleniumHandler()

# Configuración de Cloud Function
CLOUD_FUNCTION_URL = "https://southamerica-east1-lista-precios-2025.cloudfunctions.net/actualizar-precios-v2"

# Configuración de IA y contacto
AI_CONFIG = {
    "api_key": "AIzaSyBYjaWimtWtTk3m_4SjFgLQRWPkiu0suiw",  # Tu API key
    "whatsapp": "541139563099",
    "email": "info@stelshop.com",
    "telefono_display": "+54 11 3956-3099",
    "website": "www.stelshop.com"
}

# Handler de IA
ai_handler = None

# Cache de productos
products_cache = []
cache_timestamp = 0

# HTML embebido para el showcase con TODAS las funcionalidades
SHOWCASE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STEL Shop Manager - Generador de Descripciones</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #ff6600;
            --primary-dark: #e55500;
            --secondary: #333;
            --light: #f8f9fa;
            --white: #ffffff;
            --shadow: rgba(0, 0, 0, 0.1);
            --success: #28a745;
            --danger: #dc3545;
            --transition: all 0.3s ease;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--light);
            color: var(--secondary);
            line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: var(--white);
            padding: 1.5rem 0;
            box-shadow: 0 4px 6px var(--shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .logo {
            font-size: 1.8rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        .header-actions {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Filtros */
        .filters-section {
            background: var(--white);
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
        }

        .filters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
        }

        .filter-group label {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--secondary);
        }

        .filter-group input,
        .filter-group select {
            padding: 0.5rem;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1rem;
            transition: var(--transition);
        }

        .filter-group input:focus,
        .filter-group select:focus {
            outline: none;
            border-color: var(--primary);
        }

        /* Controles de selección */
        .selection-controls {
            background: #fff3e0;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .selection-info {
            font-weight: 600;
            color: var(--primary);
        }

        .selection-actions {
            display: flex;
            gap: 0.5rem;
        }

        /* Grid de productos */
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .product-card {
            background: var(--white);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px var(--shadow);
            transition: var(--transition);
            position: relative;
        }

        .product-card.selected {
            border: 3px solid var(--primary);
            transform: translateY(-2px);
        }

        .product-checkbox {
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 25px;
            height: 25px;
            cursor: pointer;
            z-index: 10;
        }

        .product-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: var(--white);
            padding: 1.5rem;
            padding-right: 4rem;
        }

        .product-name {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.3rem;
        }

        .product-brand {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .product-image {
            width: 100%;
            height: 200px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: #ccc;
        }

        .product-body {
            padding: 1rem;
        }

        .product-specs {
            margin-bottom: 1rem;
        }

        .spec-item {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
        }

        .product-price {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary);
            text-align: center;
            margin: 0.5rem 0;
        }

        .product-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }

        /* Botones */
        .btn {
            background: var(--primary);
            color: var(--white);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            text-align: center;
        }

        .btn:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: #6c757d;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .btn-success {
            background: var(--success);
            color: white;
        }

        .btn-success:hover {
            background: #218838;
        }

        .btn-danger {
            background: var(--danger);
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-large {
            padding: 0.75rem 2rem;
            font-size: 1.1rem;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            overflow-y: auto;
        }

        .modal-content {
            background: white;
            max-width: 900px;
            margin: 2rem auto;
            border-radius: 10px;
            position: relative;
            max-height: 90vh;
            overflow-y: auto;
        }

        .modal-header {
            background: var(--primary);
            color: white;
            padding: 1.5rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .close-modal {
            font-size: 2rem;
            cursor: pointer;
            background: none;
            border: none;
            color: white;
        }

        .close-modal:hover {
            opacity: 0.8;
        }

        .modal-body {
            padding: 2rem;
        }

        /* Loading */
        .loading {
            text-align: center;
            padding: 3rem;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Badge */
        .badge {
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        /* Panel de procesamiento */
        .processing-panel {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 3px solid var(--primary);
            padding: 1.5rem;
            box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.1);
            transform: translateY(100%);
            transition: transform 0.3s ease;
            z-index: 999;
        }

        .processing-panel.show {
            transform: translateY(0);
        }

        .processing-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
        }

        .processing-info {
            flex: 1;
        }

        .processing-actions {
            display: flex;
            gap: 1rem;
        }

        /* Preview imagen */
        .image-preview {
            width: 100%;
            height: 250px;
            background: #f5f5f5;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            overflow: hidden;
        }

        .image-preview img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        /* PDF buttons */
        .pdf-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .pdf-btn {
            flex: 1;
            padding: 0.5rem;
            border: 2px solid var(--primary);
            background: white;
            color: var(--primary);
            border-radius: 5px;
            text-decoration: none;
            text-align: center;
            font-weight: 600;
            transition: var(--transition);
        }

        .pdf-btn:hover {
            background: var(--primary);
            color: white;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">🏭 STEL Shop Manager - Generador de Descripciones</div>
            <div class="header-actions">
                <span class="badge" id="selected-count">0 seleccionados</span>
                <button class="btn btn-success btn-large" onclick="processSelected()" id="process-btn" disabled>
                    🚀 Procesar Seleccionados
                </button>
            </div>
        </div>
    </header>

    <main class="container">
        <!-- Filtros -->
        <section class="filters-section">
            <h3 style="margin-bottom: 1rem;">🔍 Filtros de Búsqueda</h3>
            <div class="filters-grid">
                <div class="filter-group">
                    <label for="search">Buscar</label>
                    <input type="text" id="search" placeholder="Nombre, marca, SKU...">
                </div>
                <div class="filter-group">
                    <label for="filter-familia">Familia</label>
                    <select id="filter-familia">
                        <option value="">Todas las familias</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-marca">Marca</label>
                    <select id="filter-marca">
                        <option value="">Todas las marcas</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-stock">Stock</label>
                    <select id="filter-stock">
                        <option value="">Todos</option>
                        <option value="con-stock">Con stock</option>
                        <option value="sin-stock">Sin stock</option>
                    </select>
                </div>
            </div>
            <div style="text-align: center; margin-top: 1rem;">
                <button class="btn" onclick="applyFilters()">Aplicar Filtros</button>
                <button class="btn btn-secondary" onclick="clearFilters()">Limpiar</button>
            </div>
        </section>

        <!-- Controles de selección -->
        <section class="selection-controls">
            <div class="selection-info">
                <span id="filtered-count">0</span> productos mostrados
            </div>
            <div class="selection-actions">
                <button class="btn btn-secondary" onclick="selectAll()">Seleccionar Todos</button>
                <button class="btn btn-secondary" onclick="selectNone()">Quitar Selección</button>
                <button class="btn btn-secondary" onclick="invertSelection()">Invertir Selección</button>
            </div>
        </section>

        <!-- Grid de productos -->
        <section id="products-container">
            <div class="loading">
                <div class="spinner"></div>
                <p style="margin-top: 1rem;">Cargando productos...</p>
            </div>
        </section>
    </main>

    <!-- Modal de detalle -->
    <div id="detail-modal" class="modal" onclick="closeModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2 id="modal-title">Detalle del Producto</h2>
                <button class="close-modal" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Generando vista previa...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Panel de procesamiento -->
    <div id="processing-panel" class="processing-panel">
        <div class="processing-content">
            <div class="processing-info">
                <h3>📦 Productos listos para procesar</h3>
                <p><span id="process-count">0</span> productos seleccionados para generar descripciones</p>
            </div>
            <div class="processing-actions">
                <button class="btn btn-secondary" onclick="hideProcessingPanel()">Cancelar</button>
                <button class="btn btn-success btn-large" onclick="startProcessing()">
                    ⚡ Iniciar Generación con IA
                </button>
            </div>
        </div>
    </div>

    <script>
        // Estado de la aplicación
        let allProducts = [];
        let filteredProducts = [];
        let selectedProducts = new Set();
        
        // Cargar productos
        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                const data = await response.json();
                
                if (data.success) {
                    allProducts = data.products;
                    // Asignar IDs únicos si no tienen
                    allProducts.forEach((product, index) => {
                        if (!product.id) {
                            product.id = product.sku || product.SKU || `product-${index}`;
                        }
                    });
                    
                    populateFilters();
                    applyFilters();
                } else {
                    showError('Error cargando productos: ' + (data.error || 'Error desconocido'));
                }
            } catch (error) {
                showError('Error de conexión: ' + error.message);
            }
        }

        // Popular filtros
        function populateFilters() {
            const familias = [...new Set(allProducts.map(p => p.familia).filter(Boolean))];
            const marcas = [...new Set(allProducts.map(p => p.marca).filter(Boolean))];
            
            const familiaSelect = document.getElementById('filter-familia');
            familiaSelect.innerHTML = '<option value="">Todas las familias</option>';
            familias.forEach(familia => {
                familiaSelect.innerHTML += `<option value="${familia}">${familia}</option>`;
            });
            
            const marcaSelect = document.getElementById('filter-marca');
            marcaSelect.innerHTML = '<option value="">Todas las marcas</option>';
            marcas.forEach(marca => {
                marcaSelect.innerHTML += `<option value="${marca}">${marca}</option>`;
            });
        }

        // Aplicar filtros
        function applyFilters() {
            const search = document.getElementById('search').value.toLowerCase();
            const familia = document.getElementById('filter-familia').value;
            const marca = document.getElementById('filter-marca').value;
            const stock = document.getElementById('filter-stock').value;
            
            filteredProducts = allProducts.filter(product => {
                const matchSearch = !search || 
                    (product.nombre && product.nombre.toLowerCase().includes(search)) ||
                    (product.marca && product.marca.toLowerCase().includes(search)) ||
                    (product.modelo && product.modelo.toLowerCase().includes(search)) ||
                    (product.sku && product.sku.toLowerCase().includes(search));
                
                const matchFamilia = !familia || product.familia === familia;
                const matchMarca = !marca || product.marca === marca;
                
                let matchStock = true;
                if (stock === 'con-stock') {
                    matchStock = product.stock > 0;
                } else if (stock === 'sin-stock') {
                    matchStock = product.stock === 0;
                }
                
                return matchSearch && matchFamilia && matchMarca && matchStock;
            });
            
            displayProducts();
            updateCounts();
        }

        // Limpiar filtros
        function clearFilters() {
            document.getElementById('search').value = '';
            document.getElementById('filter-familia').value = '';
            document.getElementById('filter-marca').value = '';
            document.getElementById('filter-stock').value = '';
            applyFilters();
        }

        // Mostrar productos
        function displayProducts() {
            const container = document.getElementById('products-container');
            
            if (filteredProducts.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 3rem;">No se encontraron productos con los filtros aplicados</p>';
                return;
            }
            
            container.innerHTML = `
                <div class="products-grid">
                    ${filteredProducts.map(product => {
                        const isSelected = selectedProducts.has(product.id);
                        const imageUrl = product.imagen_url || '';
                        const pdfUrl = product.pdf_url || '';
                        
                        return `
                        <div class="product-card ${isSelected ? 'selected' : ''}" id="card-${product.id}">
                            <input type="checkbox" 
                                   class="product-checkbox" 
                                   ${isSelected ? 'checked' : ''}
                                   onchange="toggleSelection('${product.id}')"
                                   onclick="event.stopPropagation()">
                            
                            <div class="product-header">
                                <div class="product-name">${product.nombre || 'Producto'}</div>
                                <div class="product-brand">${product.marca || ''} ${product.modelo || ''}</div>
                            </div>
                            
                            <div class="product-image" onclick="showPreview('${product.id}')">
                                ${imageUrl ? 
                                    `<img src="${imageUrl}" alt="${product.nombre}" onerror="this.style.display='none'">` : 
                                    '📷'
                                }
                            </div>
                            
                            <div class="product-body">
                                <div class="product-specs">
                                    ${product.sku ? `
                                        <div class="spec-item">
                                            <span>SKU:</span>
                                            <span>${product.sku}</span>
                                        </div>
                                    ` : ''}
                                    ${product.familia ? `
                                        <div class="spec-item">
                                            <span>Familia:</span>
                                            <span>${product.familia}</span>
                                        </div>
                                    ` : ''}
                                    ${product.potencia ? `
                                        <div class="spec-item">
                                            <span>Potencia:</span>
                                            <span>${product.potencia}</span>
                                        </div>
                                    ` : ''}
                                    <div class="spec-item">
                                        <span>Stock:</span>
                                        <span style="color: ${product.stock > 0 ? 'green' : 'red'}">
                                            ${product.stock || 0} unidades
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="product-price">
                                    ${product.precio ? `USD ${parseFloat(product.precio).toLocaleString()}` : 'Consultar'}
                                </div>
                                
                                <div class="product-actions">
                                    <button class="btn" onclick="showPreview('${product.id}')">
                                        👁️ Vista Previa
                                    </button>
                                    <button class="btn btn-secondary" onclick="showDetail('${product.id}')">
                                        📝 Ver Detalle
                                    </button>
                                </div>
                                
                                ${pdfUrl ? `
                                    <div class="pdf-actions">
                                        <a href="${pdfUrl}" target="_blank" class="pdf-btn">
                                            📄 Ver PDF Original
                                        </a>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            `;
            
            document.getElementById('filtered-count').textContent = filteredProducts.length;
        }

        // Toggle selección
        function toggleSelection(productId) {
            if (selectedProducts.has(productId)) {
                selectedProducts.delete(productId);
            } else {
                selectedProducts.add(productId);
            }
            
            const card = document.getElementById(`card-${productId}`);
            if (card) {
                card.classList.toggle('selected');
            }
            
            updateCounts();
        }

        // Seleccionar todos
        function selectAll() {
            filteredProducts.forEach(product => {
                selectedProducts.add(product.id);
            });
            displayProducts();
            updateCounts();
        }

        // Quitar selección
        function selectNone() {
            selectedProducts.clear();
            displayProducts();
            updateCounts();
        }

        // Invertir selección
        function invertSelection() {
            filteredProducts.forEach(product => {
                if (selectedProducts.has(product.id)) {
                    selectedProducts.delete(product.id);
                } else {
                    selectedProducts.add(product.id);
                }
            });
            displayProducts();
            updateCounts();
        }

        // Actualizar contadores
        function updateCounts() {
            const count = selectedProducts.size;
            document.getElementById('selected-count').textContent = `${count} seleccionados`;
            document.getElementById('process-count').textContent = count;
            
            const processBtn = document.getElementById('process-btn');
            processBtn.disabled = count === 0;
            
            const panel = document.getElementById('processing-panel');
            if (count > 0) {
                panel.classList.add('show');
            } else {
                panel.classList.remove('show');
            }
        }

        // Mostrar vista previa
        async function showPreview(productId) {
            const product = allProducts.find(p => p.id === productId);
            if (!product) return;
            
            document.getElementById('modal-title').textContent = 'Vista Previa - ' + product.nombre;
            document.getElementById('detail-modal').style.display = 'block';
            
            try {
                const response = await fetch(`/api/products/${product.sku || product.id}`);
                const data = await response.json();
                
                if (data.success && data.product.descripcion_html) {
                    document.getElementById('modal-body').innerHTML = `
                        <div class="image-preview">
                            ${product.imagen_url ? 
                                `<img src="${product.imagen_url}" alt="${product.nombre}">` : 
                                '<div style="font-size: 5rem; color: #ddd;">📷</div>'
                            }
                        </div>
                        ${data.product.descripcion_html}
                        <div class="pdf-actions" style="margin-top: 2rem;">
                            ${product.pdf_url ? `
                                <a href="${product.pdf_url}" target="_blank" class="pdf-btn">
                                    📄 Ver PDF Original
                                </a>
                            ` : ''}
                            <button class="pdf-btn" onclick="generatePDF('${productId}')">
                                📥 Descargar como PDF
                            </button>
                        </div>
                    `;
                } else {
                    showBasicPreview(product);
                }
            } catch (error) {
                showBasicPreview(product);
            }
        }

        // Vista previa básica
        function showBasicPreview(product) {
            document.getElementById('modal-body').innerHTML = `
                <div class="image-preview">
                    ${product.imagen_url ? 
                        `<img src="${product.imagen_url}" alt="${product.nombre}">` : 
                        '<div style="font-size: 5rem; color: #ddd;">📷</div>'
                    }
                </div>
                <h3>${product.nombre}</h3>
                <p>SKU: ${product.sku || 'N/A'}</p>
                <p>Marca: ${product.marca || 'N/A'}</p>
                <p>Precio: USD ${product.precio || 'Consultar'}</p>
                <p style="color: #666; margin-top: 1rem;">
                    La descripción detallada se generará durante el procesamiento.
                </p>
            `;
        }

        // Ver detalle completo
        async function showDetail(productId) {
            // Similar a showPreview pero con más información
            showPreview(productId);
        }

        // Cerrar modal
        function closeModal(event) {
            if (!event || event.target.classList.contains('modal')) {
                document.getElementById('detail-modal').style.display = 'none';
            }
        }

        // Procesar seleccionados
        function processSelected() {
            if (selectedProducts.size === 0) {
                alert('Por favor selecciona al menos un producto');
                return;
            }
            
            const selectedList = Array.from(selectedProducts).map(id => 
                allProducts.find(p => p.id === id)
            ).filter(Boolean);
            
            console.log('Productos seleccionados para procesar:', selectedList);
            
            // Aquí conectarías con el proceso de Selenium
            if (confirm(`¿Procesar ${selectedList.length} productos?\\n\\nEsto generará las descripciones y las subirá a Stelorder.`)) {
                startProcessing();
            }
        }

        // Panel de control de Selenium
        let seleniumInterval = null;

        async function startProcessing() {
            const selectedList = Array.from(selectedProducts).map(id => 
                allProducts.find(p => p.id === id)
            ).filter(Boolean);
            
            // Verificar estado de Selenium
            const statusResponse = await fetch('/api/selenium/status');
            const status = await statusResponse.json();
            
            if (!status.browser_active) {
                if (confirm('Chrome no está iniciado. ¿Deseas iniciarlo ahora?')) {
                    await startSelenium();
                    return;
                }
            }
            
            if (!status.logged_in) {
                alert('Por favor, inicia sesión en Stelorder primero');
                return;
            }
            
            // Enviar productos a procesar
            try {
                const response = await fetch('/api/process-products', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({products: selectedList})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showProcessingStatus();
                    startStatusMonitoring();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error iniciando procesamiento: ' + error.message);
            }
        }

        async function startSelenium() {
            try {
                const response = await fetch('/api/selenium/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({headless: false})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Chrome iniciado. Por favor, realiza el login manualmente en Stelorder.');
                } else {
                    alert('Error iniciando Chrome');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function showProcessingStatus() {
            // Crear modal de estado
            const statusModal = document.createElement('div');
            statusModal.id = 'processing-status-modal';
            statusModal.className = 'modal';
            statusModal.style.display = 'block';
            statusModal.innerHTML = `
                <div class="modal-content" style="max-width: 600px;">
                    <div class="modal-header">
                        <h2>⚡ Procesando Productos</h2>
                        <button class="close-modal" onclick="closeProcessingStatus()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div id="processing-info">
                            <div class="loading">
                                <div class="spinner"></div>
                                <p>Iniciando procesamiento...</p>
                            </div>
                        </div>
                        <div style="margin-top: 2rem; text-align: center;">
                            <button class="btn btn-secondary" onclick="pauseProcessing()">⏸️ Pausar</button>
                            <button class="btn btn-danger" onclick="stopProcessing()">🛑 Detener</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(statusModal);
        }

        function startStatusMonitoring() {
            // Actualizar estado cada 2 segundos
            seleniumInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/selenium/status');
                    const status = await response.json();
                    
                    updateProcessingDisplay(status);
                    
                    if (!status.processing) {
                        clearInterval(seleniumInterval);
                        setTimeout(() => {
                            alert('¡Procesamiento completado!');
                            closeProcessingStatus();
                        }, 1000);
                    }
                } catch (error) {
                    console.error('Error obteniendo estado:', error);
                }
            }, 2000);
        }

        function updateProcessingDisplay(status) {
            const infoDiv = document.getElementById('processing-info');
            if (!infoDiv) return;
            
            infoDiv.innerHTML = `
                <h3>📊 Estado del Procesamiento</h3>
                <div style="margin: 1rem 0;">
                    <div style="background: #f0f0f0; height: 30px; border-radius: 15px; overflow: hidden;">
                        <div style="background: var(--primary); height: 100%; width: ${status.progress || 0}%; transition: width 0.3s;"></div>
                    </div>
                    <p style="text-align: center; margin-top: 0.5rem;">${status.progress || 0}%</p>
                </div>
                <div class="spec-item">
                    <span>Producto actual:</span>
                    <span>${status.current_product || 'N/A'}</span>
                </div>
                <div class="spec-item">
                    <span>Procesados:</span>
                    <span style="color: green;">${status.processed || 0}</span>
                </div>
                <div class="spec-item">
                    <span>Errores:</span>
                    <span style="color: red;">${status.errors || 0}</span>
                </div>
                <div class="spec-item">
                    <span>Total:</span>
                    <span>${status.total || 0}</span>
                </div>
                ${status.paused ? '<p style="color: orange; text-align: center; margin-top: 1rem;">⏸️ PAUSADO</p>' : ''}
            `;
        }

        async function pauseProcessing() {
            await fetch('/api/selenium/pause', {method: 'POST'});
        }

        async function stopProcessing() {
            if (confirm('¿Estás seguro de detener el procesamiento?')) {
                await fetch('/api/selenium/stop', {method: 'POST'});
                clearInterval(seleniumInterval);
                closeProcessingStatus();
            }
        }

        function closeProcessingStatus() {
            const modal = document.getElementById('processing-status-modal');
            if (modal) {
                modal.remove();
            }
            clearInterval(seleniumInterval);
        }

        // Ocultar panel
        function hideProcessingPanel() {
            document.getElementById('processing-panel').classList.remove('show');
        }

        // Generar PDF (placeholder)
        function generatePDF(productId) {
            alert('Funcionalidad de generación de PDF próximamente');
        }

        // Mostrar error
        function showError(message) {
            const container = document.getElementById('products-container');
            container.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: red;">
                    <p>❌ ${message}</p>
                    <button class="btn" onclick="loadProducts()" style="margin-top: 1rem;">Reintentar</button>
                </div>
            `;
        }

        // Listeners para filtros en tiempo real
        document.getElementById('search').addEventListener('input', applyFilters);
        document.getElementById('filter-familia').addEventListener('change', applyFilters);
        document.getElementById('filter-marca').addEventListener('change', applyFilters);
        document.getElementById('filter-stock').addEventListener('change', applyFilters);

        // Cargar al iniciar
        window.onload = loadProducts;
    </script>
</body>
</html>
"""

def get_products_from_cloud_function():
    """Obtiene productos desde la Cloud Function"""
    global products_cache, cache_timestamp
    import time
    
    # Cache de 5 minutos
    if products_cache and (time.time() - cache_timestamp) < 300:
        return products_cache
    
    try:
        print("🔄 Obteniendo productos desde Cloud Function...")
        
        response = requests.get(
            CLOUD_FUNCTION_URL,
            timeout=30,
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # La Cloud Function puede devolver los datos en diferentes formatos
            if isinstance(data, dict) and 'products' in data:
                products = data['products']
            elif isinstance(data, list):
                products = data
            else:
                # Intentar encontrar la lista de productos
                products = data.get('data', [])
            
            print(f"✅ {len(products)} productos obtenidos")
            products_cache = products
            cache_timestamp = time.time()
            return products
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}...")
            return []
            
    except Exception as e:
        print(f"❌ Error conectando con Cloud Function: {e}")
        return []

@app.route('/')
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

@app.route('/api/products')
def get_products():
    """Obtiene todos los productos de la Cloud Function"""
    try:
        # Obtener productos desde Cloud Function
        products = get_products_from_cloud_function()
        
        # Formatear productos al formato esperado
        formatted_products = []
        for product in products:
            # Adaptarse a diferentes nombres de campos posibles
            formatted_products.append({
                "sku": product.get('SKU') or product.get('sku') or '',
                "nombre": product.get('Descripción') or product.get('descripcion') or product.get('nombre') or '',
                "marca": product.get('Marca') or product.get('marca') or '',
                "modelo": product.get('Modelo') or product.get('modelo') or '',
                "familia": product.get('Familia') or product.get('familia') or '',
                "precio": product.get('Precio_USD_con_IVA') or product.get('precio') or 0,
                "stock": product.get('Stock') or product.get('stock') or 0,
                "pdf_url": product.get('URL_PDF') or product.get('pdf_url') or '',
                "potencia": product.get('Potencia') or product.get('potencia') or '',
                "voltaje": product.get('Tensión') or product.get('voltaje') or '',
                "motor": product.get('Motor') or product.get('motor') or '',
                "combustible": product.get('Combustible') or product.get('combustible') or '',
                "frecuencia": product.get('Frecuencia') or product.get('frecuencia') or '',
                "consumo": product.get('Consumo_L_h') or product.get('consumo') or ''
            })
        
        return jsonify({
            "success": True,
            "count": len(formatted_products),
            "products": formatted_products
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/products/<sku>')
def get_product_detail(sku):
    """Obtiene detalle de un producto específico con descripción generada"""
    try:
        # Buscar producto en cache
        products = get_products_from_cloud_function()
        
        # Buscar por SKU (considerando diferentes formatos)
        product = None
        for p in products:
            if (p.get('SKU') == sku or p.get('sku') == sku):
                product = p
                break
        
        if not product:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Formatear producto
        formatted_product = {
            "sku": product.get('SKU') or product.get('sku'),
            "nombre": product.get('Descripción') or product.get('descripcion'),
            "marca": product.get('Marca') or product.get('marca'),
            "modelo": product.get('Modelo') or product.get('modelo'),
            "familia": product.get('Familia') or product.get('familia'),
            "precio": product.get('Precio_USD_con_IVA') or product.get('precio'),
            "stock": product.get('Stock') or product.get('stock'),
            "pdf_url": product.get('URL_PDF') or product.get('pdf_url'),
            "raw_data": product
        }
        
        # Generar descripción mejorada si tenemos IA
        if ai_handler:
            try:
                formatted_product['descripcion_html'] = ai_handler.generate_enhanced_description(
                    product, AI_CONFIG
                )
                formatted_product['seo'] = ai_handler.generate_seo_metadata(product)
            except Exception as e:
                print(f"Error generando descripción: {e}")
                formatted_product['descripcion_html'] = None
        
        return jsonify({
            "success": True,
            "product": formatted_product
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/showcase')
def showcase():
    """Página de visualización de productos"""
    return SHOWCASE_HTML

@app.route('/api/generate-description', methods=['POST'])
def generate_description():
    """Genera descripción HTML para un producto"""
    try:
        data = request.json
        
        if not data or 'sku' not in data:
            return jsonify({"error": "SKU requerido"}), 400
        
        # Buscar producto
        products = get_products_from_cloud_function()
        product = None
        
        for p in products:
            if (p.get('SKU') == data['sku'] or p.get('sku') == data['sku']):
                product = p
                break
        
        if not product:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Generar descripción
        if not ai_handler:
            return jsonify({"error": "IA no configurada"}), 500
        
        description_html = ai_handler.generate_enhanced_description(
            product, AI_CONFIG
        )
        
        seo_metadata = ai_handler.generate_seo_metadata(product)
        
        return jsonify({
            "success": True,
            "sku": data['sku'],
            "description_html": description_html,
            "seo": seo_metadata
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/selenium/start', methods=['POST'])
def start_selenium():
    """Inicia el navegador Chrome"""
    try:
        data = request.json or {}
        headless = data.get('headless', False)
        
        success = selenium_handler.start_browser(headless)
        
        return jsonify({
            "success": success,
            "status": selenium_handler.get_status()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/selenium/login', methods=['POST'])
def selenium_login():
    """Realiza login en Stelorder"""
    try:
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        
        success = selenium_handler.login_to_stelorder(username, password)
        
        return jsonify({
            "success": success,
            "status": selenium_handler.get_status()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/selenium/status')
def selenium_status():
    """Obtiene el estado de Selenium"""
    return jsonify(selenium_handler.get_status())

@app.route('/api/process-products', methods=['POST'])
def process_products_selenium():
    """Procesa productos con Selenium"""
    try:
        data = request.json
        products = data.get('products', [])
        
        if not products:
            return jsonify({"error": "No hay productos para procesar"}), 400
        
        if not selenium_handler.is_logged_in:
            return jsonify({"error": "Debes iniciar sesión en Stelorder primero"}), 400
        
        # Función callback para generar descripciones
        def generate_description_for_product(product):
            try:
                # Crear función de log para el handler
                log_func = create_log_function("      ")
                
                if ai_handler:
                    # Generar con IA
                    description_html = ai_handler.generate_enhanced_description(
                        product, AI_CONFIG
                    )
                    seo = ai_handler.generate_seo_metadata(product)
                    
                    # Generar descripción simple (primera parte del nombre + características)
                    descripcion_simple = f"{product.get('nombre', 'Producto')}\n"
                    if product.get('potencia'):
                        descripcion_simple += f"Potencia: {product['potencia']}\n"
                    if product.get('motor'):
                        descripcion_simple += f"Motor: {product['motor']}\n"
                    
                    return {
                        "descripcion": descripcion_simple,
                        "descripcion_detallada": description_html,
                        "seo": seo
                    }
                else:
                    # Sin IA, usar descripción básica
                    return {
                        "descripcion": product.get('nombre', 'Producto'),
                        "descripcion_detallada": f"<p>{product.get('nombre', 'Producto')}</p>",
                        "seo": {
                            "title": product.get('nombre', 'Producto'),
                            "description": product.get('nombre', 'Producto')[:160]
                        }
                    }
            except Exception as e:
                print(f"Error generando descripción: {e}")
                return None
        
        # Iniciar procesamiento
        selenium_handler.process_products(products, generate_description_for_product)
        
        return jsonify({
            "success": True,
            "message": f"Procesando {len(products)} productos",
            "status": selenium_handler.get_status()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/selenium/pause', methods=['POST'])
def pause_selenium():
    """Pausa el procesamiento"""
    selenium_handler.pause()
    return jsonify({"success": True, "status": selenium_handler.get_status()})

@app.route('/api/selenium/resume', methods=['POST'])
def resume_selenium():
    """Reanuda el procesamiento"""
    selenium_handler.resume()
    return jsonify({"success": True, "status": selenium_handler.get_status()})

@app.route('/api/selenium/stop', methods=['POST'])
def stop_selenium():
    """Detiene el procesamiento"""
    selenium_handler.stop()
    return jsonify({"success": True, "status": selenium_handler.get_status()})

@app.route('/api/selenium/close', methods=['POST'])
def close_selenium():
    """Cierra el navegador"""
    selenium_handler.close_browser()
    return jsonify({"success": True, "status": selenium_handler.get_status()})

def initialize_app():
    """Inicializa la aplicación con la configuración"""
    global ai_handler
    
    print("🚀 Inicializando STEL Shop Manager Mejorado...")
    
    # Inicializar IA
    try:
        ai_handler = EnhancedAIHandler(AI_CONFIG['api_key'])
        print("✅ IA inicializada correctamente")
    except Exception as e:
        print(f"⚠️ Error inicializando IA: {e}")
        print("   El sistema funcionará sin generación de IA")
    
    # Verificar conexión a Cloud Function
    print("🔍 Verificando conexión a Cloud Function...")
    products = get_products_from_cloud_function()
    if products:
        print(f"✅ Cloud Function conectada - {len(products)} productos disponibles")
    else:
        print("⚠️ No se pudieron obtener productos de Cloud Function")

if __name__ == '__main__':
    # Inicializar aplicación
    initialize_app()
    
    # Iniciar servidor
    print("\n🌐 Servidor iniciando en http://localhost:5000")
    print("📄 Documentación de API en http://localhost:5000")
    print("🎨 Showcase de productos en http://localhost:5000/showcase")
    
    app.run(debug=False, port=5000, host='0.0.0.0')
