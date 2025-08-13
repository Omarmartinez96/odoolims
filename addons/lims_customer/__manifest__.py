{
    'name': 'Gestión de Clientes',
    'version': '1.0',
    'author': 'Omar Martinez',
    'sequence': 10,
    'category': 'LIMS',
    'summary': 'Gestión personalizada de clientes para LIMS',
    'depends': [
        'base',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/lims_customer_views.xml',
        'views/lims_branch_views.xml',
        'views/lims_department_views.xml',
        'views/lims_contact_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
