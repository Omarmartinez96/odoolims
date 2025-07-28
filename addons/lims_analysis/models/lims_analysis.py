from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _rec_name = 'display_name'
    _order = 'create_date desc'

    # Relación con la recepción de muestra (que tiene el sample_code)
    sample_reception_id = fields.Many2one(
        'lims.sample.reception',
        string='Muestra Recibida',
        required=True,
        ondelete='cascade',
        domain=[('reception_state', '=', 'recibida')]
    )

    # Campo relacionado para mostrar el código de muestra
    sample_code = fields.Char(
        string='Código de Muestra',
        related='sample_reception_id.sample_code',
        readonly=True,
        store=True
    )

    # Campos relacionados para información adicional
    sample_identifier = fields.Char(
        string='Identificación de Muestra',
        related='sample_reception_id.sample_identifier',
        readonly=True,
        store=True
    )

    display_name = fields.Char(
        string='Nombre del Análisis',
        compute='_compute_display_name',
        store=True
    )
    
    # Fechas
    analysis_start_date = fields.Date(
        string='Fecha de Inicio',
        default=fields.Date.context_today
    )
    analysis_end_date = fields.Date(
        string='Fecha de Finalización'
    )
    
    # Estado del análisis
    analysis_state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('validated', 'Validado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft')
    
    # 🆕 RELACIÓN CON PARÁMETROS DE ANÁLISIS
    parameter_analysis_ids = fields.One2many(
        'lims.parameter.analysis',
        'analysis_id',
        string='Parámetros de Análisis'
    )
    
    @api.depends('sample_reception_id')
    def _compute_display_name(self):
        """Calcular nombre del análisis"""
        for analysis in self:
            if analysis.sample_code:
                analysis.display_name = f"Análisis - {analysis.sample_code}"
            else:
                analysis.display_name = "Análisis"
    
    def action_complete_analysis(self):
        """Completar análisis"""
        self.analysis_state = 'completed'
        self.analysis_end_date = fields.Date.context_today(self)

    def action_clean_orphan_records(self):
        """Método temporal para limpiar registros huérfanos"""
        # Buscar análisis con sample_reception_id que no existe
        all_analyses = self.search([])
        orphan_count = 0
        
        for analysis in all_analyses:
            try:
                # Intentar acceder a la recepción
                if analysis.sample_reception_id:
                    reception_exists = analysis.sample_reception_id.exists()
                    if not reception_exists:
                        analysis.unlink()
                        orphan_count += 1
            except:
                # Si hay error, es huérfano
                analysis.unlink()
                orphan_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Limpieza Completada',
                'message': f'Se eliminaron {orphan_count} registros huérfanos',
                'type': 'success',
            }
        }

    @api.model
    def cron_clean_orphan_records(self):
        """Cron job para limpiar registros huérfanos automáticamente"""
        # Limpiar análisis huérfanos
        orphan_analyses = self.search([]).filtered(
            lambda a: not a.sample_reception_id.exists()
        )
        if orphan_analyses:
            _logger.info(f"Limpiando {len(orphan_analyses)} análisis huérfanos")
            orphan_analyses.unlink()
        
        # Limpiar recepciones huérfanas
        orphan_receptions = self.env['lims.sample.reception'].search([]).filtered(
            lambda r: not r.sample_id.exists()
        )
        if orphan_receptions:
            _logger.info(f"Limpiando {len(orphan_receptions)} recepciones huérfanas")
            orphan_receptions.unlink()

    @api.model_create_multi
    def create(self, vals_list):
            """Override create para copiar parámetros desde la muestra"""
            records = super().create(vals_list)
            
            for record in records:
                # Obtener parámetros de la muestra a través de la recepción
                if record.sample_reception_id and record.sample_reception_id.sample_id:
                    sample = record.sample_reception_id.sample_id
                    sample_parameters = sample.parameter_ids
                    
                    print(f"DEBUG: Muestra encontrada: {sample.sample_identifier}")
                    print(f"DEBUG: Parámetros encontrados: {len(sample_parameters)}")
                    
                    # Crear parámetros de análisis para cada parámetro de la muestra
                    for param in sample_parameters:
                        print(f"DEBUG: Creando parámetro de análisis para: {param.name}")
                        
                        self.env['lims.parameter.analysis'].create({
                            'analysis_id': record.id,
                            'parameter_id': param.id,
                            'name': param.name or 'Sin nombre',
                            'method': param.method or '',
                            'microorganism': param.microorganism or '',
                            'unit': param.unit or '',
                            'category': param.category or 'other',
                            'sequence': param.id,  # Usar el ID como secuencia temporal
                        })
                        
                else:
                    print(f"DEBUG: No se encontró muestra para el análisis {record.id}")
                    print(f"DEBUG: sample_reception_id: {record.sample_reception_id}")
                    if record.sample_reception_id:
                        print(f"DEBUG: sample_id: {record.sample_reception_id.sample_id}")
            
            return records


