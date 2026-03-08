{
    'name': 'LIMS Portal Web',
    'version': '17.0.1.0',
    'author': 'Omar Martinez',
    'category': 'LIMS',
    'summary': 'Portal web para clientes y usuarios de Proteus Laboratorio',
    'description': '''
        Módulo que provee el sitio web principal del laboratorio Proteus, incluyendo:
        - Página de inicio con acceso a portal de clientes y usuarios
        - Formulario de contacto comercial (genera solicitudes de venta)
        - Formulario de sugerencias, quejas y felicitaciones
        - Panel de administración en backend para gestionar solicitudes web
    ''',
    'website': 'https://www.proteuslaboratorio.com',
    'depends': [
        'website',
        'portal',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/backend_views.xml',
        'views/website_homepage.xml',
        'views/website_contact_sales.xml',
        'views/website_feedback.xml',
        'views/website_pages.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'lims_website/static/src/scss/lims_website.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
