# lims_quality_control.py
from odoo import models, fields, api

class LimsQualityControlType(models.Model):
    _name = 'lims.quality.control.type'
    _description = 'Tipos de Control de Calidad'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre del Control',
        required=True,
        translate=True,
        help='Ej: Esterilidad de ronda de muestras'
    )
    
    description = fields.Text(
        string='Descripción',
        translate=True
    )
    
    default_expected_result = fields.Char(
        string='Resultado Esperado por Defecto',
        help='Ej: Estéril, Positivo, Negativo'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    category = fields.Selection([
        ('sterility', 'Esterilidad'),
        ('positive_control', 'Control Positivo'),
        ('negative_control', 'Control Negativo'),
        ('blank', 'Blanco'),
        ('duplicate', 'Duplicado'),
        ('spike', 'Spike/Adición'),
        ('other', 'Otro')
    ], string='Categoría')


class LimsQualityControl(models.Model):
    _name = 'lims.quality.control'
    _description = 'Controles de Calidad'
    _order = 'sequence, control_type_id'

    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro',
        required=True,
        ondelete='cascade'
    )
    
    control_type_id = fields.Many2one(
        'lims.quality.control.type',
        string='Tipo de Control',
        required=True
    )
    
    expected_result = fields.Char(
        string='Debe ser',
        required=True,
        help='Resultado esperado para este control'
    )
    
    sequence = fields.Integer(
        string='Orden',
        default=10
    )
    
    notes = fields.Text(
        string='Notas Adicionales'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    @api.onchange('control_type_id')
    def _onchange_control_type_id(self):
        if self.control_type_id and self.control_type_id.default_expected_result:
            self.expected_result = self.control_type_id.default_expected_result

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.control_type_id.name}: {record.expected_result}"
            result.append((record.id, name))
        return result