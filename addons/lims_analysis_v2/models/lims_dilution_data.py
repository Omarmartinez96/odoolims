from odoo import models, fields, api

class LimsRawDilutionDataV2(models.Model):
    _name = 'lims.raw.dilution.data.v2'
    _description = 'Datos Crudos de Diluciones v2'
    _order = 'dilution_factor'

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
    # === TIPO DE MÉTODO ===
    # ===============================================
    method_type = fields.Selection([
        ('ufc', 'Recuento en Placa (UFC)'),
        ('nmp', 'Número Más Probable (NMP)')
    ], string='Tipo de Método', default='ufc', required=True)
    
    # ===============================================
    # === DILUCIÓN ===
    # ===============================================
    dilution_factor = fields.Selection([
        ('direct', 'Directo (sin dilución)'),
        ('10_1', '10⁻¹ (1:10)'),
        ('10_2', '10⁻² (1:100)'),
        ('10_3', '10⁻³ (1:1,000)'),
        ('10_4', '10⁻⁴ (1:10,000)'),
        ('10_5', '10⁻⁵ (1:100,000)'),
        ('10_6', '10⁻⁶ (1:1,000,000)')
    ], string='Dilución', required=True)
    
    # ===============================================
    # === PARA RECUENTOS EN PLACA (UFC) ===
    # ===============================================
    ufc_count = fields.Integer(
        string='UFC Contadas',
        help='Número de colonias contadas en la placa'
    )
    
    # ===============================================
    # === PARA MÉTODOS NMP ===
    # ===============================================
    positive_tubes = fields.Integer(
        string='Tubos Positivos',
        help='Número de tubos positivos de esta dilución'
    )
    
    total_tubes = fields.Integer(
        string='Total de Tubos',
        help='Número total de tubos inoculados en esta dilución',
        default=3
    )
    
    # RESULTADO NMP MANUAL
    nmp_result = fields.Char(
        string='Resultado NMP',
        help='Resultado obtenido de la tabla NMP (ej: 110 NMP/100mL)'
    )
    
    # ===============================================
    # === OBSERVACIONES ===
    # ===============================================
    observations = fields.Text(
        string='Observaciones',
        help='Notas específicas sobre esta dilución',
        placeholder='Ej: Placas confluentes, Tubos con gas, etc...'
    )
    
    # ===============================================
    # === RESULTADO CALCULADO ===
    # ===============================================
    calculated_result = fields.Char(
        string='Resultado Calculado',
        compute='_compute_calculated_result',
        store=True,
        help='Resultado según el tipo de método'
    )
    
    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('method_type', 'ufc_count', 'dilution_factor', 'positive_tubes', 'total_tubes', 'nmp_result')
    def _compute_calculated_result(self):
        """Calcular resultado según el tipo de método"""
        for record in self:
            if record.method_type == 'ufc' and record.ufc_count is not False and record.ufc_count >= 0:
                # CÁLCULO UFC
                factors = {
                    'direct': 1, '10_1': 10, '10_2': 100, 
                    '10_3': 1000, '10_4': 10000, '10_5': 100000, '10_6': 1000000
                }
                factor = factors.get(record.dilution_factor, 1)
                result = record.ufc_count * factor
                
                if result == 0:
                    record.calculated_result = "No detectado"
                elif result < 10:
                    record.calculated_result = f"< 1.0 x 10¹ UFC/g"
                elif result > 300000:
                    record.calculated_result = f"> 3.0 x 10⁵ UFC/g"
                else:
                    if result >= 1000:
                        exp = len(str(int(result))) - 1
                        base = result / (10 ** exp)
                        record.calculated_result = f"{base:.1f} x 10{chr(8304 + exp)} UFC/g"
                    else:
                        record.calculated_result = f"{result} UFC/g"
                        
            elif record.method_type == 'nmp':
                # PARA NMP
                if record.positive_tubes is not False and record.total_tubes:
                    tube_info = f"{record.positive_tubes}/{record.total_tubes} tubos +"
                    if record.nmp_result:
                        record.calculated_result = f"{tube_info} → {record.nmp_result}"
                    else:
                        record.calculated_result = f"{tube_info} → Consultar tabla NMP"
                else:
                    record.calculated_result = "Datos incompletos"
            else:
                record.calculated_result = False
    
    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('method_type')
    def _onchange_method_type(self):
        """Limpiar campos no relevantes según el tipo de método"""
        if self.method_type == 'ufc':
            self.positive_tubes = False
            self.total_tubes = 3
            self.nmp_result = False
        elif self.method_type == 'nmp':
            self.ufc_count = False