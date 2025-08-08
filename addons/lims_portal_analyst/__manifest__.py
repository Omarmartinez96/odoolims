{
    'name': 'LIMS Portal Analyst - Básico',
    'version': '1.0.0',
    'summary': 'Portal básico para analistas de laboratorio',
    'description': '''
        Versión básica del portal para analistas.
        
        FASE 1 - Funcionalidades incluidas:
        - Dashboard básico
        - Lista simple de parámetros
        - Formulario básico de edición
        - Seguridad básica
        
        SIN: Auto-guardado, JavaScript avanzado, atajos de teclado
    ''',
    'category': 'LIMS',
    'author': 'Elite Development Team',
    'website': 'https://www.proteuslaboratorio.com',
    'depends': [
        'portal',
        'lims_analysis_v2',
    ],
    'data': [
        # Seguridad básica
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Vistas básicas
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}