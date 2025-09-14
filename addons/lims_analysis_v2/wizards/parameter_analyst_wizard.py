from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class ParameterAnalystAssignmentWizard(models.TransientModel):
    _name = 'parameter.analyst.assignment.wizard'
    _description = 'Wizard para Asignar Múltiples Analistas a Parámetro'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis.v2',
        string='Parámetro de Análisis',
        required=True
    )
    
    current_analyst_ids = fields.Many2many(
        'lims.analyst',
        'param_current_analyst_rel',
        string='Analistas Actuales',
        readonly=True
    )
    
    analyst_to_add_id = fields.Many2one(
        'lims.analyst',
        string='Seleccionar Analista para Agregar',
        domain=[('active', '=', True), ('pin_hash', '!=', False)],
        help='Solo analistas activos con PIN configurado'
    )
    
    pin_input = fields.Char(
        string='PIN de Verificación',
        help='PIN del analista seleccionado'
    )
    
    analyst_to_remove_id = fields.Many2one(
        'lims.analyst',
        string='Analista a Remover',
        help='Seleccionar analista para remover de la lista'
    )

    def action_add_analyst(self):
        """Agregar analista tras verificar PIN"""
        self.ensure_one()
        
        if not self.analyst_to_add_id:
            raise UserError('Debe seleccionar un analista.')
        
        if not self.pin_input:
            raise UserError('Debe ingresar el PIN del analista.')
        
        # Verificar PIN
        if not self.analyst_to_add_id.validate_pin(self.pin_input):
            raise ValidationError('PIN incorrecto. Verifique e intente nuevamente.')
        
        # Verificar que no esté ya asignado
        if self.analyst_to_add_id.id in self.parameter_analysis_id.analyst_ids.ids:
            raise UserError(f'{self.analyst_to_add_id.full_name} ya está asignado a este parámetro.')
        
        # Agregar analista
        self.parameter_analysis_id.write({
            'analyst_ids': [(4, self.analyst_to_add_id.id)]
        })
        
        # Limpiar campos
        self.write({
            'analyst_to_add_id': False,
            'pin_input': False,
            'current_analyst_ids': [(6, 0, self.parameter_analysis_id.analyst_ids.ids)]
        })
        
        # Mantener wizard abierto para agregar más analistas
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'parameter.analyst.assignment.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }

    def action_remove_analyst(self):
        """Remover analista sin verificación PIN"""
        self.ensure_one()
        
        if not self.analyst_to_remove_id:
            raise UserError('Debe seleccionar un analista para remover.')
        
        # Remover analista
        self.parameter_analysis_id.write({
            'analyst_ids': [(3, self.analyst_to_remove_id.id)]
        })
        
        # Actualizar lista actual
        self.write({
            'analyst_to_remove_id': False,
            'current_analyst_ids': [(6, 0, self.parameter_analysis_id.analyst_ids.ids)]
        })
        
        # Mantener wizard abierto
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'parameter.analyst.assignment.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }

    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto"""
        defaults = super().default_get(fields_list)
        
        if self.env.context.get('default_parameter_analysis_id'):
            parameter = self.env['lims.parameter.analysis.v2'].browse(
                self.env.context['default_parameter_analysis_id']
            )
            if parameter.exists():
                defaults.update({
                    'parameter_analysis_id': parameter.id,
                    'current_analyst_ids': [(6, 0, parameter.analyst_ids.ids)]
                })
        
        return defaults