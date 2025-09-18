from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


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

    current_assignments_info = fields.Text(
        string='Asignaciones Actuales',
        compute='_compute_current_assignments_info',
        readonly=True
    )

    parameters_with_analyst_count = fields.Integer(
        string='Ya tienen analista',
        compute='_compute_assignment_summary'
    )

    parameters_without_analyst_count = fields.Integer(
        string='Sin analista',
        compute='_compute_assignment_summary'
    )

    will_override_count = fields.Integer(
        string='Se sobrescribirán',
        compute='_compute_assignment_summary'
    )

    @api.depends('parameter_analysis_ids', 'override_existing')
    def _compute_current_assignments_info(self):
        for record in self:
            if not record.parameter_analysis_ids:
                record.current_assignments_info = "No hay parámetros seleccionados"
                continue
            
            info_lines = []
            for param in record.parameter_analysis_ids:
                current_analyst = param.analyst_id.full_name if param.analyst_id else "Sin asignar"
                info_lines.append(f"• {param.name}: {current_analyst}")
            
            record.current_assignments_info = "\n".join(info_lines)

    @api.depends('parameter_analysis_ids', 'override_existing')
    def _compute_assignment_summary(self):
        for record in self:
            if not record.parameter_analysis_ids:
                record.parameters_with_analyst_count = 0
                record.parameters_without_analyst_count = 0
                record.will_override_count = 0
                continue
            
            with_analyst = record.parameter_analysis_ids.filtered('analyst_id')
            without_analyst = record.parameter_analysis_ids.filtered(lambda p: not p.analyst_id)
            
            record.parameters_with_analyst_count = len(with_analyst)
            record.parameters_without_analyst_count = len(without_analyst)
            record.will_override_count = len(with_analyst) if record.override_existing else 0

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
        
        if not self.analyst_id:
            raise UserError('Debe seleccionar un analista.')
        
        # Verificación PIN usando el sistema existente
        if self.verify_pin:
            if not self.pin_code:
                raise UserError('Debe ingresar el PIN del analista.')
            
            # Usar el método validate_pin del modelo lims.analyst
            if not self.analyst_id.validate_pin(self.pin_code):
                raise UserError('PIN incorrecto para el analista seleccionado.')
            
            _logger.info(f'PIN verificado exitosamente para analista: {self.analyst_id.full_name}')
        
        # Filtrar parámetros según configuración
        parameters_to_update = self.parameter_analysis_ids
        if not self.override_existing:
            parameters_to_update = parameters_to_update.filtered(
                lambda p: not p.analyst_id
            )
        
        if not parameters_to_update:
            raise UserError('No hay parámetros disponibles para actualizar. Verifique la opción "Sobrescribir Asignaciones Existentes".')
        
        # Asignar analista
        parameters_to_update.write({
            'analyst_id': self.analyst_id.id
        })
        
        # Log de auditoría en cada parámetro
        for param in parameters_to_update:
            param.message_post(
                body=f'Analista asignado masivamente: {self.analyst_id.full_name} (Código: {self.analyst_id.employee_code or "N/A"})',
                subject='Asignación Masiva de Analista',
                subtype_xmlid='mail.mt_note'
            )
        
        # Log en el sistema
        _logger.info(f'Asignación masiva completada: {self.analyst_id.full_name} asignado a {len(parameters_to_update)} parámetros')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Analista Asignado con Verificación PIN',
                'message': f'Se asignó {self.analyst_id.full_name} a {len(parameters_to_update)} parámetros con verificación PIN exitosa.',
                'type': 'success',
            }
        }