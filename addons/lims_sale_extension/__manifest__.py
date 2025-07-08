{
    'name': 'Integración LIMS con Ventas',
    'version': '1.0',
    'category': 'Laboratory',
    'depends': [
        'sale',
        'lims_customer',
        'web',
    ],
    'data': [
        'views/external_layout_inherit_lims.xml',
        'views/report_invoice_translate_lines.xml',
        'data/sale_order_sequence.xml',
        'views/sale_order_views.xml',
        'views/report_quote.xml',
        'views/report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
