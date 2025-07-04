{
    'name': 'Custom Theme Proteus',
    'version': '1.0',
    'category': 'Laboratory',
    'summary': 'Custom theme for Proteus Laboratorio',
    'author': 'Omar Martinez',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'custom_theme/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            'custom_theme/static/src/scss/custom_styles.scss',
        ],
        'web.assets_frontend': [
            'custom_theme/static/src/scss/custom_styles.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
