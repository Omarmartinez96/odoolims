{
    'name': "Cadenas de Custodia",
    'version': '1.0',
    'summary': "Gestión de Cadenas de Custodia para LIMS",
    'description': """
        Módulo para registrar Cadenas de Custodia y Muestras dentro de un LIMS básico.
    """,
    'category': 'Tools',  
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
