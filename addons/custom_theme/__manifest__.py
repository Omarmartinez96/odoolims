{
    'name': 'Custom Theme Proteus',
    'version': '1.0',
    'category': 'Laboratory',
    'summary': 'Custom theme for Proteus Laboratorio',
    'author': 'Omar Martinez',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
        'web.assets_frontend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
