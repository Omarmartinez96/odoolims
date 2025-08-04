{
    'name': 'LIMS - Configuración de Análisis',
    'version': '1.0',
    'summary': 'Configuración base para análisis LIMS',
    'description': '''
        Módulo base de configuración que incluye:
        - Equipos de laboratorio
        - Medios de cultivo y lotes
        - Controles de calidad de medios
        - Configuraciones base para análisis
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'mail',
        'lims_reception',  # Para lims.culture.media
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Vistas de configuración
        'views/lims_equipment_views.xml',
        'views/lims_culture_media_batch_views.xml',
        'views/lims_culture_media_qc_views.xml',
    ],
    'installable': True,
    'application': False,  # Es un módulo de configuración, no aplicación
    'auto_install': False,
    'license': 'LGPL-3',
}