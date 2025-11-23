from odoo import models, fields, api

class LimsMediaSet(models.Model):
    _name = 'lims.media.set'
    _description = 'Sets de Medios de Cultivo'
    _order = 'process_type, name'

    name = fields.Char(
        string='Nombre del Set',
        required=True,
        help='Ej: Salmonella USP - Pre enriquecimiento'
    )
    
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=True)
    
    description = fields.Text(
        string='Descripción',
        help='Descripción del set y cuándo utilizarlo'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Líneas del set
    media_line_ids = fields.One2many(
        'lims.media.set.line',
        'media_set_id',
        string='Medios del Set'
    )
    
    times_used = fields.Integer(
        string='Veces Utilizado',
        default=0,
        readonly=True
    )


class LimsMediaSetLine(models.Model):
    _name = 'lims.media.set.line'
    _description = 'Líneas de Sets de Medios'
    _order = 'sequence'

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    media_set_id = fields.Many2one(
        'lims.media.set',
        string='Set de Medios',
        required=True,
        ondelete='cascade'
    )
    
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
        string='Notas',
        help='Instrucciones específicas para este medio'
    )