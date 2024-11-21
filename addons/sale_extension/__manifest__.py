{
    'name': 'Sale Extension',
    'version': '1.0',
    'summary': 'Extensión básica del módulo de ventas',
    'description': 'Este módulo permite agregar un código de cliente manual debajo del Tax ID.',
    'author': 'Omar Martínez',
    'website': 'https://proteuslaboratorio.com',
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_extension_views.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
