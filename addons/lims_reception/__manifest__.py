{
    'name': "Cadenas de Custodia",
    'version': '1.1',
    'summary': "Gestión de Cadenas de Custodia para LIMS",
    'description': """
        Módulo para registrar Cadenas de Custodia y Muestras dentro de un LIMS básico.
    """,
    'category': 'Tools',  
    'author': "Laboratorio Proteus",
    'depends': [
        'base', 
        'lims_customer', 
        'sale',
        'mail',
    ],
    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        # reportes
        'report/report_custody_chain.xml',
        'report/report_custody_chain_action.xml',
        'data/email_templates.xml',
        'views/lims_sample_views.xml',
        'views/lims_custody_chain_views.xml',

    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
