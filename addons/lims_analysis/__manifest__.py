{
    'name': 'Análisis de Muestras LIMS',
    'version': '1.0',
    'summary': 'Módulo para ejecutar análisis y registrar resultados',
    'description': '''
        Sistema completo para gestión de análisis de laboratorio:
        - Ejecución de análisis de muestras
        - Registro de resultados de parámetros
        - Sistema de firmas digitales
        - Gestión de reportes y workflow
        - Control de calidad integrado
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'mail',
        'lims_customer',
        'lims_reception',
        'lims_sample_reception',
        'lims_analysis_config',
    ],
    'data': [
        # Datos base
        'data/sequences.xml',
        'data/cron_jobs.xml',
        
        # Seguridad
        'security/ir.model.access.csv',
        
        # Vistas principales
        'views/lims_analysis_views.xml',
        'views/lims_analysis_report_views.xml',
        'views/wizard_views.xml',
        
        # Reportes
        'report/report_analysis_action.xml',
        'report/report_analysis_results.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}