# 🆕 NUEVO MODELO PARA PARÁMETROS DE ANÁLISIS - CORREGIDO
class LimsParameterAnalysis(models.Model):
    _name = 'lims.parameter.analysis'
    _description = 'Parámetros de Análisis con Resultados'
    _rec_name = 'name'
    _order = 'sequence, name'

    # Relación con el análisis padre
    analysis_id = fields.Many2one(
        'lims.analysis',
        string='Análisis',
        required=True,
        ondelete='cascade'
    )
    
    analysis_start_date = fields.Date(
        string='Fecha Inicio de Análisis',
        help='Fecha en que se inició el análisis de este parámetro'
    )

    analysis_commitment_date = fields.Date(
        string='Fecha Compromiso de Análisis',
        help='Fecha comprometida para la entrega del resultado'
    )

    # Información del parámetro (copiada desde el parámetro original)
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro Original',
        readonly=True
    )
    
    name = fields.Char(
        string='Nombre del Parámetro',
        required=True
    )
    method = fields.Char(
        string='Método'
    )
    microorganism = fields.Char(
        string='Microorganismo/Analito'
    )
    unit = fields.Char(
        string='Unidad'
    )
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], string='Categoría')
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    # 🆕 SISTEMA HÍBRIDO DE RESULTADOS
    
    # Campo principal (siempre visible)
    result_value = fields.Char(
        string='Resultado',
        help='Resultado principal del análisis',
        placeholder='Ej: 7.2, Negativo, 1.2 x 10² UFC/g, < 0.01 mg/kg'
    )
    
    # Campos específicos que aparecen según contexto
    result_numeric = fields.Float(
        string='Valor Numérico',
        help='Para cálculos automáticos y validaciones',
        digits=(12, 4)
    )
    
    result_unit = fields.Char(
        string='Unidad',
        help='Unidad del resultado',
        placeholder='mg/L, °C, pH, NTU, etc.'
    )

    result_type = fields.Selection([
        ('qualitative', 'Cualitativo'),
        ('quantitative', 'Cuantitativo')
    ], string='Tipo de Resultado', default='quantitative', required=True)
    
    # Para microbiología
    result_qualitative = fields.Selection([
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
    ], string='Resultado Cualitativo')
    
    # Límites de detección y cuantificación
    below_detection_limit = fields.Boolean(
        string='< Límite de Detección',
        help='Resultado por debajo del límite de detección'
    )
    
    above_quantification_limit = fields.Boolean(
        string='> Límite de Cuantificación',
        help='Resultado por encima del límite de cuantificación'
    )
    
    # CAMPOS DE ANÁLISIS (sin duplicar analysis_status)
    analysis_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string='Estado del Análisis', default='pending')
    
    analysis_date = fields.Date(
        string='Fecha de Análisis'
    )
    
    analyst_notes = fields.Text(
        string='Observaciones del Analista',
        help='Notas técnicas sobre el análisis realizado'
    )
    
    # Control de calidad específico
    qc_passed = fields.Boolean(
        string='Control de Calidad Aprobado',
        default=False
    )
    
    # 🆕 RELACIÓN CON DATOS CRUDOS DE DILUCIONES
    raw_dilution_data_ids = fields.One2many(
        'lims.raw.dilution.data',
        'parameter_analysis_id',
        string='Datos Crudos de Diluciones'
    )
    
    # Campo que muestra SOLO los cálculos (NO actualiza resultado automáticamente)
    dilution_calculations = fields.Text(
        string='Cálculos Informativos',
        compute='_compute_dilution_calculations',
        help='Cálculos informativos basados en datos crudos (solo referencia)'
    )
    
    # 🆕 CAMPOS PARA RESULTADO MANUAL
    result_unit_selection = fields.Selection([
        ('ufc_g', 'UFC/g'),
        ('ufc_ml', 'UFC/mL'),
        ('nmp_g', 'NMP/g'),
        ('nmp_ml', 'NMP/mL'),
        ('ufc_100ml', 'UFC/100mL'),
        ('nmp_100ml', 'NMP/100mL'),
        ('mg_kg', 'mg/kg'),
        ('mg_l', 'mg/L'),
        ('custom', 'Otra unidad (especificar)')
    ], string='Unidad del Resultado')
    
    custom_unit = fields.Char(
        string='Especificar Unidad',
        help='Especificar unidad personalizada'
    )
    
    @api.depends('raw_dilution_data_ids.ufc_count')
    def _compute_dilution_calculations(self):
        """Mostrar SOLO cálculos informativos (NO actualiza resultado automáticamente)"""
        for record in self:
            if record.raw_dilution_data_ids:
                calculations = []
                
                # Mapeo manual de diluciones para mostrar
                dilution_names = {
                    'direct': 'Directo',
                    '10_1': '10⁻¹',
                    '10_2': '10⁻²',
                    '10_3': '10⁻³',
                    '10_4': '10⁻⁴',
                    '10_5': '10⁻⁵',
                    '10_6': '10⁻⁶'
                }
                
                for data in record.raw_dilution_data_ids:
                    if data.ufc_count is not False and data.ufc_count >= 0:
                        dilution_name = dilution_names.get(data.dilution_factor, data.dilution_factor)
                        calculations.append(f"{dilution_name}: {data.ufc_count} UFC → {data.calculated_result}")
                
                if calculations:
                    record.dilution_calculations = "\n".join(calculations)
                else:
                    record.dilution_calculations = "Sin datos registrados"
            else:
                record.dilution_calculations = "Sin diluciones registradas"
    
    @api.onchange('result_unit_selection')
    def _onchange_result_unit_selection(self):
        """Limpiar unidad personalizada si no se selecciona 'custom'"""
        if self.result_unit_selection != 'custom':
            self.custom_unit = False
    
    # 🆕 MÉTODOS ONCHANGE BÁSICOS (sin campos inexistentes)
    @api.onchange('result_numeric', 'result_unit')
    def _onchange_numeric_result(self):
        """Auto-completar resultado principal cuando se llena numérico + unidad"""
        if self.result_numeric and self.result_unit:
            if self.result_unit.lower() in ['ph', 'unidades de ph']:
                self.result_value = f"{self.result_numeric:.1f} {self.result_unit}"
            else:
                self.result_value = f"{self.result_numeric} {self.result_unit}"
    
    @api.onchange('result_qualitative')
    def _onchange_qualitative_result(self):
        """Auto-completar resultado principal con resultado cualitativo"""
        if self.result_qualitative:
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
            self.result_value = qualitative_map.get(self.result_qualitative, self.result_qualitative)
    
    @api.onchange('below_detection_limit', 'above_quantification_limit')
    def _onchange_limits(self):
        """Auto-completar resultado cuando está fuera de límites"""
        if self.below_detection_limit:
            unit = self.result_unit or ''
            self.result_value = f"< LD {unit}".strip()
        elif self.above_quantification_limit:
            unit = self.result_unit or ''
            self.result_value = f"> LC {unit}".strip()

    @api.onchange('result_type')
    def _onchange_result_type(self):
        """Limpiar campos cuando cambia el tipo de resultado"""
        if self.result_type == 'qualitative':
            # Limpiar campos cuantitativos
            self.result_numeric = False
            self.result_unit = False
            self.below_detection_limit = False
            self.above_quantification_limit = False
            self.result_unit_selection = False
            self.custom_unit = False
            # Limpiar datos de diluciones
            self.raw_dilution_data_ids = [(5, 0, 0)]
        elif self.result_type == 'quantitative':
            # Limpiar campos cualitativos
            self.result_qualitative = False

