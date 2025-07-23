{
    'name': 'Recepción de Muestras LIMS',
    'version': '1.0',
    'summary': 'Módulo para la recepción y verificación de muestras en laboratorio',
    'description': '''
        Permite a los técnicos de recepción:
        - Acceder a las cadenas de custodia pendientes
        - Verificar condiciones de recepción de muestras
        - Asignar códigos de muestra automáticamente
        - Controlar estados de recepción
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'lims_customer',
        'lims_reception',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/lims_sample_reception_views.xml',
        'views/lims_custody_chain_reception_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}