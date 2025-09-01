from odoo import models, fields, api

class LimsParameterMediaProcess(models.Model):
    _name = 'lims.parameter.media.process'
    _description = 'Medios de Cultivo por Proceso en Parámetros'
    _order = 'sequence, process_type'

    sequence = fields.Integer(
        string='Secuencia', 
        default=10
    )
    
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro',
        required=True,
        ondelete='cascade'
    )
    
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),  
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=True)
    
    culture_media_id = fields.Many2one(
        'lims.culture.media',
        string='Medio de Cultivo',
        required=True
    )
    
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
    ], string='Uso del Medio', required=True, default='diluyente')
    
    notes = fields.Text(
        string='Notas'
    )
    
    # @api.onchange('process_type')
    # def _onchange_process_type_default_usage(self):
    #     """Establecer uso por defecto según el tipo de proceso"""
    #     if self.process_type == 'pre_enrichment':
    #         self.media_usage = 'enriquecimiento'
    #     elif self.process_type == 'selective_enrichment':
    #         self.media_usage = 'desarrollo_selectivo'
    #     elif self.process_type == 'quantitative':
    #         self.media_usage = 'diluyente'
    #     elif self.process_type == 'qualitative':
    #         self.media_usage = 'desarrollo_selectivo'
    #     elif self.process_type == 'confirmation':
    #         self.media_usage = 'pruebas_bioquimicas'