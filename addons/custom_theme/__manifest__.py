{
    'name': 'Custom Theme Proteus',
    'version': '1.0',
    'category': 'Laboratory',
    'summary': 'Custom theme for Proteus Laboratorio',
    'author': 'Omar Martinez',
    'depends': ['web'],
    'assets': {
        # Sobrescribimos variables en el momento correcto
        'web._assets_primary_variables': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
        # Añadimos estilos personalizados al frontend y backend
        'web.assets_backend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
        'web.assets_frontend': [
            'custom_theme/static/src/scss/custom_variables.scss',
        ],
        # Asegurar bootstrap mixins y funciones para darken()/lighten()
        'web._assets_helpers': [
            # ruta interna, no es obligatorio repetir si ya carga helpers
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
