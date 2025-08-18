{
    'name': 'LIMS - Configuración de Analistas',
    'version': '1.0',
    'summary': 'Gestión de analistas con verificación PIN',
    'description': '''
        Módulo para gestión de analistas de laboratorio que incluye:
        - Registro de analistas con datos personales
        - Sistema de PIN para verificación de identidad
        - Widget reutilizable en cualquier módulo LIMS
        - Trazabilidad de actividades por analista
    ''',
    'sequence': 10,
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/lims_analyst_views.xml',
        'views/analyst_pin_wizard_views.xml',
        'views/analyst_pin_templates.xml',
        'data/lims_analyst_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lims_analyst_config/static/src/js/analyst_pin_widget.js',
            'lims_analyst_config/static/src/css/analyst_pin_widget.css',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}