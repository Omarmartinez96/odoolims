# Archivo: __manifest__.py
{
    'name': 'Sale Extension',
    'version': '1.0',
    'summary': 'Extensión básica del módulo de ventas',
    'description': 'Este módulo extiende el módulo de ventas para agregar funcionalidades adicionales.',
    'author': 'Omar Martínez',
    'website': 'https://proteuslaboratorio.com',
    'category': 'Sales',
    'depends': ['sale'],  # Dependencia del módulo de ventas
    'data': [
        'views/sale_extension_views.xml',  # Archivo de vistas para mostrar el nuevo campo
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'test': False, #Desactiva las pruebas automáticas
}
