{
    'name': 'LIMS Customer Management',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión personalizada de clientes para LIMS',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/lims_branch_views.xml',  # Agregado aquí
        'views/lims_customer_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
