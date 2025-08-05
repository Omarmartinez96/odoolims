from odoo import models, fields, api

class LimsEquipmentInvolvedV2(models.Model):
    _name = 'lims.equipment.involved.v2'
    _description = 'Equipos Involucrados en el Análisis v2'
    _rec_name = 'display_name'
    _order = 'sequence, equipment_id'

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
    # === INFORMACIÓN DEL EQUIPO ===
    # ===============================================
    equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo',
        required=True
    )
    
    usage = fields.Char(
        string='Uso',
        required=True,
        help='Especificar cómo se utilizó el equipo',
        placeholder='Ej: Pesado de muestra, Medición de pH, Autoclavado, etc.'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de uso del equipo'
    )
    
    # ===============================================
    # === FECHAS DE USO ===
    # ===============================================
    usage_date = fields.Date(
        string='Fecha de Uso',
        help='Fecha en que se utilizó el equipo'
    )
    
    usage_time = fields.Char(
        string='Hora de Uso',
        help='Hora específica de uso (formato HH:MM)'
    )
    
    # ===============================================
    # === RESPONSABLE ===
    # ===============================================
    used_by = fields.Many2one(
        'res.users',
        string='Utilizado por',
        help='Usuario que utilizó el equipo'
    )
    
    # ===============================================
    # === OBSERVACIONES ===
    # ===============================================
    notes = fields.Text(
        string='Observaciones',
        help='Notas adicionales sobre el uso del equipo'
    )
    
    # ===============================================
    # === CAMPOS COMPUTADOS ===
    # ===============================================
    display_name = fields.Char(
        string='Descripción',
        compute='_compute_display_name',
        store=True
    )
    
    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('equipment_id.name', 'usage')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.equipment_id and record.usage:
                record.display_name = f"{record.equipment_id.name} - {record.usage}"
            elif record.equipment_id:
                record.display_name = record.equipment_id.name
            else:
                record.display_name = "Equipo sin especificar"
    
    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        """Establecer valores por defecto cuando se selecciona un equipo"""
        if self.equipment_id:
            self.usage_date = fields.Date.context_today(self)
            self.used_by = self.env.user