{
    'name': 'Análisis de Muestras LIMS v2',
    'version': '2.0.0',
    'summary': 'Sistema completo de análisis de laboratorio - Versión optimizada',
    'description': '''
        Sistema completo para gestión de análisis de laboratorio v2:
        
        🔬 CARACTERÍSTICAS PRINCIPALES:
        - Ejecución de análisis de muestras con workflow optimizado
        - Registro detallado de resultados de parámetros
        - Sistema de firmas digitales con trazabilidad completa
        - Reportes dinámicos (sin almacenamiento innecesario)
        - Control de calidad integrado y automatizado
        - Sistema de revisiones completo con historial
        - Gestión avanzada de incubaciones con estados en tiempo real
        
        🎯 MEJORAS DE LA V2:
        - Interfaz de usuario moderna y optimizada
        - Modelos unificados para mejor rendimiento
        - Reportes dinámicos que se generan al momento
        - Flujo de trabajo simplificado y más intuitivo
        - Mejor organización de datos y menor redundancia
        - Sistema de medios consolidado en un solo modelo
        
        📊 FUNCIONALIDADES AVANZADAS:
        - Datos crudos de diluciones con cálculos automáticos
        - Seguimiento de incubaciones con alertas de vencimiento
        - Control de calidad ejecutado con estados y trazabilidad
        - Gestión de equipos involucrados en cada análisis
        - Sistema de confirmaciones para análisis cualitativos
        - Acciones masivas para eficiencia operativa
        
        🔄 SISTEMA DE REVISIONES:
        - Creación automática de revisiones con copia completa de datos
        - Trazabilidad completa de cambios y motivos
        - Numeración automática de revisiones
        - Historial completo de modificaciones
        
        🖊️ FIRMAS DIGITALES:
        - Captura de firmas digitales con metadatos completos
        - Cancelación y recuperación de firmas
        - Generación de reportes para firma manual adicional
        - Trazabilidad completa del proceso de autorización
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'website': 'https://www.proteuslaboratorio.com',
    'depends': [
        'base',
        'mail',
        'web',
        'lims_customer',
        'lims_reception',
        'lims_sample_reception',
        'lims_analysis_config',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Vistas principales
        'views/lims_analysis_views.xml',
        'views/lims_parameter_views.xml',
        'views/wizard_views.xml',
        
        # Reportes dinámicos
        'report/report_actions.xml',
        'report/report_templates.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'price': 0.0,
    'currency': 'USD',
}