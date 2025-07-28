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
        'lims_customer',
        'lims_reception',
        'lims_sample_reception', 
    ],
    'data': [
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'views/lims_culture_media_qc_views.xml',
        'views/lims_culture_media_batch_views.xml',
        'views/lims_analysis_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}