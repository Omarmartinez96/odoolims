# __manifest__.py
{
    'name': "LIMS Customer Extension",
    'version': '1.0',
    'depends': ['base', 'contacts'],
    'author': "Tu Nombre",
    'category': 'Sales',
    'summary': 'Gestión personalizada de clientes, sucursales y departamentos',
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/res_sucursal_views.xml',
        'views/res_departamento_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
