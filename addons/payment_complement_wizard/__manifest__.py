{
    'name': 'Payment Complement Wizard',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Simplified Payment Complement Generation for Mexican Localization',
    'depends': [
        'account',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/payment_complement_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}