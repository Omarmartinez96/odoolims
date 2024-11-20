{
    'name': 'Sale Extension',
    'version': '1.0',
    'summary': 'Extensión para agregar código de cliente basado en VAT',
    'description': (
        'Este módulo extiende el módulo de ventas para generar un código de cliente '
        'automáticamente basado en los tres primeros caracteres del VAT (RFC en México).'
    ),
    'author': 'Omar Martínez',
    'website': 'https://proteuslaboratorio.com',
    'category': 'Sales',
    'depends': ['sale'],  # Mantén 'sale' si planeas agregar más funcionalidades a ventas
    'data': [
        'views/sale_extension_views.xml',  # Vista personalizada de res.partner
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
