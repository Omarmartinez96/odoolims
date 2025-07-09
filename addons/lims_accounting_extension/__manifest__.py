{
    'name': 'LIMS Accounting Extension',
    'version': '1.0',
    'summary': 'Plantillas de factura LIMS personalizadas',
    'category': 'Laboratory',
    'author': 'Proteus LIMS',
    'depends': ['account', 'lims_sale_extension'],
    'data': [
        'views/external_layout_invoice_lims.xml',
        'views/report_invoice.xml',
        'views/report.xml',
    ],
    'installable': True,
    'application': True,
}