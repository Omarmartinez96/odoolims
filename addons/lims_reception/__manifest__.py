{
    'name': 'LIMS Reception Module',
    'version': '1.0',
    'author': 'Omar Martinez',
    'category': 'Laboratory',
    'summary': 'Gestión de Recepción de Muestras para LIMS',
    'depends': ['base', 'sale_extension'],  # Agrega otros módulos si es necesario
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/lims_sample_views.xml',
    ],
    'installable': True,
    'application': True,
}
