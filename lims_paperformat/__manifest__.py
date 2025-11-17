{
    'name': 'LIMS Paper Format',
    'version': '1.0',
    'summary': 'Paper formats personalizados para reportes LIMS',
    'description': 'Define tipos de papel personalizados para reportes como cotizaciones, resultados o facturas en el sistema LIMS.',
    'category': 'LIMS',
    'author': 'Omar Alejandro Martínez ',
    'depends': ['base', 'web'],
    'data': [
        'data/paperformat.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}