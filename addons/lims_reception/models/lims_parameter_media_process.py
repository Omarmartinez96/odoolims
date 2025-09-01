from odoo import models, fields

class LimsParameterMediaProcess(models.Model):
    _name = 'lims.parameter.media.process'
    _description = 'Medios de Cultivo por Proceso en Parámetros'
    _order = 'sequence'

    sequence = fields.Integer(
        string='Secuencia', 
        default=10
    )
    
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro',
        ondelete='cascade'
    )
    
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),  
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', default='quantitative')
    
    culture_media_name = fields.Char(
        string='Nombre del Medio'
    )
    
    media_usage = fields.Selection([
        ('diluyente', 'Diluyente'),
        ('enriquecimiento', 'Enriquecimiento'),
        ('desarrollo_selectivo', 'Desarrollo Selectivo'),
        ('pruebas_bioquimicas', 'Pruebas Bioquímicas'),
        ('otro', 'Otro')
    ], string='Uso del Medio', default='diluyente')
    
    notes = fields.Text(string='Notas')