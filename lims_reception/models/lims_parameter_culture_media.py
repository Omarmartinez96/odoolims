from odoo import models, fields, api

class LimsParameterCultureMedia(models.Model):
    _name = 'lims.parameter.culture.media'
    _description = 'Medios de Cultivo por Parámetro'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Secuencia', 
        default=10
    )
    # FUNCIÓN: Conecta con el parámetro padre
    # PARA QUE: Saber a qué parámetro pertenece este medio
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro',
        required=True,
        ondelete='cascade'  # Si se borra el parámetro, se borra esta relación
    )
    # FUNCIÓN: Conecta con el catálogo de medios
    # PARA QUE: Seleccionar un medio del catálogo maestro
    culture_media_id = fields.Many2one(
        'lims.culture.media',
        string='Medio de Cultivo',
        required=True
    )
    # FUNCIÓN: Notas específicas para este parámetro
    # PARA QUE: El mismo medio puede tener instrucciones diferentes 
    #          según el parámetro (ej: "Incubar 24h para Coliformes, 48h para Salmonella")
    notes = fields.Text(
        string='Notas'
    )

    # DESPUÉS del campo `notes`, AGREGAR:
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),  
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=False, default='quantitative')

    media_usage = fields.Selection([
        ('diluyente', 'Diluyente'),
        ('eluyente', 'Eluyente'),
        ('enriquecimiento', 'Enriquecimiento'),
        ('desarrollo_selectivo', 'Desarrollo Selectivo'),
        ('desarrollo_diferencial', 'Desarrollo Diferencial'),
        ('desarrollo_selectivo_diferencial', 'Desarrollo Selectivo y Diferencial'),
        ('pruebas_bioquimicas', 'Pruebas Bioquímicas'),
        ('transporte', 'Transporte'),
        ('mantenimiento', 'Mantenimiento'),
        ('otro', 'Otro')
    ], string='Uso del Medio', required=False, default='diluyente')

    @api.onchange('process_type')
    def _onchange_process_type_default_usage(self):
        """Establecer uso por defecto según el tipo de proceso"""
        if self.process_type == 'pre_enrichment':
            self.media_usage = 'enriquecimiento'
        elif self.process_type == 'selective_enrichment':
            self.media_usage = 'desarrollo_selectivo'
        elif self.process_type == 'quantitative':
            self.media_usage = 'diluyente'
        elif self.process_type == 'qualitative':
            self.media_usage = 'desarrollo_selectivo'
        elif self.process_type == 'confirmation':
            self.media_usage = 'pruebas_bioquimicas'

    def update_existing_records(self):
        """Método temporal para actualizar registros existentes"""
        existing_records = self.search([
            '|', 
            ('process_type', '=', False), 
            ('media_usage', '=', False)
        ])
        
        for record in existing_records:
            record.write({
                'process_type': 'quantitative',
                'media_usage': 'diluyente'
            })
        
        return f"Actualizados {len(existing_records)} registros"