{
    'name': 'Análisis de Muestras LIMS',
    'version': '1.0',
    'summary': 'Módulo para ejecutar análisis y registrar resultados',
    'description': '''
        Permite:
        - Crear lotes de medios de cultivo
        - Ejecutar análisis de muestras
        - Registrar resultados de parámetros
        - Control de calidad de medios
    ''',
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'depends': [
        'base',
        'mail',
        'lims_customer',
        'lims_reception',
        'lims_sample_reception', 
    ],
    'data': [
        # PRIMERO: Datos básicos y seguridad
        'data/sequences.xml',
        'data/cron_jobs.xml', 
        'security/ir.model.access.csv',
        
        # SEGUNDO: Reportes (para que las vistas puedan referenciarlos)
        'report/report_analysis_results.xml',
        'report/report_analysis_action.xml',
        
        # TERCERO: Vistas básicas que definen menús principales
        'views/lims_analysis_views.xml',  # Define menu_lims_analysis_config
        'views/lims_equipment_views.xml',
        
        # CUARTO: Vistas que definen acciones
        'views/lims_culture_media_batch_views.xml',  # Define action_culture_media_batches
        
        # QUINTO: Vistas que referencian reportes y acciones
        'views/lims_analysis_report_views.xml',  # Referencia reportes
        'views/wizard_views.xml',  # Referencia reportes
        'views/lims_culture_media_qc_views.xml',  # Referencia menús y acciones
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}