from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassAnalystWizardV2(models.TransientModel):
    _name = 'lims.mass.analyst.wizard.v2'
    _description = 'Asignación Masiva de Analista'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Analista a Asignar',
        required=True
    )
    
    verify_pin = fields.Boolean(
        string='Verificar PIN del Analista',
        default=True,
        help='Requiere verificación PIN para asegurar que el analista autoriza la asignación'
    )
    
    pin_code = fields.Char(
        string='PIN de Verificación',
        help='PIN del analista para verificar autorización'
    )
    
    override_existing = fields.Boolean(
        string='Sobrescribir Analistas Existentes',
        default=True,
        help='Si está marcado, reemplazará analistas ya asignados'
    )

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('verify_pin')
    def _onchange_verify_pin(self):
        """Limpiar PIN cuando se desactiva verificación"""
        if not self.verify_pin:
            self.pin_code = False

    def action_assign_analyst(self):
        """Asignar analista a todos los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        # Verificar PIN si está habilitado
        if self.verify_pin:
            if not self.pin_code:
                raise UserError('Debe ingresar el PIN de verificación.')
            
            if not self.analyst_id.verify_pin(self.pin_code):
                raise UserError('PIN incorrecto para el analista seleccionado.')
        
        # Filtrar parámetros a actualizar
        parameters_to_update = self.parameter_analysis_ids
        if not self.override_existing:
            parameters_to_update = self.parameter_analysis_ids.filtered(
                lambda p: not p.analyst_id
            )
        
        if not parameters_to_update:
            raise UserError('No hay parámetros disponibles para actualizar. Verifique la opción "Sobrescribir Analistas Existentes".')
        
        # Asignar analista
        parameters_to_update.write({
            'analyst_id': self.analyst_id.id,
            'analyst_names': self.analyst_id.initials or self.analyst_id.full_name
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Analista Asignado',
                'message': f'Se asignó {self.analyst_id.full_name} a {len(parameters_to_update)} parámetros.',
                'type': 'success',
            }
        }