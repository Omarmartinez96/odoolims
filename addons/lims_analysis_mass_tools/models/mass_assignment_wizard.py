from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassAssignmentWizardV2(models.TransientModel):
    _name = 'lims.mass.assignment.wizard.v2'
    _description = 'Wizard de Asignación Masiva v2'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    assignment_type = fields.Selection([
        ('analyst', '👤 Asignar Analista Responsable'),
        ('dates', '📅 Asignar Fechas de Procesamiento'),
        ('media', '🧪 Asignar Medios de Cultivo'),
        ('equipment', '🔧 Asignar Equipos'),
        ('status', '📊 Cambiar Estados'),
        ('environment', '🏭 Asignar Ambientes de Procesamiento'),
    ], string='Tipo de Asignación', required=True)

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    def action_open_specific_wizard(self):
        """Abrir el wizard específico según el tipo seleccionado"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        wizard_mapping = {
            'analyst': 'lims.mass.analyst.wizard.v2',
            'dates': 'lims.mass.dates.wizard.v2', 
            'media': 'lims.mass.media.wizard.v2',
            'equipment': 'lims.mass.equipment.wizard.v2',
            'status': 'lims.mass.status.wizard.v2',
            'environment': 'lims.mass.environment.wizard.v2',
        }
        
        wizard_model = wizard_mapping.get(self.assignment_type)
        wizard_name = dict(self._fields["assignment_type"].selection)[self.assignment_type]
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Asignación Masiva - {wizard_name}',
            'res_model': wizard_model,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parameter_analysis_ids': [(6, 0, self.parameter_analysis_ids.ids)]
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer parámetros desde contexto"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            defaults['parameter_analysis_ids'] = [(6, 0, active_ids)]
        
        return defaults