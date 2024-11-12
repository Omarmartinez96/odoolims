# __manifest__.py
{
    'name': "Customer Management",
    'summary': "Módulo para la gestión de clientes",
    'description': "Módulo para gestionar clientes en Odoo.",
    'author': "Tu Nombre o Compañía",
    'category': 'Uncategorized',
    'version': '1.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',    
        'views/customer_view.xml',  # Ruta al archivo XML donde están las vistas y menús
    ],
    'application': True,
}
