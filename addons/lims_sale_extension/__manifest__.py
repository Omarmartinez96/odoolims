{
    'name': 'Integración LIMS con Ventas',
    'version': '1.0',
    'depends': [
        'sale',
        'lims_customer',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
