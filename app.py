import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime
import time
import requests
from io import BytesIO

# Importar módulos personalizados
from utils.expert_system import SafetyExpertSystem
from utils.config import CLASS_NAMES, ALERT_LEVELS

# Configurar la página
st.set_page_config(
    page_title="SafeBuild - Monitoreo de Seguridad",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .alert-high {
        background-color: #FEE2E2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #DC2626;
        margin: 1rem 0;
    }
    .alert-medium {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #D97706;
        margin: 1rem 0;
    }
    .alert-ok {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #059669;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
        margin: 0.5rem 0;
    }
    .demo-image {
        border-radius: 10px;
        border: 2px solid #E2E8F0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🦺 SafeBuild</h1>', unsafe_allow_html=True)
st.markdown("### Sistema Inteligente de Monitoreo de Seguridad en Obras")
st.markdown("---")

# Inicializar sistema experto
expert_system = SafetyExpertSystem()

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Configuración de parámetros
min_confidence = st.sidebar.slider(
    "Confianza Mínima", 
    0.1, 0.9, 0.6, 0.05
)

alert_system = st.sidebar.checkbox("Sistema de Alertas Activo", True)
auto_save = st.sidebar.checkbox("Guardar Reportes", True)

# Selección de modo
st.sidebar.header("🎯 Modo de Operación")
mode = st.sidebar.radio(
    "Selecciona el modo:",
    ["📊 Demo con Imágenes", "📸 Subir Imagen"],
    index=0
)

# URLs de imágenes de demo para Streamlit Cloud
DEMO_IMAGES = {
    "escenario_seguro": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=600",
    "escenario_alerta": "https://images.unsplash.com/photo-1581091226033-d5c48150dbaa?w=600", 
    "escenario_critico": "https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?w=600"
}

def load_demo_image(url):
    """Cargar imagen de demo desde URL"""
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        return np.array(image)
    except:
        # Fallback: crear imagen simple
        return np.ones((400, 600, 3), dtype=np.uint8) * 100

def simulate_detections(scenario):
    """Simular detecciones basadas en el escenario seleccionado"""
    if scenario == "escenario_seguro":
        return [
            {'class_name': 'person', 'confidence': 0.95, 'bbox': [100, 100, 200, 300]},
            {'class_name': 'helmet', 'confidence': 0.92, 'bbox': [110, 90, 130, 120]},
            {'class_name': 'safety_vest', 'confidence': 0.89, 'bbox': [100, 100, 200, 150]},
            {'class_name': 'person', 'confidence': 0.88, 'bbox': [300, 150, 400, 350]},
            {'class_name': 'helmet', 'confidence': 0.91, 'bbox': [310, 140, 330, 170]},
            {'class_name': 'safety_vest', 'confidence': 0.87, 'bbox': [300, 150, 400, 200]}
        ]
    elif scenario == "escenario_alerta":
        return [
            {'class_name': 'person', 'confidence': 0.95, 'bbox': [100, 100, 200, 300]},
            {'class_name': 'helmet', 'confidence': 0.92, 'bbox': [110, 90, 130, 120]},
            # Falta chaleco para una persona
            {'class_name': 'person', 'confidence': 0.88, 'bbox': [300, 150, 400, 350]},
            {'class_name': 'safety_vest', 'confidence': 0.87, 'bbox': [300, 150, 400, 200]}
            # Falta casco para la segunda persona
        ]
    else:  # escenario_critico
        return [
            {'class_name': 'person', 'confidence': 0.95, 'bbox': [100, 100, 200, 300]},
            {'class_name': 'person', 'confidence': 0.88, 'bbox': [300, 150, 400, 350]},
            # Faltan ambos EPPs para todas las personas
        ]

def draw_simple_detections(image, detections, analysis):
    """Dibujar detecciones simples en la imagen"""
    img_copy = image.copy()
    
    # Colores para las clases
    colors = {
        'person': (0, 255, 0),      # Verde
        'helmet': (255, 0, 0),      # Azul
        'safety_vest': (0, 0, 255)  # Rojo
    }
    
    for detection in detections:
        class_name = detection['class_name']
        x1, y1, x2, y2 = map(int, detection['bbox'])
        color = colors.get(class_name, (255, 255, 255))
        
        # Dibujar rectángulo
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        
        # Etiqueta
        label = f"{class_name}"
        cv2.putText(img_copy, label, (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return img_copy

# Sección principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("👁️ Monitoreo de Seguridad")
    
    if mode == "📊 Demo con Imágenes":
        st.info("🎯 Selecciona un escenario para analizar la seguridad en obra")
        
        # Selector de escenario
        scenario = st.radio(
            "Escenario de Obra:",
            ["✅ Condiciones Seguras", "⚠️ Alertas de Seguridad", "🚨 Condiciones Críticas"],
            horizontal=True
        )
        
        # Mapear selección a URLs de demo
        scenario_map = {
            "✅ Condiciones Seguras": "escenario_seguro",
            "⚠️ Alertas de Seguridad": "escenario_alerta", 
            "🚨 Condiciones Críticas": "escenario_critico"
        }
        
        selected_scenario = scenario_map[scenario]
        
        # Cargar y mostrar imagen
        with st.spinner("🖼️ Cargando escenario de obra..."):
            demo_image = load_demo_image(DEMO_IMAGES[selected_scenario])
            time.sleep(1)  # Simular carga
            
        # Simular análisis
        with st.spinner("🔍 Analizando condiciones de seguridad..."):
            detections = simulate_detections(selected_scenario)
            analysis = expert_system.analyze_detections(detections)
            time.sleep(1)
        
        # Mostrar imagen con detecciones
        result_image = draw_simple_detections(demo_image, detections, analysis)
        st.image(result_image, caption=f"Escenario: {scenario}", use_column_width=True)
        
        # Mostrar resultados del análisis
        alert_level = analysis['alert_level']
        if alert_level == "ALTA":
            st.markdown(f"""
            <div class="alert-high">
                <h3>🚨 ALERTA CRÍTICA DE SEGURIDAD</h3>
                <p><strong>{analysis['alert_message']}</strong></p>
                <p>📋 <strong>Acción Recomendada:</strong> {analysis['recommended_action']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif alert_level == "MEDIA":
            st.markdown(f"""
            <div class="alert-medium">
                <h3>⚠️ ALERTA DE SEGURIDAD</h3>
                <p><strong>{analysis['alert_message']}</strong></p>
                <p>📋 <strong>Acción Recomendada:</strong> {analysis['recommended_action']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-ok">
                <h3>✅ CONDICIONES SEGURAS</h3>
                <p><strong>{analysis['alert_message']}</strong></p>
                <p>📋 <strong>Acción Recomendada:</strong> {analysis['recommended_action']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    else:  # Modo subir imagen
        uploaded_file = st.file_uploader(
            "📤 Sube una imagen de la obra", 
            type=['jpg', 'jpeg', 'png'],
            help="La imagen será analizada para detectar condiciones de seguridad"
        )
        
        if uploaded_file is not None:
            # Procesar imagen subida
            image = Image.open(uploaded_file)
            image_np = np.array(image)
            
            # Para demo, usar detecciones simuladas
            with st.spinner("🔍 Analizando seguridad en la imagen..."):
                # Simular diferentes escenarios basados en nombre del archivo
                if "safe" in uploaded_file.name.lower():
                    detections = simulate_detections("escenario_seguro")
                elif "alert" in uploaded_file.name.lower():
                    detections = simulate_detections("escenario_alerta")
                else:
                    detections = simulate_detections("escenario_critico")
                
                analysis = expert_system.analyze_detections(detections)
                result_image = draw_simple_detections(image_np, detections, analysis)
            
            st.image(result_image, caption="Análisis de Seguridad", use_column_width=True)
            
            # Mostrar resultados
            alert_level = analysis['alert_level']
            if alert_level == "ALTA":
                st.error(f"🚨 {analysis['alert_message']}")
            elif alert_level == "MEDIA":
                st.warning(f"⚠️ {analysis['alert_message']}")
            else:
                st.success(f"✅ {analysis['alert_message']}")

with col2:
    st.subheader("📊 Panel de Control")
    
    # Mostrar estadísticas actuales
    if 'analysis' in locals():
        stats = analysis.get('statistics', {})
        persons = stats.get('persons', 0)
        helmets = stats.get('helmets', 0)
        vests = stats.get('vests', 0)
        
        compliance = 0
        if persons > 0:
            compliance = min(helmets, vests) / persons * 100
    else:
        persons = helmets = vests = compliance = 0
    
    # Métricas
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    col11, col12 = st.columns(2)
    with col11:
        st.metric("👥 Trabajadores", persons)
        st.metric("🪖 Cascos", helmets)
    with col12:
        st.metric("🦺 Chalecos", vests)
        st.metric("📈 Cumplimiento", f"{compliance:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Alertas activas
    st.subheader("🚨 Estado Actual")
    if persons > 0:
        if helmets < persons:
            st.error(f"❌ {persons - helmets} sin casco")
        if vests < persons:
            st.warning(f"⚠️ {persons - vests} sin chaleco")
        if helmets >= persons and vests >= persons:
            st.success("✅ EPP completo")
    else:
        st.info("👀 No hay trabajadores")
    
    # Historial de simulaciones
    st.subheader("📋 Actividad Reciente")
    activity_data = {
        'Hora': [datetime.now().strftime("%H:%M"), '10:30', '09:15'],
        'Evento': ['Análisis Actual', 'Inspección Zona B', 'Reunión Seguridad'],
        'Resultado': [analysis['alert_level'], 'MEDIA', 'OK']
    }
    df = pd.DataFrame(activity_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Sección de analytics
st.markdown("---")
st.subheader("📈 Estadísticas del Sistema")

col3, col4, col5, col6 = st.columns(4)

with col3:
    st.metric("Inspecciones Hoy", "47", "12%")
with col4:
    st.metric("Alertas Totales", "8", "-3%")
with col5:
    st.metric("Tasa Cumplimiento", "83%", "5%")
with col6:
    st.metric("Tiempo Respuesta", "2.1 min", "0.3 min")

# Información del sistema
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Información del Sistema")
st.sidebar.info("""
**SafeBuild v1.0**  
Sistema de monitoreo inteligente  
para obras de construcción

🚧 **Integra:**  
• Visión por computadora  
• Sistema experto de reglas  
• Alertas automáticas
""")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p><strong>SafeBuild v1.0</strong> - Sistema de Monitoreo Inteligente | 🚧 TP Integrador IA 🚧</p>
</div>
""", unsafe_allow_html=True)
