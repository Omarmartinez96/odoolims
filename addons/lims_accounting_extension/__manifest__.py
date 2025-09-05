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
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}