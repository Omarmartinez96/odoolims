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
        # PASO 1: Datos básicos y seguridad
        'data/sequences.xml',
        'security/ir.model.access.csv',
        
        # PASO 2: Vistas que definen elementos base (menús raíz y configuración)
        'views/lims_culture_media_qc_views.xml',  # Define menu_lims_analysis_root
        
        # PASO 3: Vistas de modelos principales
        'views/lims_analysis_views.xml',  # Vistas principales de análisis
        'views/lims_equipment_views.xml',  # Vistas de equipos
        'views/lims_culture_media_batch_views.xml',  # Vistas de lotes de medios
        
        # PASO 4: Vistas que referencian elementos base y reportes
        'views/lims_analysis_report_views.xml',  # Referencia menu_lims_analysis_root
        
        # PASO 5: Wizards (dependen de modelos principales)
        'views/wizard_views.xml',
        
        # PASO 6: Reportes (al final para que las vistas puedan referenciarlos)
        'report/report_analysis_results.xml',
        'report/report_analysis_action.xml',
        
        # PASO 7: Trabajos programados (al final)
        'data/cron_jobs.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}