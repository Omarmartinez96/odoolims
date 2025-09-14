from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class LimsEquipmentUsageLog(models.Model):
    _name = 'lims.equipment.usage.log'
    _description = 'Bitácora de Uso de Equipos'
    _rec_name = 'display_name'
    _order = 'start_datetime desc, id desc'

    # === RELACIÓN PRINCIPAL ===
    equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo',
        required=True,
        ondelete='cascade'
    )
    
    # === TIPO Y CONTEXTO DE USO ===
    usage_type = fields.Selection([
        ('incubation', 'Incubación'),
        ('processing', 'Procesamiento de Ambiente'), 
        ('weighing', 'Pesado'),
        ('measurement', 'Medición'),
        ('sterilization', 'Esterilización'),
        ('storage', 'Almacenamiento'),
        ('other', 'Otro')
    ], string='Tipo de Uso', required=True)
    
    process_context = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),
        ('confirmation', 'Confirmación'),
        ('other', 'Otro')
    ], string='Contexto del Proceso')
    
    # === RELACIONES CON ANÁLISIS ===
    related_analysis_id = fields.Many2one(
        'lims.analysis.v2',
        string='Análisis Relacionado',
        ondelete='cascade'
    )
    
    related_parameter_id = fields.Many2one(
        'lims.parameter.analysis.v2',
        string='Parámetro Relacionado',
        ondelete='cascade'
    )
    
    related_media_id = fields.Many2one(
        'lims.analysis.media.v2',
        string='Medio Relacionado',
        ondelete='cascade'
    )
    
    # === FECHAS Y TIEMPOS ===
    start_datetime = fields.Datetime(
        string='Inicio de Uso',
        required=True
    )
    
    end_datetime = fields.Datetime(
        string='Fin de Uso'
    )
    
    planned_end_datetime = fields.Datetime(
        string='Fin Planificado'
    )
    
    # === USUARIO Y OBSERVACIONES ===
    used_by_name = fields.Char(
        string='Utilizado por',
        required=True
    )
    
    usage_notes = fields.Text(
        string='Observaciones'
    )
    
    # === MARCADORES ESPECIALES ===
    is_historical = fields.Boolean(
        string='Registro Histórico',
        default=False,
        help='Indica si fue creado por sincronización de datos históricos'
    )
    
    is_active_use = fields.Boolean(
        string='Uso Activo',
        compute='_compute_is_active_use',
        store=True,
        help='Indica si el equipo está actualmente en uso'
    )
    
    # === CAMPOS COMPUTADOS ===
    display_name = fields.Char(
        string='Descripción',
        compute='_compute_display_name',
        store=True
    )
    
    duration_hours = fields.Float(
        string='Duración (Horas)',
        compute='_compute_duration',
        store=True
    )
    
    status_display = fields.Char(
        string='Estado',
        compute='_compute_status_display'
    )
    
    # === CAMPOS RELACIONADOS ===
    sample_code = fields.Char(
        string='Código de Muestra',
        related='related_analysis_id.sample_code',
        store=True
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='related_analysis_id.customer_id',
        store=True
    )
    
    media_culture_name = fields.Char(
        string='Medio de Cultivo',
        compute='_compute_media_info',
        store=True,
        help='Nombre del medio de cultivo específico'
    )

    process_display = fields.Char(
        string='Proceso Específico',
        compute='_compute_media_info',
        store=True,
        help='Proceso más específico basado en el contexto'
    )

    tijuana_start_display = fields.Char(
        string='Inicio (Tijuana)',
        compute='_compute_tijuana_times',
        help='Hora de inicio en timezone de Tijuana'
    )
    
    tijuana_planned_display = fields.Char(
        string='Fin Previsto (Tijuana)', 
        compute='_compute_tijuana_times',
        help='Hora planificada de fin en timezone de Tijuana'
    )
    
    tijuana_end_display = fields.Char(
        string='Fin Real (Tijuana)',
        compute='_compute_tijuana_times',
        help='Hora real de fin en timezone de Tijuana'
    )

    # === MÉTODOS COMPUTADOS ===

    @api.depends('start_datetime', 'planned_end_datetime', 'end_datetime')
    def _compute_tijuana_times(self):
        """Convertir horarios UTC a Tijuana para mostrar"""
        try:
            import pytz
            tijuana_tz = pytz.timezone('America/Tijuana')
            
            for record in self:
                # Inicio
                if record.start_datetime:
                    start_utc = pytz.UTC.localize(record.start_datetime)
                    start_tijuana = start_utc.astimezone(tijuana_tz)
                    record.tijuana_start_display = start_tijuana.strftime('%d/%m/%Y %H:%M')
                else:
                    record.tijuana_start_display = ''
                
                # Fin Previsto
                if record.planned_end_datetime:
                    planned_utc = pytz.UTC.localize(record.planned_end_datetime)
                    planned_tijuana = planned_utc.astimezone(tijuana_tz)
                    record.tijuana_planned_display = planned_tijuana.strftime('%d/%m/%Y %H:%M')
                else:
                    record.tijuana_planned_display = ''
                
                # Fin Real
                if record.end_datetime:
                    end_utc = pytz.UTC.localize(record.end_datetime)
                    end_tijuana = end_utc.astimezone(tijuana_tz)
                    record.tijuana_end_display = end_tijuana.strftime('%d/%m/%Y %H:%M')
                else:
                    record.tijuana_end_display = ''
                    
        except Exception as e:
            # Fallback sin timezone
            for record in self:
                record.tijuana_start_display = record.start_datetime.strftime('%d/%m/%Y %H:%M') if record.start_datetime else ''
                record.tijuana_planned_display = record.planned_end_datetime.strftime('%d/%m/%Y %H:%M') if record.planned_end_datetime else ''
                record.tijuana_end_display = record.end_datetime.strftime('%d/%m/%Y %H:%M') if record.end_datetime else ''

    @api.depends('related_media_id.culture_media_name', 'process_context', 'related_parameter_id.name')
    def _compute_media_info(self):
        for record in self:
            # Priorizar medio de cultivo
            if record.related_media_id and record.related_media_id.culture_media_name:
                record.media_culture_name = record.related_media_id.culture_media_name
            else:
                record.media_culture_name = 'Sin medio específico'
            
            # Proceso más específico
            process_names = {
                'pre_enrichment': 'Pre-enriquecimiento',
                'selective_enrichment': 'Enriquecimiento Selectivo',
                'quantitative': 'Cuantitativo',
                'qualitative': 'Cualitativo',
                'confirmation': 'Confirmación',
                'other': 'Otro'
            }
            
            record.process_display = process_names.get(record.process_context, record.process_context or 'Sin especificar')

    @api.depends('equipment_id.name', 'usage_type', 'media_culture_name', 'process_display')
    def _compute_display_name(self):
        for record in self:
            usage_names = {
                'incubation': 'Incubación',
                'processing': 'Procesamiento',
                'weighing': 'Pesado',
                'measurement': 'Medición',
                'sterilization': 'Esterilización',
                'storage': 'Almacenamiento',
                'other': 'Otro'
            }
            
            usage_display = usage_names.get(record.usage_type, record.usage_type)
            
            # Priorizar medio de cultivo sobre proceso
            if record.media_culture_name and record.media_culture_name != 'Sin medio específico':
                context = f" - {record.media_culture_name}"
            elif record.process_display and record.process_display != 'Sin especificar':
                context = f" - {record.process_display}"
            else:
                context = ""
            
            record.display_name = f"{record.equipment_id.name} ({usage_display}){context}"
    
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for record in self:
            if record.start_datetime and record.end_datetime:
                delta = record.end_datetime - record.start_datetime
                record.duration_hours = round(delta.total_seconds() / 3600, 2)
            else:
                record.duration_hours = 0.0
    
    @api.depends('start_datetime', 'end_datetime', 'planned_end_datetime')
    def _compute_is_active_use(self):
        for record in self:
            record.is_active_use = bool(record.start_datetime and not record.end_datetime)

    @api.depends('is_active_use', 'end_datetime', 'planned_end_datetime')
    def _compute_status_display(self):
        """Calcular estado usando timezone de Tijuana"""
        try:
            import pytz
            
            # Obtener hora actual en Tijuana
            tijuana_tz = pytz.timezone('America/Tijuana')
            utc_now = pytz.UTC.localize(datetime.utcnow())
            tijuana_now = utc_now.astimezone(tijuana_tz)
            
            for record in self:
                if record.is_active_use:
                    if record.planned_end_datetime:
                        # Convertir planned_end_datetime de UTC a Tijuana para comparar
                        planned_utc = pytz.UTC.localize(record.planned_end_datetime)
                        planned_tijuana = planned_utc.astimezone(tijuana_tz)
                        
                        if tijuana_now > planned_tijuana:
                            record.status_display = "🔴 Vencido"
                        else:
                            record.status_display = "🟢 En Uso"
                    else:
                        record.status_display = "🟢 En Uso"
                elif record.end_datetime:
                    record.status_display = "✅ Completado"
                else:
                    record.status_display = "⏸️ Sin Definir"
                    
        except Exception as e:
            # Fallback sin timezone
            now = fields.Datetime.now()
            for record in self:
                if record.is_active_use:
                    if record.planned_end_datetime and now > record.planned_end_datetime:
                        record.status_display = "🔴 Vencido"
                    else:
                        record.status_display = "🟢 En Uso"
                elif record.end_datetime:
                    record.status_display = "✅ Completado"
                else:
                    record.status_display = "⏸️ Sin Definir"

    @api.depends('start_datetime', 'incubation_start_time', 'incubation_end_date', 'incubation_end_time', 'incubation_end_date_real')
    def _compute_time_remaining(self):
        """Calcular tiempo restante con zona horaria de Tijuana"""
        try:
            import pytz
            
            # Obtener hora actual en Tijuana
            tijuana_tz = pytz.timezone('America/Tijuana')
            utc_now = pytz.UTC.localize(datetime.utcnow())
            tijuana_now = utc_now.astimezone(tijuana_tz)
            
            for record in self:
                if not record.requires_incubation:
                    record.time_remaining = ""
                    continue
                    
                # Si ya finalizó
                if record.end_datetime:
                    if record.start_datetime:
                        # Convertir ambos a Tijuana para calcular duración
                        start_utc = pytz.UTC.localize(record.start_datetime)
                        start_tijuana = start_utc.astimezone(tijuana_tz)
                        
                        end_utc = pytz.UTC.localize(record.end_datetime)
                        end_tijuana = end_utc.astimezone(tijuana_tz)
                        
                        duration = end_tijuana - start_tijuana
                        hours = int(duration.total_seconds() / 3600)
                        minutes = int((duration.total_seconds() % 3600) / 60)
                        
                        record.time_remaining = f"✅ Finalizado: {hours}h {minutes}min"
                    else:
                        record.time_remaining = "✅ Finalizado"
                    continue
                
                # Si tiene fechas planificadas
                if record.planned_end_datetime:
                    # Convertir planned a Tijuana
                    planned_utc = pytz.UTC.localize(record.planned_end_datetime)
                    planned_tijuana = planned_utc.astimezone(tijuana_tz)
                    
                    if tijuana_now < planned_tijuana:
                        # Aún no vence
                        time_left = planned_tijuana - tijuana_now
                        hours = int(time_left.total_seconds() / 3600)
                        minutes = int((time_left.total_seconds() % 3600) / 60)
                        
                        if hours > 0:
                            record.time_remaining = f"⏰ Restante: {hours}h {minutes}min"
                        else:
                            record.time_remaining = f"⏰ Restante: {minutes}min"
                    else:
                        # Ya venció
                        time_over = tijuana_now - planned_tijuana
                        hours = int(time_over.total_seconds() / 3600)
                        minutes = int((time_over.total_seconds() % 3600) / 60)
                        record.time_remaining = f"⚠️ Vencido: +{hours}h {minutes}min"
                else:
                    record.time_remaining = "⚪ Sin fecha límite"
                    
        except Exception as e:
            # Fallback sin timezone
            for record in self:
                record.time_remaining = "❌ Error de timezone"

    def action_finish_individual(self):
        """Finalizar uso individual de equipo"""
        if not self.is_active_use and self.status_display != '🔴 Vencido':
            raise UserError('Este registro ya está finalizado.')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Finalizar Uso de Equipo',
            'res_model': 'lims.equipment.finish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_ids': [self.id],
                'default_usage_log_ids': [(6, 0, [self.id])]
            }
        }

    def action_finish_equipment_usage(self):
        """Finalizar uso masivo de equipos"""
        # Si se llama desde un recordset específico, usar esos IDs
        if self:
            active_ids = self.ids
        else:
            # Si se llama desde contexto (botón de header)
            active_ids = self.env.context.get('active_ids', [])
        
        if not active_ids:
            raise UserError('No hay registros seleccionados.')
        
        # Filtrar solo registros que pueden finalizarse
        logs_to_finish = self.browse(active_ids).filtered(
            lambda l: l.is_active_use or l.status_display == '🔴 Vencido'
        )
        
        if not logs_to_finish:
            raise UserError('Ningún registro seleccionado puede finalizarse.')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Finalizar Uso de Equipos',
            'res_model': 'lims.equipment.finish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_ids': logs_to_finish.ids,
                'default_usage_log_ids': [(6, 0, logs_to_finish.ids)]
            }
        }