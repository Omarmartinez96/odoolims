from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassStatusWizardV2(models.TransientModel):
    _name = 'lims.mass.status.wizard.v2'
    _description = 'Cambio Masivo de Estados'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    status_type = fields.Selection([
        ('analysis_status', 'Estado de Análisis'),
        ('report_status', 'Estado de Reporte'),
        ('process_requirements', 'Configuración de Procesos Requeridos')
    ], string='Tipo de Estado', required=True)
    
    # Estados de análisis
    new_analysis_status = fields.Selection([
        ('sin_procesar', 'Sin Procesar'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ], string='Nuevo Estado de Análisis')
    
    # Estados de reporte
    new_report_status = fields.Selection([
        ('draft', 'En Proceso'),
        ('ready', 'Listo para Reporte'),
    ], string='Nuevo Estado de Reporte')
    
    # Configuración de procesos
    requires_pre_enrichment = fields.Boolean(
        string='Requiere Pre-enriquecimiento'
    )
    requires_selective_enrichment = fields.Boolean(
        string='Requiere Enriquecimiento Selectivo'
    )
    requires_confirmation = fields.Boolean(
        string='Requiere Confirmación'
    )
    requires_ph_adjustment = fields.Boolean(
        string='Requiere Ajuste de pH'
    )
    
    # Opciones de aplicación
    apply_to_filter = fields.Selection([
        ('all_selected', 'Todos los Parámetros Seleccionados'),
        ('by_current_status', 'Solo Parámetros con Estado Específico'),
        ('by_result_type', 'Solo Parámetros por Tipo de Resultado')
    ], string='Aplicar a', default='all_selected', required=True)
    
    current_status_filter = fields.Selection([
        ('sin_procesar', 'Sin Procesar'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ], string='Estado Actual a Filtrar')
    
    result_type_filter = fields.Selection([
        ('qualitative', 'Cualitativo'),
        ('quantitative', 'Cuantitativo')
    ], string='Tipo de Resultado a Filtrar')

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('status_type')
    def _onchange_status_type(self):
        """Limpiar campos según tipo seleccionado"""
        if self.status_type != 'analysis_status':
            self.new_analysis_status = False
        if self.status_type != 'report_status':
            self.new_report_status = False
        if self.status_type != 'process_requirements':
            self.requires_pre_enrichment = False
            self.requires_selective_enrichment = False
            self.requires_confirmation = False
            self.requires_ph_adjustment = False

    @api.onchange('apply_to_filter')
    def _onchange_apply_to_filter(self):
        """Limpiar filtros según opción seleccionada"""
        if self.apply_to_filter != 'by_current_status':
            self.current_status_filter = False
        if self.apply_to_filter != 'by_result_type':
            self.result_type_filter = False

    def action_change_status(self):
        """Cambiar estados en los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        # Filtrar parámetros según criterios
        parameters_to_update = self._filter_parameters()
        
        if not parameters_to_update:
            raise UserError('No hay parámetros que cumplan con los criterios especificados.')
        
        if self.status_type == 'analysis_status':
            return self._change_analysis_status(parameters_to_update)
        elif self.status_type == 'report_status':
            return self._change_report_status(parameters_to_update)
        elif self.status_type == 'process_requirements':
            return self._change_process_requirements(parameters_to_update)
    
    def _filter_parameters(self):
        """Filtrar parámetros según criterios especificados"""
        parameters = self.parameter_analysis_ids
        
        if self.apply_to_filter == 'by_current_status':
            if self.current_status_filter:
                parameters = parameters.filtered(
                    lambda p: p.analysis_status_checkbox == self.current_status_filter
                )
        elif self.apply_to_filter == 'by_result_type':
            if self.result_type_filter:
                parameters = parameters.filtered(
                    lambda p: p.result_type == self.result_type_filter
                )
        
        return parameters
    
    def _change_analysis_status(self, parameters):
        """Cambiar estado de análisis"""
        if not self.new_analysis_status:
            raise UserError('Debe especificar el nuevo estado de análisis.')
        
        parameters.write({
            'analysis_status_checkbox': self.new_analysis_status
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Estados de Análisis Actualizados',
                'message': f'Se cambió el estado a "{dict(self._fields["new_analysis_status"].selection)[self.new_analysis_status]}" en {len(parameters)} parámetros.',
                'type': 'success',
            }
        }
    
    def _change_report_status(self, parameters):
        """Cambiar estado de reporte"""
        if not self.new_report_status:
            raise UserError('Debe especificar el nuevo estado de reporte.')
        
        parameters.write({
            'report_status': self.new_report_status
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Estados de Reporte Actualizados',
                'message': f'Se cambió el estado a "{dict(self._fields["new_report_status"].selection)[self.new_report_status]}" en {len(parameters)} parámetros.',
                'type': 'success',
            }
        }
    
    def _change_process_requirements(self, parameters):
        """Cambiar configuración de procesos requeridos"""
        update_vals = {
            'requires_pre_enrichment': self.requires_pre_enrichment,
            'requires_selective_enrichment': self.requires_selective_enrichment,
            'requires_confirmation': self.requires_confirmation,
            'requires_ph_adjustment': self.requires_ph_adjustment,
        }
        
        parameters.write(update_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Configuración de Procesos Actualizada',
                'message': f'Se actualizó la configuración de procesos en {len(parameters)} parámetros.',
                'type': 'success',
            }
        }