{
    'name': 'LIMS Reception Module',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión de Recepción de Muestras para LIMS',
    'depends': ['base', 'sale_extension'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/lims_sample_views.xml',
        'views/lims_custody_chain_views.xml',  # Agregar si necesitas vistas para cadenas de custodia
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
