{
    'name': "Recepción de Muestras",
    'version': '1.0',
    'summary': "Gestión de Recepción de Muestras para LIMS",
    'description': """
        Módulo para registrar Cadenas de Custodia y Muestras dentro de un LIMS básico.
    """,
    'category': 'Tools',  # <-- Cambiado para que aparezca en el listado de Apps
    'author': "Laboratorio Proteus",
    'depends': ['base', 'lims_customer'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/lims_sample_views.xml',
        'views/lims_custody_chain_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
