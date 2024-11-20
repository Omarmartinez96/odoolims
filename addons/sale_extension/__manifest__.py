{
    'name': 'Sale Extension',
    'version': '1.0',
    'summary': 'Extensión básica del módulo de ventas',
    'description': 'Este módulo extiende el módulo de ventas para agregar RFC y código de cliente.',
    'author': 'Omar Martínez',
    'website': 'proteuslaboratorio.com',
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'views/sale_extension_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
