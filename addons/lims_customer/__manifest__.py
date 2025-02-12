{
    'name': 'LIMS Customer Management',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión personalizada de clientes para LIMS',
    'depends': ['base'],
    'data': [
        'data/ir.model.csv',
        'security/ir.model.access.csv',
        'views/lims_customer_views.xml',
    ],
    'installable': True,
    'application': True,  # ✅ Debe ser True si se usa como módulo independiente
    'license': 'LGPL-3',
}
