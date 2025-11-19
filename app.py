import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime
import time
import requests
from io import BytesIO
import os

# Importar módulos personalizados
from utils.expert_system import SafetyExpertSystem
from utils.config import CLASS_NAMES, ALERT_LEVELS

# =============================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================
st.set_page_config(
    page_title="SafeBuild - Monitoreo de Seguridad",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# CSS PERSONALIZADO
# =============================================
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
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 6px solid #DC2626;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-medium {
        background-color: #FEF3C7;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 6px solid #D97706;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-ok {
        background-color: #D1FAE5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 6px solid #059669;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #E2E8F0;
        margin: 0.5rem 0;
    }
    .sidebar-section {
        background-color: #F1F5F9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton button {
        width: 100%;
        background-color: #1E40AF;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# INICIALIZACIÓN DEL SISTEMA
# =============================================
@st.cache_resource
def init_expert_system():
    """Inicializar el sistema experto (cached para mejor performance)"""
    return SafetyExpertSystem()

expert_system = init_expert_system()

# =============================================
# DATOS DE DEMO - IMÁGENES DESDE UNSPLASH
# =============================================
DEMO_IMAGES = {
    "escenario_seguro": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=600&fit=crop",
    "escenario_alerta": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&fit=crop", 
    "escenario_critico": "https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?w=600&fit=crop"
}

# =============================================
# FUNCIONES AUXILIARES
# =============================================
def load_demo_image(url):
    """
    Cargar imagen de demo desde URL externa
    Returns: numpy array de la imagen
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return np.array(image)
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar la imagen demo: {e}")
        # Crear imagen de fallback
        return create_fallback_image()

def create_fallback_image():
    """Crear imagen simple cuando falla la carga"""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 150
    cv2.putText(img, "SafeBuild Demo", (150, 200), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(img, "Sistema de Monitoreo de Seguridad", (100, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return img

def simulate_detections(scenario_type):
    """
    Simular detecciones de YOLO basadas en el escenario
    Returns: lista de detecciones simuladas
    """
    if scenario_type == "escenario_seguro":
        return [
            {'class_name': 'person', 'confidence': 0.95, 'bbox': [100, 100, 200, 300]},
            {'class_name': 'helmet', 'confidence': 0.92, 'bbox': [110, 90, 130, 120]},
            {'class_name': 'safety_vest', 'confidence': 0.89, 'bbox': [100, 100, 200, 150]},
            {'class_name': 'person', 'confidence': 0.88, 'bbox': [300, 150, 400, 350]},
            {'class_name': 'helmet', 'confidence': 0.91, 'bbox': [310, 140, 330, 170]},
            {'class_name': 'safety_vest', 'confidence': 0.87, 'bbox': [300, 150, 400, 200]}
        ]
    elif scenario_type == "escenario_alerta":
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

def draw_detections_on_image(image, detections, analysis):
    """
    Dibujar bounding boxes y información en la imagen
    Returns: imagen con anotaciones
    """
    img_copy = image.copy()
    
    # Colores para cada clase
    colors = {
        'person': (0, 255, 0),      # Verde - Trabajadores
        'helmet': (255, 0, 0),      # Azul - Cascos
        'safety_vest': (0, 0, 255)  # Rojo - Chalecos
    }
    
    # Dibujar cada detección
    for detection in detections:
        class_name = detection['class_name']
        confidence = detection['confidence']
        x1, y1, x2, y2 = map(int, detection['bbox'])
        color = colors.get(class_name, (255, 255, 255))
        
        # Dibujar bounding box
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 3)
        
        # Etiqueta con clase y confianza
        label = f"{class_name} ({confidence:.2f})"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # Fondo para la etiqueta
        cv2.rectangle(img_copy, (x1, y1 - label_size[1] - 10), 
                     (x1 + label_size[0], y1), color, -1)
        # Texto de la etiqueta
        cv2.putText(img_copy, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Añadir panel de información del análisis
    alert_level = analysis['alert_level']
    alert_color = {
        'ALTA': (0, 0, 255),    # Rojo
        'MEDIA': (0, 165, 255), # Naranja
        'OK': (0, 255, 0)       # Verde
    }.get(alert_level, (255, 255, 255))
    
    # Panel semi-transparente
    overlay = img_copy.copy()
    cv2.rectangle(overlay, (10, 10), (500, 130), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, img_copy, 0.3, 0, img_copy)
    
    # Texto del análisis
    cv2.putText(img_copy, f"ESTADO: {alert_level}", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, alert_color, 2)
    cv2.putText(img_copy, analysis['alert_message'], (20, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Estadísticas
    stats = analysis.get('statistics', {})
    stats_text = f"Trabajadores: {stats.get('persons', 0)} | Cascos: {stats.get('helmets', 0)} | Chalecos: {stats.get('vests', 0)}"
    cv2.putText(img_copy, stats_text, (20, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return img_copy

# =============================================
# INTERFAZ PRINCIPAL - SIDEBAR
# =============================================
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("⚙️ Configuración del Sistema")

# Configuración de parámetros
min_confidence = st.sidebar.slider(
    "Nivel de Confianza Mínimo", 
    0.1, 0.9, 0.6, 0.05,
    help="Ajusta qué tan seguras deben ser las detecciones"
)

alert_system_active = st.sidebar.checkbox("Sistema de Alertas Activo", True, 
                                         help="Activar/desactivar notificaciones")
auto_save_reports = st.sidebar.checkbox("Guardar Reportes Automáticamente", True,
                                       help="Guardar historial de análisis")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("🎯 Modo de Operación")
operation_mode = st.sidebar.radio(
    "Selecciona cómo usar SafeBuild:",
    ["📊 Modo Demo - Imágenes Predefinidas", "📸 Subir Mi Propia Imagen"],
    index=0
)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# =============================================
# INTERFAZ PRINCIPAL - CONTENIDO
# =============================================

# HEADER PRINCIPAL
st.markdown('<h1 class="main-header">🦺 SafeBuild</h1>', unsafe_allow_html=True)
st.markdown("### Sistema Inteligente de Monitoreo de Seguridad en Obras de Construcción")
st.markdown("---")

# COLUMNAS PRINCIPALES
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("👁️ Monitoreo en Tiempo Real")
    
    if operation_mode == "📊 Modo Demo - Imágenes Predefinidas":
        # MODO DEMO - IMÁGENES PREDEFINIDAS
        st.info("🎯 **Selecciona un escenario de obra para analizar:**")
        
        # Selector de escenario con descripciones
        scenario_option = st.radio(
            "Escenarios Disponibles:",
            [
                "✅ Escenario 1: Condiciones Seguras", 
                "⚠️ Escenario 2: Alertas de Seguridad", 
                "🚨 Escenario 3: Condiciones Críticas"
            ],
            index=0
        )
        
        # Mapear selección a URLs
        scenario_mapping = {
            "✅ Escenario 1: Condiciones Seguras": "escenario_seguro",
            "⚠️ Escenario 2: Alertas de Seguridad": "escenario_alerta", 
            "🚨 Escenario 3: Condiciones Críticas": "escenario_critico"
        }
        
        selected_scenario_key = scenario_mapping[scenario_option]
        
        # Botón para ejecutar análisis
        if st.button("🚀 Ejecutar Análisis de Seguridad", use_container_width=True):
            with st.spinner("🖼️ Cargando escenario de obra..."):
                # Cargar imagen de demo
                demo_image = load_demo_image(DEMO_IMAGES[selected_scenario_key])
                time.sleep(1)  # Simular tiempo de carga
            
            with st.spinner("🔍 Analizando condiciones de seguridad..."):
                # Simular detecciones de YOLO
                simulated_detections = simulate_detections(selected_scenario_key)
                # Ejecutar sistema experto
                safety_analysis = expert_system.analyze_detections(simulated_detections)
                time.sleep(1)  # Simular procesamiento
            
            # Mostrar resultados
            st.success("✅ Análisis completado correctamente")
            
            # Mostrar imagen con detecciones
            result_image = draw_detections_on_image(demo_image, simulated_detections, safety_analysis)
            st.image(result_image, caption=f"Resultado del Análisis - {scenario_option}", use_column_width=True)
            
            # Mostrar alerta según nivel
            alert_level = safety_analysis['alert_level']
            if alert_level == "ALTA":
                st.markdown(f"""
                <div class="alert-high">
                    <h3>🚨 ALERTA CRÍTICA DE SEGURIDAD</h3>
                    <p><strong>{safety_analysis['alert_message']}</strong></p>
                    <p>📋 <strong>Acción Recomendada:</strong> {safety_analysis['recommended_action']}</p>
                    <p>⏰ <strong>Prioridad:</strong> Resolución Inmediata</p>
                </div>
                """, unsafe_allow_html=True)
            elif alert_level == "MEDIA":
                st.markdown(f"""
                <div class="alert-medium">
                    <h3>⚠️ ALERTA DE SEGURIDAD</h3>
                    <p><strong>{safety_analysis['alert_message']}</strong></p>
                    <p>📋 <strong>Acción Recomendada:</strong> {safety_analysis['recommended_action']}</p>
                    <p>⏰ <strong>Prioridad:</strong> Resolución en 1 hora</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-ok">
                    <h3>✅ CONDICIONES SEGURAS</h3>
                    <p><strong>{safety_analysis['alert_message']}</strong></p>
                    <p>📋 <strong>Acción Recomendada:</strong> {safety_analysis['recommended_action']}</p>
                    <p>⏰ <strong>Estado:</strong> Operaciones Normales</p>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Estado inicial - mostrar instrucciones
            st.info("👆 **Presiona el botón 'Ejecutar Análisis' para comenzar**")
            
    else:
        # MODO SUBIR IMAGEN PERSONALIZADA
        st.info("📸 **Sube una imagen de tu obra para analizar**")
        
        uploaded_image = st.file_uploader(
            "Selecciona una imagen (JPG, PNG):", 
            type=['jpg', 'jpeg', 'png'],
            help="La imagen será analizada para detectar condiciones de seguridad"
        )
        
        if uploaded_image is not None:
            # Procesar imagen subida por el usuario
            user_image = Image.open(uploaded_image)
            image_array = np.array(user_image)
            
            with st.spinner("🔍 Analizando seguridad en la imagen..."):
                # Simular detecciones basadas en el nombre del archivo
                file_name = uploaded_image.name.lower()
                if "safe" in file_name or "good" in file_name:
                    user_detections = simulate_detections("escenario_seguro")
                elif "alert" in file_name or "warning" in file_name:
                    user_detections = simulate_detections("escenario_alerta")
                else:
                    user_detections = simulate_detections("escenario_critico")
                
                user_analysis = expert_system.analyze_detections(user_detections)
                processed_image = draw_detections_on_image(image_array, user_detections, user_analysis)
            
            # Mostrar resultados
            st.image(processed_image, caption="Análisis de Seguridad - Tu Imagen", use_column_width=True)
            
            # Mostrar alerta simple
            alert_level = user_analysis['alert_level']
            if alert_level == "ALTA":
                st.error(f"🚨 {user_analysis['alert_message']}")
                st.warning(f"📋 **Acción:** {user_analysis['recommended_action']}")
            elif alert_level == "MEDIA":
                st.warning(f"⚠️ {user_analysis['alert_message']}")
                st.info(f"📋 **Acción:** {user_analysis['recommended_action']}")
            else:
                st.success(f"✅ {user_analysis['alert_message']}")
                st.info(f"📋 **Acción:** {user_analysis['recommended_action']}")

with col2:
    st.subheader("📊 Panel de Control")
    
    # Mostrar estadísticas actuales
    if 'safety_analysis' in locals():
        current_stats = safety_analysis.get('statistics', {})
        workers_detected = current_stats.get('persons', 0)
        helmets_detected = current_stats.get('helmets', 0)
        vests_detected = current_stats.get('vests', 0)
        
        # Calcular cumplimiento
        compliance_rate = 0
        if workers_detected > 0:
            compliance_rate = min(helmets_detected, vests_detected) / workers_detected * 100
    else:
        workers_detected = helmets_detected = vests_detected = compliance_rate = 0
    
    # TARJETAS DE MÉTRICAS
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("**👥 Estadísticas de Personal**")
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Trabajadores", workers_detected)
        st.metric("Cascos", helmets_detected)
    with metric_col2:
        st.metric("Chalecos", vests_detected)
        st.metric("Cumplimiento", f"{compliance_rate:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ALERTAS ACTIVAS
    st.subheader("🚨 Estado Actual")
    if workers_detected > 0:
        if helmets_detected < workers_detected:
            missing_helmets = workers_detected - helmets_detected
            st.error(f"❌ **{missing_helmets}** trabajador(es) sin casco")
        else:
            st.success("✅ Todos con casco")
            
        if vests_detected < workers_detected:
            missing_vests = workers_detected - vests_detected
            st.warning(f"⚠️ **{missing_vests}** trabajador(es) sin chaleco")
        else:
            st.success("✅ Todos con chaleco")
    else:
        st.info("👀 No se detectaron trabajadores en el área analizada")
    
    # HISTORIAL DE ACTIVIDAD
    st.subheader("📋 Actividad Reciente")
    activity_data = {
        'Hora': [
            datetime.now().strftime("%H:%M:%S"), 
            '10:30:15', 
            '09:15:45',
            '08:45:30'
        ],
        'Evento': [
            'Análisis Actual', 
            'Inspección Zona B', 
            'Revisión Matutina',
            'Monitoreo Inicial'
        ],
        'Resultado': [
            safety_analysis.get('alert_level', 'N/A'), 
            'MEDIA', 
            'OK',
            'ALTA'
        ]
    }
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True, hide_index=True)

# =============================================
# SECCIÓN DE ANALYTICS
# =============================================
st.markdown("---")
st.subheader("📈 Estadísticas del Sistema")

# MÉTRICAS DEL SISTEMA
stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

with stats_col1:
    st.metric("Inspecciones Hoy", "24", "+12%")
with stats_col2:
    st.metric("Alertas Totales", "8", "-3%")
with stats_col3:
    st.metric("Tasa de Cumplimiento", "83%", "+5%")
with stats_col4:
    st.metric("Tiempo Respuesta", "2.1 min", "-0.3 min")

# =============================================
# INFORMACIÓN EN SIDEBAR
# =============================================
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.subheader("ℹ️ Información del Sistema")
st.sidebar.info("""
**SafeBuild v1.0**  

🚧 **Sistema Integrado de:**  
• Visión por Computadora  
• Sistema Experto de Reglas  
• Alertas Automáticas  

📞 **Soporte:**  
soporte@safebuild.com
""")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# =============================================
# FOOTER
# =============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>SafeBuild v1.0</strong> - Sistema Inteligente de Monitoreo de Seguridad en Obras</p>
    <p>🚧 <strong>Trabajo Práctico Integrador</strong> - Desarrollo de Sistemas de Inteligencia Artificial 🚧</p>
    <p style="font-size: 0.8rem;">Desarrollado con Streamlit | OpenCV | Sistema Experto</p>
</div>
""", unsafe_allow_html=True)
