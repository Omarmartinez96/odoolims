{
    'name': 'Sale Extension',
    'version': '1.0',
    'summary': 'Extensión básica del módulo de ventas',
    'description': 'Este módulo permite agregar un código de cliente manual y mostrarlo en la vista de lista y formulario.',
    'author': 'Omar Martínez',
    'website': 'https://proteuslaboratorio.com',
    'category': 'Sales',
    'depends': ['sale'],  # Depende del módulo de ventas
    'data': [
        'views/sale_extension_views.xml',  # Archivo de vistas
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
