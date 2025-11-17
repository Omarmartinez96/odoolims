{
    'name': 'LIMS - Bitácora de Uso de Equipos',
    'version': '1.0.0',
    'summary': 'Registro y trazabilidad del uso de equipos de laboratorio',
    'category': 'LIMS',
    'depends': [
        'base',
        'lims_analysis_config',
        'lims_analysis_v2',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_views.xml',  # Wizards primero
        'views/lims_equipment_usage_views.xml',
        'views/lims_lab_equipment_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}