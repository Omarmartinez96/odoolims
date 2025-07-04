{
    'name': 'Custom Theme Proteus',
    'version': '1.0',
    'category': 'Laboratory',
    'summary': 'Custom theme for Proteus Laboratorio',
    'author': 'Omar Martinez',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'custom_theme/static/src/scss/custom_variables.scss'),
        ],
        'web.assets_backend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
        'web.assets_frontend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
