from odoo import models, fields

class LimsFieldResult(models.Model):
    _name = 'lims.field.result'
    _description = 'Resultados de Campo'
    _order = 'sequence, id'

    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de los campos'
    )
    
    parameter_name = fields.Char(
        string='Parámetro',
        required=True,
        placeholder='Ej: pH, Temperatura, Cloro residual'
    )
    
    result_value = fields.Char(
        string='Resultado',
        placeholder='Ej: 7.2, 25°C, 0.5 mg/L'
    )
    
    unit = fields.Char(
        string='Unidad',
        placeholder='Ej: pH, °C, mg/L'
    )
    
    notes = fields.Text(
        string='Notas',
        placeholder='Observaciones adicionales...'
    )