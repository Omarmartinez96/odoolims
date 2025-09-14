from odoo import models, fields, api
from odoo.exceptions import UserError
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
        """Sincronizar uso histórico con timezone correcto - TODOS los tipos"""
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # ===== 1. EQUIPOS DE INCUBACIÓN =====
        historical_media = self.env['lims.analysis.media.v2'].search([
            ('incubation_equipment', '=', self.id),
            ('incubation_start_date', '!=', False)
        ])
        
        _logger.info(f"Sincronizando {len(historical_media)} registros de medios para equipo {self.name}")
        
        for media in historical_media:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_media_id', '=', media.id),
                    ('usage_type', '=', 'incubation')
                ])
                
                if existing_log:
                    # RECALCULAR horarios existentes con timezone correcto
                    updates = {}
                    
                    if media.incubation_start_date:
                        start_datetime = self._combine_date_time_to_utc(
                            media.incubation_start_date,
                            media.incubation_start_time or '00:00'
                        )
                        updates['start_datetime'] = start_datetime
                    
                    if media.incubation_end_date:
                        planned_end_datetime = self._combine_date_time_to_utc(
                            media.incubation_end_date,
                            media.incubation_end_time or '23:59'
                        )
                        updates['planned_end_datetime'] = planned_end_datetime
                    
                    if media.incubation_end_date_real:
                        end_datetime = self._combine_date_time_to_utc(
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
                    # Crear nuevo registro con timezone correcto
                    start_datetime = self._combine_date_time_to_utc(
                        media.incubation_start_date,
                        media.incubation_start_time or '00:00'
                    )
                    
                    planned_end_datetime = False
                    if media.incubation_end_date:
                        planned_end_datetime = self._combine_date_time_to_utc(
                            media.incubation_end_date,
                            media.incubation_end_time or '23:59'
                        )
                    
                    end_datetime = False
                    if media.incubation_end_date_real:
                        end_datetime = self._combine_date_time_to_utc(
                            media.incubation_end_date_real,
                            media.incubation_end_time_real or '23:59'
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
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Incubación - {media.culture_media_name or 'Medio'}",
                        'is_historical': True
                    })
                    created_count += 1
                    
            except Exception as e:
                _logger.error(f"Error procesando medio ID {media.id}: {e}")
                error_count += 1
                continue
        
        # ===== 2. EQUIPOS DE AMBIENTES DE PROCESAMIENTO =====
        
        # Pre-enriquecimiento
        pre_enrichment_params = self.env['lims.parameter.analysis.v2'].search([
            ('pre_enrichment_equipment_id', '=', self.id),
            ('pre_enrichment_processing_date', '!=', False)
        ])
        
        for param in pre_enrichment_params:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', param.id),
                    ('process_context', '=', 'pre_enrichment')
                ])
                
                if not existing_log:
                    start_datetime = self._combine_date_time_to_utc(
                        param.pre_enrichment_processing_date,
                        param.pre_enrichment_processing_time or '12:00'
                    )
                    
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'processing',
                        'process_context': 'pre_enrichment',
                        'related_analysis_id': param.analysis_id.id,
                        'related_parameter_id': param.id,
                        'start_datetime': start_datetime,
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Procesamiento Pre-enriquecimiento - {param.name}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando pre-enriquecimiento param ID {param.id}: {e}")
                error_count += 1
                continue
        
        # Enriquecimiento Selectivo
        selective_params = self.env['lims.parameter.analysis.v2'].search([
            ('selective_enrichment_equipment_id', '=', self.id),
            ('selective_enrichment_processing_date', '!=', False)
        ])
        
        for param in selective_params:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', param.id),
                    ('process_context', '=', 'selective_enrichment')
                ])
                
                if not existing_log:
                    start_datetime = self._combine_date_time_to_utc(
                        param.selective_enrichment_processing_date,
                        param.selective_enrichment_processing_time or '12:00'
                    )
                    
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'processing',
                        'process_context': 'selective_enrichment',
                        'related_analysis_id': param.analysis_id.id,
                        'related_parameter_id': param.id,
                        'start_datetime': start_datetime,
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Procesamiento Selectivo - {param.name}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando enriquecimiento selectivo param ID {param.id}: {e}")
                error_count += 1
                continue
        
        # Cuantitativo
        quantitative_params = self.env['lims.parameter.analysis.v2'].search([
            ('quantitative_equipment_id', '=', self.id),
            ('quantitative_processing_date', '!=', False)
        ])
        
        for param in quantitative_params:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', param.id),
                    ('process_context', '=', 'quantitative')
                ])
                
                if not existing_log:
                    start_datetime = self._combine_date_time_to_utc(
                        param.quantitative_processing_date,
                        param.quantitative_processing_time or '12:00'
                    )
                    
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'processing',
                        'process_context': 'quantitative',
                        'related_analysis_id': param.analysis_id.id,
                        'related_parameter_id': param.id,
                        'start_datetime': start_datetime,
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Procesamiento Cuantitativo - {param.name}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando cuantitativo param ID {param.id}: {e}")
                error_count += 1
                continue
        
        # Cualitativo
        qualitative_params = self.env['lims.parameter.analysis.v2'].search([
            ('qualitative_equipment_id', '=', self.id),
            ('qualitative_processing_date', '!=', False)
        ])
        
        for param in qualitative_params:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', param.id),
                    ('process_context', '=', 'qualitative')
                ])
                
                if not existing_log:
                    start_datetime = self._combine_date_time_to_utc(
                        param.qualitative_processing_date,
                        param.qualitative_processing_time or '12:00'
                    )
                    
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'processing',
                        'process_context': 'qualitative',
                        'related_analysis_id': param.analysis_id.id,
                        'related_parameter_id': param.id,
                        'start_datetime': start_datetime,
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Procesamiento Cualitativo - {param.name}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando cualitativo param ID {param.id}: {e}")
                error_count += 1
                continue
        
        # Confirmación
        confirmation_params = self.env['lims.parameter.analysis.v2'].search([
            ('confirmation_equipment_id', '=', self.id),
            ('confirmation_processing_date', '!=', False)
        ])
        
        for param in confirmation_params:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', param.id),
                    ('process_context', '=', 'confirmation')
                ])
                
                if not existing_log:
                    start_datetime = self._combine_date_time_to_utc(
                        param.confirmation_processing_date,
                        param.confirmation_processing_time or '12:00'
                    )
                    
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'processing',
                        'process_context': 'confirmation',
                        'related_analysis_id': param.analysis_id.id,
                        'related_parameter_id': param.id,
                        'start_datetime': start_datetime,
                        'used_by_name': 'Sistema (Sincronizado)',
                        'usage_notes': f"Procesamiento Confirmación - {param.name}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando confirmación param ID {param.id}: {e}")
                error_count += 1
                continue
        
        # ===== 3. EQUIPOS INVOLUCRADOS ADICIONALES =====
        equipment_involved = self.env['lims.equipment.involved.v2'].search([
            ('equipment_id', '=', self.id),
            ('usage_date', '!=', False)
        ])
        
        for equipment_use in equipment_involved:
            try:
                existing_log = self.env['lims.equipment.usage.log'].search([
                    ('equipment_id', '=', self.id),
                    ('related_parameter_id', '=', equipment_use.parameter_analysis_id.id),
                    ('usage_type', '=', 'other'),
                    ('start_datetime', '=', self._combine_date_time_to_utc(
                        equipment_use.usage_date,
                        equipment_use.usage_time or '12:00'
                    ))
                ])
                
                if not existing_log:
                    self.env['lims.equipment.usage.log'].create({
                        'equipment_id': self.id,
                        'usage_type': 'other',
                        'process_context': 'other',
                        'related_analysis_id': equipment_use.parameter_analysis_id.analysis_id.id,
                        'related_parameter_id': equipment_use.parameter_analysis_id.id,
                        'start_datetime': self._combine_date_time_to_utc(
                            equipment_use.usage_date,
                            equipment_use.usage_time or '12:00'
                        ),
                        'used_by_name': equipment_use.used_by_name or 'Usuario',
                        'usage_notes': f"Uso: {equipment_use.usage} - {equipment_use.notes or ''}",
                        'is_historical': True
                    })
                    created_count += 1
            except Exception as e:
                _logger.error(f"Error procesando equipo involucrado ID {equipment_use.id}: {e}")
                error_count += 1
                continue
        
        message = f'✅ {created_count} nuevos, 🔄 {updated_count} recalculados, ⏭️ {skipped_count} omitidos'
        if error_count > 0:
            message += f', ❌ {error_count} errores'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'Sincronización de {self.name}',
                'message': message,
                'type': 'success' if error_count == 0 else 'warning'
            }
        }

    def _combine_date_time_to_utc(self, date_field, time_field):
        """Combinar fecha y hora de Tijuana y convertir a UTC con validación robusta"""
        if not date_field:
            return False
        
        # Manejar casos problemáticos
        if not time_field:
            time_field = '12:00'
        
        # Convertir a string y limpiar
        time_field = str(time_field).strip()
        
        # Si está completamente vacío o es 'False'
        if not time_field or time_field.lower() in ['false', 'none', '']:
            time_field = '12:00'
        
        try:
            import pytz
            
            # Parsear tiempo HH:MM con múltiples formatos
            hour, minute = 12, 0  # Default
            
            if ':' in time_field:
                parts = time_field.split(':')
                if len(parts) >= 2:
                    try:
                        hour = int(float(parts[0]))  # float por si viene "12.0"
                        minute = int(float(parts[1]))
                    except (ValueError, TypeError):
                        hour, minute = 12, 0
            else:
                # Solo número, asumir que es hora
                try:
                    hour = int(float(time_field))
                    minute = 0
                except (ValueError, TypeError):
                    hour, minute = 12, 0
            
            # CORRECCIÓN DE RANGOS AUTOMÁTICA
            # Manejar 24:00 como 00:00 del día siguiente
            if hour == 24 and minute == 0:
                hour = 0
                from datetime import timedelta
                date_field = date_field + timedelta(days=1)
            elif hour >= 24:
                # Si es mayor a 24, usar módulo para obtener hora válida
                hour = hour % 24
            elif hour < 0:
                hour = 0
            
            # Corregir minutos
            if minute >= 60:
                extra_hours = minute // 60
                hour += extra_hours
                minute = minute % 60
                # Volver a verificar hora después de agregar minutos extra
                if hour >= 24:
                    hour = hour % 24
            elif minute < 0:
                minute = 0
            
            # Crear datetime naive en tiempo local (Tijuana)
            local_datetime = datetime.combine(
                date_field,
                datetime.min.time().replace(hour=hour, minute=minute)
            )
            
            # Localizar en zona de Tijuana
            tijuana_tz = pytz.timezone('America/Tijuana')
            tijuana_datetime = tijuana_tz.localize(local_datetime)
            
            # Convertir a UTC para almacenamiento en Odoo
            utc_datetime = tijuana_datetime.astimezone(pytz.UTC)
            
            return utc_datetime.replace(tzinfo=None)
            
        except Exception as e:
            # Último fallback: usar mediodía
            _logger.warning(f"Error parsing time '{time_field}' for date '{date_field}': {e}. Using 12:00 as fallback.")
            
            return datetime.combine(date_field, datetime.min.time().replace(hour=12, minute=0))
    
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