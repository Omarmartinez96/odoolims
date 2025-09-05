{
    'name': 'LIMS Extensión de Contabilidad',
    'version': '1.0',
    'category': 'LIMS',
    'author': 'Omar Martínez',
    'depends': [
        'account',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',  # AGREGAR
        'views/account_move_views.xml',
        'wizard/payment_wizard_views.xml',  # AGREGAR
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}