# 🆕 MODELO PARA DATOS CRUDOS DE DILUCIONES
class LimsRawDilutionData(models.Model):
    _name = 'lims.raw.dilution.data'
    _description = 'Datos Crudos de Diluciones'
    _order = 'dilution_factor'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # 🆕 TIPO DE MÉTODO
    method_type = fields.Selection([
        ('ufc', 'Recuento en Placa (UFC)'),
        ('nmp', 'Número Más Probable (NMP)'),
        ('qualitative', 'Cualitativo')
    ], string='Tipo de Método', default='ufc', required=True)
    
    dilution_factor = fields.Selection([
        ('direct', 'Directo (sin dilución)'),
        ('10_1', '10⁻¹ (1:10)'),
        ('10_2', '10⁻² (1:100)'),
        ('10_3', '10⁻³ (1:1,000)'),
        ('10_4', '10⁻⁴ (1:10,000)'),
        ('10_5', '10⁻⁵ (1:100,000)'),
        ('10_6', '10⁻⁶ (1:1,000,000)')
    ], string='Dilución', required=True)
    
    # 🆕 PARA RECUENTOS EN PLACA (UFC)
    ufc_count = fields.Integer(
        string='UFC Contadas',
        help='Número de colonias contadas en la placa'
    )
    
    # 🆕 PARA MÉTODOS NMP
    positive_tubes = fields.Integer(
        string='Tubos Positivos',
        help='Número de tubos positivos de esta dilución'
    )
    
    total_tubes = fields.Integer(
        string='Total de Tubos',
        help='Número total de tubos inoculados en esta dilución',
        default=3
    )
    
    # 🆕 RESULTADO NMP MANUAL (ya que se consulta en tabla)
    nmp_result = fields.Char(
        string='Resultado NMP',
        help='Resultado obtenido de la tabla NMP (ej: 110 NMP/100mL)'
    )
    
    # 🆕 PARA CUALITATIVO POR DILUCIÓN
    result_qualitative = fields.Selection([
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
        ('growth', 'Crecimiento'),
        ('no_growth', 'Sin Crecimiento')
    ], string='Resultado')
    
    # Observaciones específicas de esta dilución
    observations = fields.Text(
        string='Observaciones',
        help='Notas específicas sobre esta dilución',
        placeholder='Ej: Placas confluentes, Tubos con gas, etc...'
    )
    
    # 🆕 CAMPO COMPUTADO QUE SE ADAPTA AL TIPO
    calculated_result = fields.Char(
        string='Resultado Calculado',
        compute='_compute_calculated_result',
        store=True,
        help='Resultado según el tipo de método'
    )
    
    @api.depends('method_type', 'ufc_count', 'dilution_factor', 'positive_tubes', 'total_tubes', 'nmp_result', 'result_qualitative')
    def _compute_calculated_result(self):
        """Calcular resultado según el tipo de método"""
        for record in self:
            if record.method_type == 'ufc' and record.ufc_count is not False and record.ufc_count >= 0:
                # CÁLCULO UFC (como antes)
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
                # PARA NMP - MOSTRAR INFO DE TUBOS + RESULTADO MANUAL
                if record.positive_tubes is not False and record.total_tubes:
                    tube_info = f"{record.positive_tubes}/{record.total_tubes} tubos +"
                    if record.nmp_result:
                        record.calculated_result = f"{tube_info} → {record.nmp_result}"
                    else:
                        record.calculated_result = f"{tube_info} → Consultar tabla NMP"
                else:
                    record.calculated_result = "Datos incompletos"
                    
            elif record.method_type == 'qualitative' and record.result_qualitative:
                # PARA CUALITATIVO
                qualitative_map = {
                    'positive': 'Positivo',
                    'negative': 'Negativo',
                    'growth': 'Crecimiento',
                    'no_growth': 'Sin Crecimiento'
                }
                record.calculated_result = qualitative_map.get(record.result_qualitative, record.result_qualitative)
            else:
                record.calculated_result = False
    
    @api.onchange('method_type')
    def _onchange_method_type(self):
        """Limpiar campos no relevantes según el tipo de método"""
        if self.method_type == 'ufc':
            self.positive_tubes = False
            self.total_tubes = 3
            self.nmp_result = False
            self.result_qualitative = False
        elif self.method_type == 'nmp':
            self.ufc_count = False
            self.result_qualitative = False
        elif self.method_type == 'qualitative':
            self.ufc_count = False
            self.positive_tubes = False
            self.total_tubes = False
            self.nmp_result = False