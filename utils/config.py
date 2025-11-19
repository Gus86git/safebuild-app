"""
Configuraciones del sistema SafeBuild
Centraliza todas las constantes y configuraciones del proyecto
"""

# =============================================
# CONFIGURACIÓN DE CLASES PARA DETECCIÓN
# =============================================
CLASS_NAMES = {
    'person': 'Trabajador',
    'helmet': 'Casco de Seguridad', 
    'safety_vest': 'Chaleco Reflectante',
    'no_helmet': 'Falta de Casco',
    'no_vest': 'Falta de Chaleco'
}

# =============================================
# NIVELES DE ALERTA Y SU CONFIGURACIÓN
# =============================================
ALERT_LEVELS = {
    'ALTA': {
        'color': '#DC2626',      # Rojo
        'icon': '🚨',
        'priority': 1,
        'response_time': 'Inmediata',
        'notification': 'Todas las vías'
    },
    'MEDIA': {
        'color': '#D97706',      # Naranja
        'icon': '⚠️', 
        'priority': 2,
        'response_time': '1 hora',
        'notification': 'Supervisor y Jefe de Cuadrilla'
    },
    'OK': {
        'color': '#059669',      # Verde
        'icon': '✅',
        'priority': 3,
        'response_time': 'Rutinario',
        'notification': 'Registro en sistema'
    }
}

# =============================================
# REGLAS DE SEGURIDAD GENERALES
# =============================================
SAFETY_RULES = {
    'helmet_required': True,
    'vest_required': True,
    'min_workers_for_alert': 1,
    'auto_generate_reports': True,
    'notification_emails': ['supervisor@obra.com', 'seguridad@empresa.com']
}

# =============================================
# CONFIGURACIÓN DEL MODELO (SIMULADO)
# =============================================
MODEL_CONFIG = {
    'confidence_threshold': 0.6,
    'iou_threshold': 0.45,
    'image_size': 640,
    'max_detections': 50
}

# =============================================
# COLORES PARA VISUALIZACIÓN
# =============================================
COLORS = {
    'person': (0, 255, 0),      # Verde
    'helmet': (255, 0, 0),      # Azul
    'safety_vest': (0, 0, 255), # Rojo
    'background': (240, 240, 240),
    'text_dark': (50, 50, 50),
    'text_light': (255, 255, 255)
}

# =============================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =============================================
APP_CONFIG = {
    'name': 'SafeBuild v1.0',
    'version': '1.0.0',
    'description': 'Sistema Inteligente de Monitoreo de Seguridad en Obras',
    'author': 'Equipo de Desarrollo IA',
    'contact': 'soporte@safebuild.com'
}

