{
    'name': 'Análisis de Muestras',
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
    ''',
    'sequence': 13,
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
        'lims_paperformat',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Vistas de wizards PRIMERO
        'views/wizard_views.xml',
        
        # Vistas principales
        'views/lims_analysis_views.xml', 
        'views/lims_parameter_views.xml',
        'views/lims_dashboard_views.xml',
        
        # Reportes dinámicos
        'report/report_actions.xml',
        'report/report_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}