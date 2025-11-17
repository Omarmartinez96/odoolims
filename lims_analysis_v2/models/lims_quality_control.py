from odoo import models, fields, api

class LimsExecutedQualityControlV2(models.Model):
    _name = 'lims.executed.quality.control.v2'
    _description = 'Controles de Calidad Ejecutados en Análisis v2'
    _rec_name = 'display_name'
    _order = 'sequence, execution_date desc'

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
    # === TIPO DE CONTROL ===
    # ===============================================
    qc_type_id = fields.Many2one(
        'lims.quality.control.type',
        string='Tipo de Control',
        required=True,
        help='Tipo de control de calidad a ejecutar'
    )
    
    # ===============================================
    # === INFORMACIÓN DEL CONTROL ===
    # ===============================================
    expected_result = fields.Char(
        string='Resultado Esperado',
        required=True,
        help='Resultado que debe obtenerse si el control es exitoso'
    )
    
    actual_result = fields.Char(
        string='Resultado Obtenido',
        help='Resultado real obtenido en el control'
    )
    
    # ===============================================
    # === ESTADO DEL CONTROL ===
    # ===============================================
    control_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('passed', 'Exitoso'),
        ('failed', 'Falló'),
        ('not_applicable', 'No Aplica')
    ], string='Estado del Control', default='pending', required=True)
    
    # ===============================================
    # === FECHAS Y SEGUIMIENTO ===
    # ===============================================
    execution_date = fields.Date(
        string='Fecha de Ejecución',
        help='Fecha en que se ejecutó el control'
    )
    
    execution_time = fields.Char(
        string='Hora de Ejecución',
        help='Formato HH:MM'
    )
    
    # ===============================================
    # === RESPONSABLE ===
    # ===============================================

    # =============================================== CAMPO DEPRECADO ===============================================
    executed_by = fields.Many2one(
        'res.users',
        string='CAMPO DEPRECADO',
        help='CAMPO DEPRECADO'
    )
    # =============================================== CAMPO DEPRECADO ===============================================

    executed_by_name = fields.Char(
        string='Ejecutado por',
        help='Nombre de la persona que ejecutó el control de calidad'
    )
        
    # ===============================================
    # === DETALLES TÉCNICOS ===
    # ===============================================
    method_used = fields.Char(
        string='Método Utilizado',
        help='Método o procedimiento específico utilizado'
    )
    
    equipment_used = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Utilizado',
        help='Equipo de laboratorio utilizado para el control'
    )
    
    # ===============================================
    # === LOTE DE MEDIO UTILIZADO ===
    # ===============================================
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio Utilizado',
        help='Lote específico del medio utilizado en el control'
    )
    
    # ===============================================
    # === OBSERVACIONES Y NOTAS ===
    # ===============================================
    notes = fields.Text(
        string='Notas y Observaciones',
        help='Observaciones adicionales sobre la ejecución del control'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de ejecución del control'
    )
    
    # ===============================================
    # === CAMPOS COMPUTADOS ===
    # ===============================================
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    days_since_execution = fields.Integer(
        string='Días desde Ejecución',
        compute='_compute_days_since_execution',
        help='Días transcurridos desde la ejecución'
    )
    
    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('qc_type_id.name', 'control_status', 'expected_result')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.qc_type_id:
                status_icons = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'passed': '✅',
                    'failed': '❌',
                    'not_applicable': '➖'
                }
                icon = status_icons.get(record.control_status, '❓')
                record.display_name = f"{icon} {record.qc_type_id.name}: {record.expected_result}"
            else:
                record.display_name = "Control sin especificar"
    
    @api.depends('execution_date')
    def _compute_days_since_execution(self):
        """Calcular días desde la ejecución"""
        today = fields.Date.context_today(self)
        for record in self:
            if record.execution_date:
                delta = today - record.execution_date
                record.days_since_execution = delta.days
            else:
                record.days_since_execution = 0

    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('control_status')
    def _onchange_control_status(self):
        """Auto-llenar campos cuando cambia el estado"""
        if self.control_status in ['passed', 'failed'] and not self.execution_date:
            self.execution_date = fields.Date.context_today(self)
            self.execution_time = fields.Datetime.now().strftime('%H:%M')
    
    @api.onchange('qc_type_id')
    def _onchange_qc_type_id(self):
        """Auto-llenar resultado esperado desde el tipo de control"""
        if self.qc_type_id and self.qc_type_id.default_expected_result:
            self.expected_result = self.qc_type_id.default_expected_result