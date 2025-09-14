from odoo import models, fields, api
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
    
    # === MÉTODOS COMPUTADOS ===
    @api.depends('equipment_id.name', 'usage_type', 'process_context', 'start_datetime', 'related_media_id.culture_media_name')
    def _compute_display_name(self):
        for record in self:
            # Procesos más explícitos
            process_names = {
                'pre_enrichment': 'Pre-enriquecimiento',
                'selective_enrichment': 'Enriquecimiento Selectivo',
                'quantitative': 'Análisis Cuantitativo',
                'qualitative': 'Análisis Cualitativo',
                'confirmation': 'Confirmación',
                'other': 'Otro'
            }
            
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
            
            if record.process_context and record.process_context != 'other':
                process_display = process_names.get(record.process_context, record.process_context)
                context = f" - {process_display}"
            elif record.related_media_id and record.related_media_id.culture_media_name:
                context = f" - {record.related_media_id.culture_media_name}"
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
    
    @api.depends('start_datetime', 'end_datetime')
    def _compute_is_active_use(self):
        for record in self:
            record.is_active_use = bool(record.start_datetime and not record.end_datetime)
    
    @api.depends('is_active_use', 'end_datetime', 'planned_end_datetime')
    def _compute_status_display(self):
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