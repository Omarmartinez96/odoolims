from odoo import models, fields, api
from datetime import datetime

class LimsAnalysisMediaV2(models.Model):
    _name = 'lims.analysis.media.v2'
    _description = 'Medios y Reactivos Utilizados en Análisis v2'
    _rec_name = 'display_name'
    _order = 'process_type, media_usage, sequence'

    # ===============================================
    # === RELACIÓN PRINCIPAL ===
    # ===============================================
    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis.v2',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )

    # ===============================================
    # === TIPO DE PROCESO (UNIFICA 5 MODELOS) ===
    # ===============================================
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Análisis Cuantitativo'),
        ('qualitative', 'Análisis Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=True)

    # ===============================================
    # === INFORMACIÓN DEL MEDIO ===
    # ===============================================
    # Campo para nombre manual del medio
    culture_media_name = fields.Char(
        string='Nombre del Medio',
        help='Nombre del medio de cultivo (manual o automático)'
    )

    # Campo para identificar si es interno o externo
    media_source = fields.Selection([
        ('internal', 'Lote Interno'),
        ('external', 'Lote Externo')
    ], string='Origen del Medio', default='internal', required=True)

    # Lote del medio interno
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio Interno',
        help='Lote específico del medio de cultivo interno'
    )

    # Campo para lote externo
    external_batch_code = fields.Char(
        string='Código de Lote Externo',
        help='Código del lote proporcionado por el cliente'
    )
    
    # Uso específico del medio
    media_usage = fields.Selection([
        ('diluyente', 'Diluyente'),
        ('eluyente', 'Eluyente'),
        ('enriquecimiento', 'Enriquecimiento'),
        ('desarrollo_selectivo', 'Desarrollo Selectivo'),
        ('desarrollo_diferencial', 'Desarrollo Diferencial'),
        ('desarrollo_selectivo_diferencial', 'Desarrollo Selectivo y Diferencial'),
        ('pruebas_bioquimicas', 'Pruebas Bioquímicas'),
        ('transporte', 'Transporte'),
        ('mantenimiento', 'Mantenimiento'),
        ('otro', 'Otro')
    ], string='Uso del Medio', required=True)

    sequence = fields.Integer(string='Secuencia', default=10)
    
    # ===============================================
    # === SISTEMA DE INCUBACIÓN COMPLETO ===
    # ===============================================
    requires_incubation = fields.Boolean(
        string='Requiere Incubación',
        default=False,
        help='Marcar si este medio requiere incubación'
    )
    
    incubation_equipment = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo de Incubación',
        domain=[('equipment_type', '=', 'incubadora')],
        help='Equipo específico utilizado para incubación'
    )
    
    incubation_start_date = fields.Date(
        string='Fecha Inicio Incubación'
    )
    
    incubation_start_time = fields.Char(
        string='Hora Inicio',
        help='Formato HH:MM'
    )
    
    incubation_end_date = fields.Date(
        string='Fecha Fin Incubación'
    )
    
    incubation_end_time = fields.Char(
        string='Hora Fin',
        help='Formato HH:MM'
    )

    # Fechas reales de finalización
    incubation_end_date_real = fields.Date(
        string='Fecha Real de Finalización',
        help='Fecha real cuando se retiró de la incubadora'
    )

    incubation_end_time_real = fields.Char(
        string='Hora Real de Finalización',
        help='Hora real cuando se retiró (formato HH:MM)'
    )
    
    # ===============================================
    # === ESTADOS COMPUTADOS DE INCUBACIÓN ===
    # ===============================================
    incubation_status = fields.Selection([
        ('not_started', 'No Iniciada'),
        ('active', 'En Incubación'),
        ('completed', 'Completada'),
        ('overdue', 'Vencida')
    ], string='Estado de Incubación', 
    compute='_compute_incubation_status', 
    store=True)

    time_remaining = fields.Char(
        string='Tiempo Restante',
        compute='_compute_time_remaining',
        help='Tiempo restante para finalizar incubación (horas y minutos)'
    )

    is_overdue = fields.Boolean(
        string='Vencida',
        compute='_compute_incubation_status',
        store=True
    )

    # ===============================================
    # === RESULTADO EN ESTE MEDIO ===
    # ===============================================
    qualitative_result = fields.Selection([
        ('detected', 'Detectado'),
        ('not_detected', 'No Detectado'),
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
        ('presence', 'Presencia'),
        ('absence', 'Ausencia'),
        ('growth', 'Crecimiento'),
        ('no_growth', 'Sin Crecimiento'),
        ('confirmed', 'Confirmado'),
        ('not_confirmed', 'No Confirmado')
    ], string='Resultado (Si Aplica)', help='Resultado obtenido en este medio')
    
    # ===============================================
    # === NOTAS ===
    # ===============================================
    preparation_notes = fields.Text(
        string='Notas de Preparación',
        help='Instrucciones especiales, observaciones, etc.'
    )
    
    # ===============================================
    # === CAMPOS COMPUTADOS ===
    # ===============================================
    incubation_duration = fields.Char(
        string='Duración de Incubación',
        compute='_compute_incubation_duration',
        help='Duración calculada automáticamente'
    )
    
    display_name = fields.Char(
        string='Descripción',
        compute='_compute_display_name',
        store=True
    )

    # Campos relacionados para filtros
    sample_code = fields.Char(
        string='Código de Muestra',
        related='parameter_analysis_id.analysis_id.sample_code',
        store=True,
        readonly=True
    )

    analysis_parameter_name = fields.Char(
        string='Parámetro',
        related='parameter_analysis_id.name',
        store=True,
        readonly=True
    )

    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('incubation_start_date', 'incubation_start_time', 'incubation_end_date', 'incubation_end_time')
    def _compute_incubation_duration(self):
        """Calcular duración de incubación"""
        for record in self:
            if record.incubation_start_date and record.incubation_end_date:
                start_date = record.incubation_start_date
                end_date = record.incubation_end_date
                duration = (end_date - start_date).days
                
                if duration == 0:
                    record.incubation_duration = "Mismo día"
                elif duration == 1:
                    record.incubation_duration = "24 horas"
                else:
                    record.incubation_duration = f"{duration * 24} horas"
            else:
                record.incubation_duration = ""
    
    @api.depends('culture_media_batch_id', 'media_usage', 'culture_media_name', 'media_source', 'external_batch_code', 'process_type')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            # Traducir proceso
            process_translations = {
                'pre_enrichment': 'Pre-enriquecimiento',
                'selective_enrichment': 'Enriquecimiento Selectivo',
                'quantitative': 'Cuantitativo',
                'qualitative': 'Cualitativo',
                'confirmation': 'Confirmación'
            }
            
            # Traducir uso
            usage_translations = {
                'diluyente': 'Diluyente',
                'eluyente': 'Eluyente',
                'enriquecimiento': 'Enriquecimiento',
                'desarrollo_selectivo': 'Desarrollo Selectivo',
                'desarrollo_diferencial': 'Desarrollo Diferencial',
                'desarrollo_selectivo_diferencial': 'Desarrollo Selectivo y Diferencial',
                'pruebas_bioquimicas': 'Pruebas Bioquímicas',
                'transporte': 'Transporte',
                'mantenimiento': 'Mantenimiento',
                'otro': 'Otro'
            }
            
            process_display = process_translations.get(record.process_type, record.process_type)
            usage_display = usage_translations.get(record.media_usage, record.media_usage)
            
            if record.media_source == 'internal' and record.culture_media_batch_id:
                media_name = record.culture_media_batch_id.culture_media_id.name
                batch_code = record.culture_media_batch_id.batch_code
                name = f"[{process_display}] {media_name} - {usage_display} (Lote: {batch_code})"
            elif record.media_source == 'external':
                media_name = record.culture_media_name or 'Medio externo'
                batch_code = record.external_batch_code or 'Sin código'
                name = f"[{process_display}] {media_name} - {usage_display} (Ext: {batch_code})"
            else:
                name = f"[{process_display}] Medio sin especificar"
                
            record.display_name = name

    @api.depends('incubation_start_date', 'incubation_end_date', 'incubation_end_date_real', 'requires_incubation')
    def _compute_incubation_status(self):
        """Calcular estado de incubación"""
        today = fields.Date.context_today(self)
        
        for record in self:
            if not record.requires_incubation:
                record.incubation_status = 'not_started'
                record.is_overdue = False
            elif record.incubation_end_date_real:
                record.incubation_status = 'completed'
                record.is_overdue = False
            elif record.incubation_start_date and record.incubation_end_date:
                if record.incubation_start_date <= today <= record.incubation_end_date:
                    record.incubation_status = 'active'
                    record.is_overdue = False
                elif today > record.incubation_end_date:
                    record.incubation_status = 'overdue'
                    record.is_overdue = True
                else:
                    record.incubation_status = 'not_started'
                    record.is_overdue = False
            else:
                record.incubation_status = 'not_started'
                record.is_overdue = False

    @api.depends('incubation_start_date', 'incubation_start_time', 'incubation_end_date', 'incubation_end_time', 'incubation_end_date_real')
    def _compute_time_remaining(self):
        """Calcular tiempo restante o duración real de incubación"""
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)
        
        for record in self:
            if not record.requires_incubation:
                record.time_remaining = ""
                continue
                
            # Si ya finalizó (tiene fecha real), mostrar duración total real
            if record.incubation_end_date_real:
                try:
                    start_str = f"{record.incubation_start_date} {record.incubation_start_time or '00:00'}"
                    end_str = f"{record.incubation_end_date_real} {record.incubation_end_time_real or '23:59'}"
                    
                    start_datetime = fields.Datetime.from_string(start_str.replace(' ', 'T'))
                    end_datetime = fields.Datetime.from_string(end_str.replace(' ', 'T'))
                    
                    duration = end_datetime - start_datetime
                    hours = int(duration.total_seconds() / 3600)
                    minutes = int((duration.total_seconds() % 3600) / 60)
                    
                    record.time_remaining = f"✅ Finalizado: {hours}h {minutes}min"
                    
                except (ValueError, TypeError):
                    record.time_remaining = "✅ Finalizado"
                continue
            
            # Si tiene fechas programadas, calcular tiempo restante o duración
            if (record.incubation_start_date and record.incubation_start_time and 
                record.incubation_end_date and record.incubation_end_time):
                
                try:
                    start_str = f"{record.incubation_start_date} {record.incubation_start_time}"
                    end_str = f"{record.incubation_end_date} {record.incubation_end_time}"
                    
                    start_datetime = fields.Datetime.from_string(start_str.replace(' ', 'T'))
                    end_datetime = fields.Datetime.from_string(end_str.replace(' ', 'T'))
                    
                    # Si no ha empezado
                    if now < start_datetime:
                        time_to_start = start_datetime - now
                        hours = int(time_to_start.total_seconds() / 3600)
                        minutes = int((time_to_start.total_seconds() % 3600) / 60)
                        record.time_remaining = f"⏳ Inicia en: {hours}h {minutes}min"
                    
                    # Si está en proceso
                    elif start_datetime <= now <= end_datetime:
                        time_left = end_datetime - now
                        hours = int(time_left.total_seconds() / 3600)
                        minutes = int((time_left.total_seconds() % 3600) / 60)
                        if hours > 0:
                            record.time_remaining = f"🔥 Restante: {hours}h {minutes}min"
                        else:
                            record.time_remaining = f"🔥 Restante: {minutes}min"
                    
                    # Si ya venció
                    elif now > end_datetime:
                        time_over = now - end_datetime
                        hours = int(time_over.total_seconds() / 3600)
                        minutes = int((time_over.total_seconds() % 3600) / 60)
                        record.time_remaining = f"⚠️ Vencido: +{hours}h {minutes}min"
                    
                except (ValueError, TypeError):
                    record.time_remaining = "❌ Error en fechas"
            else:
                record.time_remaining = "⚪ Sin programar"

    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('media_source')
    def _onchange_media_source(self):
        """Limpiar campos según el origen seleccionado"""
        if self.media_source == 'internal':
            self.external_batch_code = False
            self.culture_media_name = False
        elif self.media_source == 'external':
            self.culture_media_batch_id = False

    @api.onchange('culture_media_batch_id')
    def _onchange_culture_media_batch_id(self):
        """Auto-llenar nombre cuando se selecciona lote interno"""
        if self.culture_media_batch_id and self.media_source == 'internal':
            self.culture_media_name = self.culture_media_batch_id.culture_media_id.name

    @api.onchange('requires_incubation')
    def _onchange_requires_incubation(self):
        """Limpiar campos de incubación cuando no se requiere"""
        if not self.requires_incubation:
            self.incubation_equipment = False
            self.incubation_start_date = False
            self.incubation_start_time = False
            self.incubation_end_date = False
            self.incubation_end_time = False
            self.incubation_end_date_real = False
            self.incubation_end_time_real = False

    @api.onchange('process_type')
    def _onchange_process_type(self):
        """Establecer uso por defecto según el tipo de proceso"""
        if self.process_type == 'pre_enrichment':
            self.media_usage = 'enriquecimiento'
        elif self.process_type == 'selective_enrichment':
            self.media_usage = 'desarrollo_selectivo'
        elif self.process_type == 'quantitative':
            self.media_usage = 'diluyente'
        elif self.process_type == 'qualitative':
            self.media_usage = 'desarrollo_selectivo'
        elif self.process_type == 'confirmation':
            self.media_usage = 'pruebas_bioquimicas'
