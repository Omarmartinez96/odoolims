# addons/lims_analysis_mass_tools/__manifest__.py
{
    'name': 'LIMS - Herramientas de Asignación Masiva',
    'version': '1.0.0',
    'summary': 'Herramientas de productividad para asignación masiva en análisis LIMS',
    'description': '''
        Herramientas de productividad para LIMS Analysis v2:
        
        🎯 CARACTERÍSTICAS:
        - Asignación masiva de analistas con verificación PIN
        - Asignación masiva de medios de cultivo por sets o individual
        - Asignación masiva de fechas de procesamiento
        - Asignación masiva de equipos de laboratorio
        - Cambio masivo de estados de parámetros
        - Asignación masiva de ambientes de procesamiento
        
        ⚡ BENEFICIOS:
        - Reduce tiempo de captura de datos repetitivos
        - Minimiza errores por asignaciones manuales
        - Mejora la eficiencia del flujo de trabajo
        - Mantiene consistencia en los datos
    ''',
    'sequence': 14,
    'category': 'LIMS',
    'author': 'Omar Martinez',
    'website': 'https://www.proteuslaboratorio.com',
    'depends': [
        'base',
        'web',
        'lims_analysis_v2',  # Dependencia principal
        'lims_analysis_config',  # Para analistas y configuraciones
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Vistas de wizards
        'views/mass_wizard_views.xml',
        
        # Herencias de vistas existentes
        'views/inherited_analysis_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,  
    'auto_install': False,
    'license': 'LGPL-3',
}