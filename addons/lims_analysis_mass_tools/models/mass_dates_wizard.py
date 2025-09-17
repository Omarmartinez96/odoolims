from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassDateWizardV2(models.TransientModel):
    _name = 'lims.mass.dates.wizard.v2'
    _description = 'Asignación Masiva de Fechas'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    date_type = fields.Selection([
        ('analysis_dates', 'Fechas de Análisis General'),
        ('process_dates', 'Fechas de Procesos Específicos'),
    ], string='Tipo de Fechas', required=True)
    
    # Fechas generales
    analysis_start_date = fields.Date(
        string='Fecha de Inicio de Análisis'
    )
    analysis_commitment_date = fields.Date(
        string='Fecha Compromiso de Análisis'
    )
    
    # Fechas por proceso
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Cuantitativo'),
        ('qualitative', 'Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Proceso')
    
    processing_date = fields.Date(
        string='Fecha de Procesamiento'
    )
    processing_time = fields.Char(
        string='Hora de Procesamiento',
        placeholder='HH:MM'
    )
    
    override_existing = fields.Boolean(
        string='Sobrescribir Fechas Existentes',
        default=True
    )

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('date_type')
    def _onchange_date_type(self):
        """Limpiar campos según tipo seleccionado"""
        if self.date_type != 'analysis_dates':
            self.analysis_start_date = False
            self.analysis_commitment_date = False
        if self.date_type != 'process_dates':
            self.process_type = False
            self.processing_date = False
            self.processing_time = False

    def action_assign_dates(self):
        """Asignar fechas a los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        if self.date_type == 'analysis_dates':
            return self._assign_analysis_dates()
        elif self.date_type == 'process_dates':
            return self._assign_process_dates()
    
    def _assign_analysis_dates(self):
        """Asignar fechas generales de análisis"""
        if not self.analysis_start_date and not self.analysis_commitment_date:
            raise UserError('Debe especificar al menos una fecha de análisis.')
        
        update_vals = {}
        if self.analysis_start_date:
            update_vals['analysis_start_date'] = self.analysis_start_date
        if self.analysis_commitment_date:
            update_vals['analysis_commitment_date'] = self.analysis_commitment_date
        
        parameters_to_update = self.parameter_analysis_ids
        
        if not self.override_existing:
            # Filtrar parámetros que no tengan las fechas ya establecidas
            if self.analysis_start_date:
                parameters_to_update = parameters_to_update.filtered(
                    lambda p: not p.analysis_start_date
                )
            if self.analysis_commitment_date:
                parameters_to_update = parameters_to_update.filtered(
                    lambda p: not p.analysis_commitment_date
                )
        
        if parameters_to_update:
            parameters_to_update.write(update_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Fechas Asignadas',
                'message': f'Se actualizaron las fechas en {len(parameters_to_update)} parámetros.',
                'type': 'success',
            }
        }
    
    def _assign_process_dates(self):
        """Asignar fechas de procesos específicos"""
        if not self.process_type or not self.processing_date:
            raise UserError('Debe especificar el tipo de proceso y la fecha.')
        
        field_mapping = {
            'pre_enrichment': ('pre_enrichment_processing_date', 'pre_enrichment_processing_time'),
            'selective_enrichment': ('selective_enrichment_processing_date', 'selective_enrichment_processing_time'),
            'quantitative': ('quantitative_processing_date', 'quantitative_processing_time'),
            'qualitative': ('qualitative_processing_date', 'qualitative_processing_time'),
            'confirmation': ('confirmation_processing_date', 'confirmation_processing_time'),
        }
        
        date_field, time_field = field_mapping[self.process_type]
        
        update_vals = {
            date_field: self.processing_date
        }
        
        if self.processing_time:
            update_vals[time_field] = self.processing_time
        
        parameters_to_update = self.parameter_analysis_ids
        
        if not self.override_existing:
            # Filtrar parámetros que no tengan la fecha ya establecida
            parameters_to_update = parameters_to_update.filtered(
                lambda p: not getattr(p, date_field)
            )
        
        if parameters_to_update:
            parameters_to_update.write(update_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Fechas de Proceso Asignadas',
                'message': f'Se actualizaron las fechas de {self.process_type} en {len(parameters_to_update)} parámetros.',
                'type': 'success',
            }
        }