from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassEnvironmentWizardV2(models.TransientModel):
    _name = 'lims.mass.environment.wizard.v2'
    _description = 'Asignación Masiva de Ambientes de Procesamiento'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Cuantitativo'),
        ('qualitative', 'Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=True)
    
    environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento', required=True)
    
    specific_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]",
        help='Equipo específico a asignar (solo para campanas)'
    )
    
    override_existing = fields.Boolean(
        string='Sobrescribir Ambientes Existentes',
        default=True
    )
    
    filter_by_result_type = fields.Boolean(
        string='Filtrar por Tipo de Resultado',
        help='Solo aplicar a parámetros cualitativos/cuantitativos'
    )
    
    result_type_filter = fields.Selection([
        ('qualitative', 'Solo Cualitativos'),
        ('quantitative', 'Solo Cuantitativos')
    ], string='Tipo de Resultado')

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('environment')
    def _onchange_environment(self):
        """Limpiar equipo específico si no es campana"""
        if self.environment not in ['campana_flujo', 'campana_bioseguridad']:
            self.specific_equipment_id = False

    @api.onchange('filter_by_result_type')
    def _onchange_filter_by_result_type(self):
        """Limpiar filtro si se desactiva"""
        if not self.filter_by_result_type:
            self.result_type_filter = False

    def action_assign_environment(self):
        """Asignar ambiente a los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        # Filtrar parámetros según criterios
        parameters_to_update = self._filter_parameters()
        
        if not parameters_to_update:
            raise UserError('No hay parámetros que cumplan con los criterios especificados.')
        
        # Mapeo de campos según el tipo de proceso
        field_mapping = {
            'pre_enrichment': ('pre_enrichment_environment', 'pre_enrichment_equipment_id'),
            'selective_enrichment': ('selective_enrichment_environment', 'selective_enrichment_equipment_id'),
            'quantitative': ('quantitative_environment', 'quantitative_equipment_id'),
            'qualitative': ('qualitative_environment', 'qualitative_equipment_id'),
            'confirmation': ('confirmation_environment', 'confirmation_equipment_id'),
        }
        
        environment_field, equipment_field = field_mapping[self.process_type]
        
        # Filtrar parámetros a actualizar
        if not self.override_existing:
            parameters_to_update = parameters_to_update.filtered(
                lambda p: not getattr(p, environment_field)
            )
        
        if not parameters_to_update:
            raise UserError('No hay parámetros disponibles para actualizar. Verifique la opción "Sobrescribir Ambientes Existentes".')
        
        # Preparar valores de actualización
        update_vals = {
            environment_field: self.environment
        }
        
        # Asignar equipo específico si aplica
        if self.environment in ['campana_flujo', 'campana_bioseguridad'] and self.specific_equipment_id:
            update_vals[equipment_field] = self.specific_equipment_id.id
        elif self.environment not in ['campana_flujo', 'campana_bioseguridad']:
            # Limpiar equipo si no es campana
            update_vals[equipment_field] = False
        
        # Actualizar parámetros
        parameters_to_update.write(update_vals)
        
        # Mensaje de confirmación
        environment_name = dict(self._fields["environment"].selection)[self.environment]
        process_name = dict(self._fields["process_type"].selection)[self.process_type]
        
        message = f'Se asignó "{environment_name}" para {process_name} en {len(parameters_to_update)} parámetros.'
        
        if self.specific_equipment_id:
            message += f' Equipo: {self.specific_equipment_id.name}.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ambientes Asignados',
                'message': message,
                'type': 'success',
            }
        }
    
    def _filter_parameters(self):
        """Filtrar parámetros según criterios especificados"""
        parameters = self.parameter_analysis_ids
        
        if self.filter_by_result_type and self.result_type_filter:
            parameters = parameters.filtered(
                lambda p: p.result_type == self.result_type_filter
            )
        
        return parameters