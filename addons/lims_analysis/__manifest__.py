{
    'name': 'Análisis de Muestras LIMS',
    'version': '1.0',
    'summary': 'Módulo para ejecutar análisis y registrar resultados',
    'description': '''
        Permite:
        - Ejecutar análisis de muestras
        - Registrar resultados de parámetros
        - Sistema de firmas y reportes
        - Gestión de workflow de análisis
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'mail',
        'lims_customer',
        'lims_reception',
        'lims_sample_reception',
        'lims_analysis_config',  # NUEVA DEPENDENCIA
    ],
    'data': [
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'views/lims_analysis_views.xml',
        'report/report_analysis_results.xml',
        'report/report_analysis_action.xml',
        'views/lims_analysis_report_views.xml',
        'views/wizard_views.xml',
        'data/cron_jobs.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}