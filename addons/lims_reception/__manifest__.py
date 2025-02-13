{
    'name': "LIMS Reception Module",
    'version': '1.0',
    'summary': "Gestión de Recepción de Muestras para LIMS",
    'category': 'Laboratory',
    'author': "Tu Nombre",
    'depends': ['base', 'lims_customer'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/lims_sample_views.xml',
        'views/lims_custody_chain_views.xml',
    ],
    'installable': True,
    'application': True,  # <--- ESTO DEBE ESTAR PRESENTE
    'license': 'LGPL-3',
}
