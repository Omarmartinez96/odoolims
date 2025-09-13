from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class LimsLabEquipmentInherited(models.Model):
    _inherit = 'lims.lab.equipment'
    
    # === CAMPOS RELACIONADOS CON BITÁCORA ===
    usage_log_ids = fields.One2many(
        'lims.equipment.usage.log',
        'equipment_id',
        string='Historial de Uso'
    )
    
    usage_log_count = fields.Integer(
        string='Total de Usos',
        compute='_compute_usage_stats'
    )
    
    current_usage_id = fields.Many2one(
        'lims.equipment.usage.log',
        string='Uso Actual',
        compute='_compute_current_usage'
    )
    
    is_currently_in_use = fields.Boolean(
        string='En Uso Actualmente',
        compute='_compute_current_usage'
    )
    
    total_usage_hours = fields.Float(
        string='Total Horas de Uso',
        compute='_compute_usage_stats'
    )
    
    @api.depends('usage_log_ids')
    def _compute_usage_stats(self):
        for equipment in self:
            logs = equipment.usage_log_ids
            equipment.usage_log_count = len(logs)
            equipment.total_usage_hours = sum(logs.mapped('duration_hours'))
    
    @api.depends('usage_log_ids.is_active_use')
    def _compute_current_usage(self):
        for equipment in self:
            current_usage = equipment.usage_log_ids.filtered('is_active_use')
            if current_usage:
                equipment.current_usage_id = current_usage[0]
                equipment.is_currently_in_use = True
            else:
                equipment.current_usage_id = False
                equipment.is_currently_in_use = False
    
    def action_sync_equipment_historical_usage(self):
        """Sincronizar uso histórico de este equipo específico"""
        
        # Buscar todos los medios que han usado este equipo
        historical_media = self.env['lims.analysis.media.v2'].search([
            ('incubation_equipment', '=', self.id),
            ('incubation_start_date', '!=', False)
        ])
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for media in historical_media:
            # Verificar si ya existe registro
            existing_log = self.env['lims.equipment.usage.log'].search([
                ('equipment_id', '=', self.id),
                ('related_media_id', '=', media.id)
            ])
            
            if existing_log:
                # Actualizar si es necesario
                updates = {}
                if media.incubation_end_date_real and not existing_log.end_datetime:
                    end_datetime = self._combine_date_time(
                        media.incubation_end_date_real,
                        media.incubation_end_time_real or '23:59'
                    )
                    updates['end_datetime'] = end_datetime
                
                if updates:
                    existing_log.write(updates)
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Crear nuevo registro
                start_datetime = self._combine_date_time(
                    media.incubation_start_date,
                    media.incubation_start_time or '00:00'
                )
                
                end_datetime = False
                if media.incubation_end_date_real:
                    end_datetime = self._combine_date_time(
                        media.incubation_end_date_real,
                        media.incubation_end_time_real or '23:59'
                    )
                
                planned_end_datetime = False
                if media.incubation_end_date:
                    planned_end_datetime = self._combine_date_time(
                        media.incubation_end_date,
                        media.incubation_end_time or '23:59'
                    )
                
                self.env['lims.equipment.usage.log'].create({
                    'equipment_id': self.id,
                    'usage_type': 'incubation',
                    'process_context': media.process_type,
                    'related_analysis_id': media.parameter_analysis_id.analysis_id.id,
                    'related_parameter_id': media.parameter_analysis_id.id,
                    'related_media_id': media.id,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                    'planned_end_datetime': planned_end_datetime,
                    'used_by_name': 'Sistema (Histórico)',
                    'usage_notes': f"Sincronización histórica - {media.culture_media_name or 'Medio'}",
                    'is_historical': True
                })
                created_count += 1
        
        # También sincronizar equipos involucrados (no incubación)
        equipment_involved = self.env['lims.equipment.involved.v2'].search([
            ('equipment_id', '=', self.id),
            ('usage_date', '!=', False)
        ])
        
        for equipment_use in equipment_involved:
            # Verificar si ya existe
            existing_log = self.env['lims.equipment.usage.log'].search([
                ('equipment_id', '=', self.id),
                ('related_parameter_id', '=', equipment_use.parameter_analysis_id.id),
                ('usage_type', '=', 'other'),
                ('start_datetime', '=', self._combine_date_time(
                    equipment_use.usage_date,
                    equipment_use.usage_time or '12:00'
                ))
            ])
            
            if not existing_log:
                self.env['lims.equipment.usage.log'].create({
                    'equipment_id': self.id,
                    'usage_type': 'other',
                    'related_analysis_id': equipment_use.parameter_analysis_id.analysis_id.id,
                    'related_parameter_id': equipment_use.parameter_analysis_id.id,
                    'start_datetime': self._combine_date_time(
                        equipment_use.usage_date,
                        equipment_use.usage_time or '12:00'
                    ),
                    'used_by_name': equipment_use.used_by_name or 'Usuario',
                    'usage_notes': f"Uso: {equipment_use.usage} - {equipment_use.notes or ''}",
                    'is_historical': True
                })
                created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'Sincronización de {self.name}',
                'message': f'✅ {created_count} nuevos, 🔄 {updated_count} actualizados, ⏭️ {skipped_count} omitidos',
                'type': 'success'
            }
        }
    
    def _combine_date_time(self, date_field, time_field):
        """Combinar fecha y hora en datetime"""
        if not date_field:
            return False
        
        if not time_field:
            time_field = '12:00'
        
        try:
            # Parsear tiempo HH:MM
            time_parts = time_field.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Combinar fecha y hora
            combined = datetime.combine(
                date_field,
                datetime.min.time().replace(hour=hour, minute=minute)
            )
            
            return combined
        except:
            # Si hay error, usar mediodía como default
            return datetime.combine(date_field, datetime.min.time().replace(hour=12))
    
    def action_view_usage_log(self):
        """Ver bitácora de uso de este equipo"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Bitácora de Uso - {self.name}',
            'res_model': 'lims.equipment.usage.log',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id}
        }