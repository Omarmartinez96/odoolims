from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassEquipmentWizardV2(models.TransientModel):
    _name = 'lims.mass.equipment.wizard.v2'
    _description = 'Asignación Masiva de Equipos'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    equipment_type = fields.Selection([
        ('processing_equipment', 'Equipos de Procesamiento'),
        ('incubation_equipment', 'Equipos de Incubación'),
        ('additional_equipment', 'Equipos Adicionales')
    ], string='Tipo de Equipo', required=True)
    
    # Para equipos de procesamiento
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Cuantitativo'),
        ('qualitative', 'Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Proceso')
    
    processing_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo de Procesamiento',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]"
    )
    
    # Para equipos de incubación
    incubation_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo de Incubación',
        domain=[('equipment_type', '=', 'incubadora')]
    )
    
    incubation_process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Cuantitativo'),
        ('qualitative', 'Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Proceso de Incubación')
    
    # Para equipos adicionales
    additional_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Adicional'
    )
    
    equipment_usage = fields.Char(
        string='Uso del Equipo',
        placeholder='Ej: Pesado de muestra, Medición de pH, etc.'
    )
    
    usage_date = fields.Date(
        string='Fecha de Uso',
        default=fields.Date.context_today
    )
    
    used_by_name = fields.Char(
        string='Utilizado por',
        default=lambda self: self.env.user.name
    )
    
    override_existing = fields.Boolean(
        string='Sobrescribir Equipos Existentes',
        default=False
    )

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('equipment_type')
    def _onchange_equipment_type(self):
        """Limpiar campos según tipo seleccionado"""
        if self.equipment_type != 'processing_equipment':
            self.process_type = False
            self.processing_equipment_id = False
        if self.equipment_type != 'incubation_equipment':
            self.incubation_equipment_id = False
            self.incubation_process_type = False
        if self.equipment_type != 'additional_equipment':
            self.additional_equipment_id = False
            self.equipment_usage = False

    def action_assign_equipment(self):
        """Asignar equipos a los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        if self.equipment_type == 'processing_equipment':
            return self._assign_processing_equipment()
        elif self.equipment_type == 'incubation_equipment':
            return self._assign_incubation_equipment()
        elif self.equipment_type == 'additional_equipment':
            return self._assign_additional_equipment()
    
    def _assign_processing_equipment(self):
        """Asignar equipos de procesamiento"""
        if not self.process_type or not self.processing_equipment_id:
            raise UserError('Debe especificar el proceso y el equipo.')
        
        field_mapping = {
            'pre_enrichment': 'pre_enrichment_equipment_id',
            'selective_enrichment': 'selective_enrichment_equipment_id',
            'quantitative': 'quantitative_equipment_id',
            'qualitative': 'qualitative_equipment_id',
            'confirmation': 'confirmation_equipment_id',
        }
        
        equipment_field = field_mapping[self.process_type]
        
        parameters_to_update = self.parameter_analysis_ids
        if not self.override_existing:
            parameters_to_update = parameters_to_update.filtered(
                lambda p: not getattr(p, equipment_field)
            )
        
        if parameters_to_update:
            parameters_to_update.write({
                equipment_field: self.processing_equipment_id.id
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Equipos de Procesamiento Asignados',
                'message': f'Se asignó {self.processing_equipment_id.name} a {len(parameters_to_update)} parámetros.',
                'type': 'success',
            }
        }
    
    def _assign_incubation_equipment(self):
        """Asignar equipos de incubación a medios"""
        if not self.incubation_process_type or not self.incubation_equipment_id:
            raise UserError('Debe especificar el proceso y el equipo de incubación.')
        
        updated_media = 0
        for parameter in self.parameter_analysis_ids:
            media_to_update = parameter.media_ids.filtered(
                lambda m: m.process_type == self.incubation_process_type and m.requires_incubation
            )
            
            if not self.override_existing:
                media_to_update = media_to_update.filtered(
                    lambda m: not m.incubation_equipment
                )
            
            if media_to_update:
                media_to_update.write({
                    'incubation_equipment': self.incubation_equipment_id.id
                })
                updated_media += len(media_to_update)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Equipos de Incubación Asignados',
                'message': f'Se asignó {self.incubation_equipment_id.name} a {updated_media} medios.',
                'type': 'success',
            }
        }
    
    def _assign_additional_equipment(self):
        """Asignar equipos adicionales"""
        if not self.additional_equipment_id or not self.equipment_usage:
            raise UserError('Debe especificar el equipo y su uso.')
        
        total_created = 0
        for parameter in self.parameter_analysis_ids:
            # Verificar si ya existe este equipo para este parámetro
            existing = parameter.equipment_involved_ids.filtered(
                lambda e: e.equipment_id.id == self.additional_equipment_id.id
            )
            
            if not existing or self.override_existing:
                if existing and self.override_existing:
                    existing.unlink()
                
                self.env['lims.equipment.involved.v2'].create({
                    'parameter_analysis_id': parameter.id,
                    'equipment_id': self.additional_equipment_id.id,
                    'usage': self.equipment_usage,
                    'usage_date': self.usage_date,
                    'used_by_name': self.used_by_name,
                })
                total_created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Equipos Adicionales Asignados',
                'message': f'Se asignó {self.additional_equipment_id.name} a {total_created} parámetros.',
                'type': 'success',
            }
        }