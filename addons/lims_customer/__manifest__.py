{
    'name': 'LIMS Customer Management',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Laboratory',
    'summary': 'Gestión de Clientes en LIMS con Sucursales, Departamentos y Contactos',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/lims_customer_views.xml',
        'views/lims_branch_views.xml',
        'views/lims_department_views.xml',
        'views/lims_contact_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
