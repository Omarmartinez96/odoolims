{
    'name': 'LIMS Customer Management',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión personalizada de clientes para LIMS',
    'depends': ['base'],
    'data': [
        'views/lims_branch_views.xml',  # Cargar modelos antes de permisos
        'views/lims_customer_views.xml',
        'security/ir.model.access.csv',  # ⚠️ Esto debe ir al final
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
