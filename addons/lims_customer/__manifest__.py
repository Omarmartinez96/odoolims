{
    'name': 'LIMS Customer Management',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión personalizada de clientes para LIMS',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir.model.csv',
        'views/lims_customer_views.xml',
    ],
    'installable': True,
    'application': True,  # ✅ Debe ser True si se usa como módulo independiente
    'license': 'LGPL-3',
}
