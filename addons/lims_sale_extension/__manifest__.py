{
    'name': 'Integración LIMS con Ventas',
    'version': '1.0',
    'category': 'Laboratory',
    'depends': [
        'sale',
        'lims_customer',
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/report_quote.xml',
        'views/report.xml',
        'views/external_layout_inherit.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
