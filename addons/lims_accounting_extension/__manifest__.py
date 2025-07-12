{
    'name': 'LIMS Accounting Extension',
    'version': '1.0',
    'summary': 'Plantillas de factura LIMS personalizadas',
    'category': 'Laboratory',
    'author': 'Proteus LIMS',
    'depends': ['account', 'lims_sale_extension'],
    'data': [
        'views/inherit_account_report_invoice_document.xml',       
        'views/payment_table_stub.xml',     
    ],
    'installable': True,
    'application': True,
}