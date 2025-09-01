from odoo import models, fields, api

class LimsQcTemplate(models.Model):
    _name = 'lims.qc.template'
    _description = 'Plantillas de Controles de Calidad'
    _order = 'name'

    name = fields.Char(
        string='Nombre de la Plantilla',
        required=True,
        help='Ej: Controles Salmonella, Controles Aerobios Mesófilos'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción de cuándo usar esta plantilla'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Líneas de controles
    control_line_ids = fields.One2many(
        'lims.qc.template.line',
        'template_id',
        string='Controles de la Plantilla'
    )
    
    times_used = fields.Integer(
        string='Veces Utilizado',
        default=0,
        readonly=True
    )


class LimsQcTemplateLine(models.Model):
    _name = 'lims.qc.template.line'
    _description = 'Líneas de Plantillas de QC'
    _order = 'sequence'

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    template_id = fields.Many2one(
        'lims.qc.template',
        string='Plantilla QC',
        required=True,
        ondelete='cascade'
    )
    
    qc_type_id = fields.Many2one(
        'lims.quality.control.type',
        string='Tipo de Control',
        required=True
    )
    
    expected_result = fields.Char(
        string='Resultado Esperado',
        required=True
    )
    
    notes = fields.Text(
        string='Notas',
        help='Instrucciones específicas para este control'
    )