from odoo import models, fields, api

class LimsConfirmationResultV2(models.Model):
    _name = 'lims.confirmation.result.v2'
    _description = 'Resultados de Confirmación por Lote v2'
    _rec_name = 'batch_display_name'
    _order = 'batch_display_name'

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
    # === RELACIÓN CON MEDIO DE CONFIRMACIÓN ===
    # ===============================================
    confirmation_media_id = fields.Many2one(
        'lims.analysis.media.v2',
        string='Medio de Confirmación',
        domain=[('process_type', '=', 'confirmation')],
        ondelete='cascade'
    )
    
    # ===============================================
    # === INFORMACIÓN DEL LOTE ===
    # ===============================================
    batch_display_name = fields.Char(
        string='Lote de Medio',
        required=True,
        readonly=True,
        help='Formato: "Nombre del Medio (Lote: Código)"'
    )
    
    # ===============================================
    # === RESULTADO DEL CRECIMIENTO ===
    # ===============================================
    result = fields.Char(
        string='Resultado del Crecimiento',
        help='Resultado observado en este lote',
        placeholder='Ej: Positivo, Negativo, Crecimiento característico, cambio de color, etc.'
    )
    
    # ===============================================
    # === RESULTADO CUALITATIVO ESTRUCTURADO ===
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
    ], string='Resultado Estructurado')
    
    # ===============================================
    # === OBSERVACIONES ===
    # ===============================================
    observations = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales sobre este resultado'
    )
    
    # ===============================================
    # === FECHAS ===
    # ===============================================
    result_date = fields.Date(
        string='Fecha del Resultado',
        default=fields.Date.context_today,
        help='Fecha en que se obtuvo el resultado'
    )
    
    # ===============================================
    # === RESPONSABLE ===
    # ===============================================

    # =============================================== CAMPO DEPRECADO ===============================================
    recorded_by = fields.Many2one(
        'res.users',
        string='Registrado por (DEPRECADO)',
        default=lambda self: self.env.user,
        help='CAMPO DEPRECADO - USAR RECORDED_BY_NAME'
    )
    # =============================================== CAMPO DEPRECADO ===============================================


    recorded_by_name = fields.Char(
        string='Registrado por',
        default=lambda self: self.env.user.name,
        help='Nombre de la persona que registró este resultado'
    )

    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('qualitative_result')
    def _onchange_qualitative_result(self):
        """Auto-completar resultado con el valor cualitativo"""
        if self.qualitative_result:
            qualitative_map = {
                'detected': 'Detectado',
                'not_detected': 'No Detectado',
                'positive': 'Positivo',
                'negative': 'Negativo',
                'presence': 'Presencia',
                'absence': 'Ausencia',
                'growth': 'Crecimiento',
                'no_growth': 'Sin Crecimiento',
                'confirmed': 'Confirmado',
                'not_confirmed': 'No Confirmado'
            }
            self.result = qualitative_map.get(self.qualitative_result, self.qualitative_result)