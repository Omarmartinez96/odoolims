{
    'name': "Cadenas de Custodia",
    'version': '1.0',
    'summary': "Gestión de Cadenas de Custodia para LIMS",
    'description': """
        Módulo para registrar Cadenas de Custodia y Muestras dentro de un LIMS básico.
    """,
    'sequence': 11,
    'category': 'LIMS',
    'author': "Omar Martinez",
    'depends': [
        'base', 
        'lims_customer', 
        'sale',
        'mail',
        'mass_mailing',
        'web',
        'lims_analyst_config',
    ],
    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        # reportes
        'report/report_custody_chain.xml',
        'report/report_custody_chain_action.xml',
        'data/email_templates.xml',
        'views/digital_signature_views.xml',
        'views/lims_custody_chain_views.xml',
        'views/lims_sample_template_views.xml',
        'views/lims_parameter_views.xml',
        'views/basic_models_views.xml',
        'data/quality_control_types_data.xml',
        'views/lims_quality_control_views.xml',
        'views/lims_culture_media_views.xml',
        # Wizards
        'views/wizards/custody_chain_duplicate_wizard_views.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
