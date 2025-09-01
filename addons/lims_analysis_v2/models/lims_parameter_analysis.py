from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsParameterAnalysisV2(models.Model):
    _name = 'lims.parameter.analysis.v2'
    _description = 'Parámetros de Análisis con Resultados v2'
    _rec_name = 'name'
    _order = 'sequence, name'

    # ===============================================
    # === RELACIÓN PRINCIPAL ===
    # ===============================================
    analysis_id = fields.Many2one(
        'lims.analysis.v2',
        string='Análisis',
        required=True,
        ondelete='cascade'
    )
    
    reception_date = fields.Date(
        string='Fecha de Recepción',
        related='analysis_id.reception_date',
        readonly=True,
        store=True
    )

    sample_reception_id = fields.Many2one(
        'lims.sample.reception',
        string='Muestra Recibida',
        related='analysis_id.sample_reception_id',
        readonly=True,
        store=True
    )

    # ===============================================
    # === INFORMACIÓN DEL PARÁMETRO ===
    # ===============================================
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro Original',
        readonly=True
    )
    name = fields.Char(
        string='Nombre del Parámetro',
        required=True
    )
    method = fields.Char(string='Método')
    microorganism = fields.Char(string='Análisis')
    unit = fields.Char(string='Unidad')
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], string='Categoría')
    sequence = fields.Integer(string='Secuencia', default=10)
    
    # ===============================================
    # === CONFIGURACIÓN DE ANÁLISIS ===
    # ===============================================
    result_type = fields.Selection([
        ('qualitative', 'Cualitativo'),
        ('quantitative', 'Cuantitativo')
    ], string='Tipo de Resultado', default='quantitative', required=True)
    
    # ===============================================
    # === FECHAS Y ESTADO ===
    # ===============================================
    analysis_start_date = fields.Date(
        string='Fecha Inicio de Análisis',
        default=lambda self: self._get_reception_date_default(),
        help='Fecha en que se inició el análisis de este parámetro'
    )
    analysis_commitment_date = fields.Date(
        string='Fecha Compromiso de Análisis',
        help='Fecha comprometida para la entrega del resultado'
    )
    analysis_date = fields.Date(string='Fecha de Análisis')
    
    @api.model
    def _get_reception_date_default(self):
        """Obtener fecha de recepción como default"""
        # Si tenemos analysis_id en contexto
        if self.env.context.get('default_analysis_id'):
            analysis = self.env['lims.analysis.v2'].browse(
                self.env.context['default_analysis_id']
            )
            if analysis.reception_date:
                return analysis.reception_date
        return fields.Date.context_today(self)

    @api.onchange('analysis_id')
    def _onchange_analysis_id_reception_date(self):
        """Actualizar fecha de inicio cuando cambie el análisis"""
        if self.analysis_id and self.analysis_id.reception_date:
            self.analysis_start_date = self.analysis_id.reception_date
    
    # Estados del análisis
    analysis_status = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string='Estado del Análisis', default='draft')
    
    # ===============================================
    # === RESPONSABLES ===
    # ===============================================
    analyst_names = fields.Char(
        string='Analistas Responsables',
        help='Firma (Iniciales separadas por comas)'
    )
    
    # ===============================================
    # === RESULTADO PRINCIPAL ===
    # ===============================================
    result_value = fields.Char(
        string='Resultado',
        help='Resultado principal del análisis',
        placeholder='Ej: 7.2, Negativo, 1.2 x 10² UFC/g, < 0.01 mg/kg'
    )
    result_complete = fields.Char(
        string='Resultado Completo',
        compute='_compute_result_complete',
        store=True,
        help='Resultado con unidad incluida'
    )
    
    # ===============================================
    # === CAMPOS ESPECÍFICOS DE RESULTADO ===
    # ===============================================
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
    
    result_quantitative_text = fields.Char(
        string='Resultado Cuantitativo',
        help='Resultado cuantitativo como texto libre para mayor flexibilidad',
        placeholder='Ej: 1.2 x 10² UFC/g, < 0.01 mg/kg, 7.2 ± 0.1 pH'
    )

    # Para resultados cualitativos
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
    
    # Unidades para resultados
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
    
    qualitative_unit_selection = fields.Selection([
        ('ausencia_presencia_25g', 'Ausencia/Presencia en 25g'),
        ('ausencia_presencia_100ml', 'Ausencia/Presencia en 100mL'),
        ('ausencia_presencia_10g', 'Ausencia/Presencia en 10g'),
        ('ausencia_presencia_1g', 'Ausencia/Presencia en 1g'),
        ('detectado_no_detectado', 'Detectado/No Detectado'),
        ('positivo_negativo', 'Positivo/Negativo'),
        ('custom', 'Otra unidad (especificar)')
    ], string='Unidad/Base para Cualitativos')
    
    qualitative_custom_unit = fields.Char(
        string='Unidad Personalizada',
        help='Especificar unidad personalizada para resultado cualitativo'
    )
    
    # Límites de detección
    below_detection_limit = fields.Boolean(
        string='< Límite de Detección',
        help='Resultado por debajo del límite de detección'
    )
    above_quantification_limit = fields.Boolean(
        string='> Límite de Cuantificación',
        help='Resultado por encima del límite de cuantificación'
    )
    
    # Estado mejorado con checkbox
    analysis_status_checkbox = fields.Selection([
        ('sin_procesar', 'Sin Procesar'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ], string='Estado del Análisis', default='sin_procesar', required=True)

    # ===============================================
    # === ESTADO DE REPORTE ===
    # ===============================================
    report_status = fields.Selection([
        ('draft', 'En Proceso'),
        ('ready', 'Listo para Reporte'),
    ], string='Estado para Reporte', 
       default='draft',
       help='Indica si este parámetro está listo para incluir en reportes')
    
    # ===============================================
    # === PROCESOS ANALÍTICOS REQUERIDOS ===
    # ===============================================
    requires_pre_enrichment = fields.Boolean(
        string='Requiere Pre-enriquecimiento',
        default=False,
        help='Marcar si este parámetro requiere proceso de pre-enriquecimiento'
    )
    requires_selective_enrichment = fields.Boolean(
        string='Requiere Enriquecimiento Selectivo',
        default=False,
        help='Marcar si este parámetro requiere enriquecimiento selectivo'
    )
    requires_confirmation = fields.Boolean(
        string='Requiere Confirmación',
        default=False,
        help='Marcar si este parámetro requiere pruebas de confirmación'
    )
    requires_ph_adjustment = fields.Boolean(
        string='Requiere Ajuste de pH',
        default=False,
        help='Marcar si este parámetro requiere ajuste de pH'
    )
    
    # ===============================================
    # === CAMPOS DE AMBIENTE DE TRABAJO ===
    # ===============================================
    # Pre-enriquecimiento
    pre_enrichment_environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento')
    pre_enrichment_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]",
        help='Equipo específico utilizado para el pre-enriquecimiento'
    )
    pre_enrichment_processing_date = fields.Date(string='Fecha de Procesamiento')
    pre_enrichment_processing_time = fields.Char(string='Hora de Procesamiento', help='Formato HH:MM')
    
    # Enriquecimiento selectivo
    selective_enrichment_environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento Selectivo')
    selective_enrichment_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Selectivo',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]"
    )
    selective_enrichment_processing_date = fields.Date(string='Fecha de Procesamiento Selectivo')
    selective_enrichment_processing_time = fields.Char(string='Hora de Procesamiento Selectivo', help='Formato HH:MM')
    
    # Confirmación
    confirmation_environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento de Confirmación')
    confirmation_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Confirmación',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]"
    )
    confirmation_processing_date = fields.Date(string='Fecha de Procesamiento de Confirmación')
    confirmation_processing_time = fields.Char(string='Hora de Procesamiento de Confirmación', help='Formato HH:MM')
    
    # Análisis cuantitativo
    quantitative_environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento Cuantitativo')
    quantitative_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Cuantitativo',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]"
    )
    quantitative_processing_date = fields.Date(string='Fecha de Procesamiento Cuantitativo')
    quantitative_processing_time = fields.Char(string='Hora de Procesamiento Cuantitativo', help='Formato HH:MM')
    
    # Análisis cualitativo
    qualitative_environment = fields.Selection([
        ('ambiente_aseptico', 'Ambiente aséptico'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
        ('no_aplica', 'N/A'),
    ], string='Ambiente de Procesamiento Cualitativo')
    qualitative_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Cualitativo',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]"
    )
    qualitative_processing_date = fields.Date(string='Fecha de Procesamiento Cualitativo')
    qualitative_processing_time = fields.Char(string='Hora de Procesamiento Cualitativo', help='Formato HH:MM')
    
    # ===============================================
    # === CAMPOS DE SETS DE MEDIOS ===
    # ===============================================
    pre_enrichment_set_id = fields.Many2one(
        'lims.media.set',
        string='Set de Pre-enriquecimiento',
        domain=[]
    )

    selective_enrichment_set_id = fields.Many2one(
        'lims.media.set',
        string='Set de Enriquecimiento Selectivo',
        domain=[]
    )

    quantitative_set_id = fields.Many2one(
        'lims.media.set',
        string='Set Cuantitativo',
        domain=[]
    )

    qualitative_set_id = fields.Many2one(
        'lims.media.set',
        string='Set Cualitativo',
        domain=[]
    )

    confirmation_set_id = fields.Many2one(
        'lims.media.set',
        string='Set de Confirmación',
        domain=[]
    )

    # ===============================================
    # === OBSERVACIONES ===
    # ===============================================
    analyst_notes = fields.Text(
        string='Observaciones del Analista',
        help='Notas técnicas sobre el análisis realizado'
    )
    
    # ===============================================
    # === RELACIONES ONE2MANY ===
    # ===============================================
    media_ids = fields.One2many(
        'lims.analysis.media.v2',
        'parameter_analysis_id',
        string='Medios y Reactivos Utilizados'
    )
    raw_dilution_data_ids = fields.One2many(
        'lims.raw.dilution.data.v2',
        'parameter_analysis_id',
        string='Datos Crudos de Diluciones'
    )
    confirmation_results_ids = fields.One2many(
        'lims.confirmation.result.v2',
        'parameter_analysis_id',
        string='Resultados de Confirmación'
    )
    executed_qc_ids = fields.One2many(
        'lims.executed.quality.control.v2',
        'parameter_analysis_id',
        string='Controles de Calidad Ejecutados'
    )
    equipment_involved_ids = fields.One2many(
        'lims.equipment.involved.v2',
        'parameter_analysis_id',
        string='Equipos Involucrados'
    )
    pre_enrichment_media_ids = fields.One2many(
        'lims.analysis.media.v2',
        'parameter_analysis_id',
        string='Medios de Pre-enriquecimiento',
        domain=[('process_type', '=', 'pre_enrichment')]
    )

    selective_enrichment_media_ids = fields.One2many(
        'lims.analysis.media.v2',
        'parameter_analysis_id', 
        string='Medios de Enriquecimiento Selectivo',
        domain=[('process_type', '=', 'selective_enrichment')]
    )

    quantitative_media_ids = fields.One2many(
        'lims.analysis.media.v2',
        'parameter_analysis_id',
        string='Medios para Análisis Cuantitativo', 
        domain=[('process_type', '=', 'quantitative')]
    )

    qualitative_media_ids = fields.One2many(
        'lims.analysis.media.v2',
        'parameter_analysis_id',
        string='Medios para Análisis Cualitativo',
        domain=[('process_type', '=', 'qualitative')]
    )

    confirmation_media_ids = fields.One2many(
        'lims.analysis.media.v2', 
        'parameter_analysis_id',
        string='Medios de Confirmación',
        domain=[('process_type', '=', 'confirmation')]
    )
    # ===============================================
    # === CAMPOS COMPUTADOS ===
    # ===============================================
    dilution_calculations = fields.Text(
        string='Cálculos Informativos',
        compute='_compute_dilution_calculations',
        help='Cálculos informativos basados en datos crudos (solo referencia)'
    )
    
    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('result_value')
    def _compute_result_complete(self):
        """Mostrar solo el resultado sin unidad en la lista"""
        for record in self:
            record.result_complete = record.result_value or ''
    
    @api.depends('raw_dilution_data_ids.ufc_count')
    def _compute_dilution_calculations(self):
        """Mostrar SOLO cálculos informativos (NO actualiza resultado automáticamente)"""
        for record in self:
            if record.raw_dilution_data_ids:
                calculations = []
                
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
    
    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('result_unit_selection')
    def _onchange_result_unit_selection(self):
        """Limpiar unidad personalizada si no se selecciona 'custom'"""
        if self.result_unit_selection != 'custom':
            self.custom_unit = False
    
    @api.onchange('result_numeric', 'result_unit', 'result_quantitative_text')
    def _onchange_numeric_result(self):
        """Auto-completar resultado principal cuando se llena cuantitativo + unidad"""
        # Priorizar el campo de texto si está lleno
        if self.result_quantitative_text:
            self.result_value = self.result_quantitative_text
        elif self.result_numeric and self.result_unit:
            if self.result_unit.lower() in ['ph', 'unidades de ph']:
                self.result_value = f"{self.result_numeric:.1f} {self.result_unit}"
            else:
                self.result_value = f"{self.result_numeric} {self.result_unit}"
    
    @api.onchange('result_quantitative_text')
    def _onchange_quantitative_text_result(self):
        """Auto-completar resultado principal con resultado cuantitativo de texto"""
        if self.result_quantitative_text:
            self.result_value = self.result_quantitative_text

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
            self.result_quantitative_text = False  
            self.below_detection_limit = False
            self.above_quantification_limit = False
            self.result_unit_selection = False
            self.custom_unit = False
            # Limpiar datos de diluciones
            self.raw_dilution_data_ids = [(5, 0, 0)]
        elif self.result_type == 'quantitative':
            # Limpiar campos cualitativos
            self.result_qualitative = False

    @api.onchange('result_type')
    def _onchange_result_type_cleanup(self):
        """Limpiar campos y medios cuando cambia el tipo de resultado"""
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
            # Limpiar medios cuantitativos
            self.quantitative_media_ids = [(5, 0, 0)]
            # Limpiar campos de ambiente cuantitativo
            self.quantitative_environment = False
            self.quantitative_equipment_id = False
            self.quantitative_processing_date = False
            self.quantitative_processing_time = False
            
        elif self.result_type == 'quantitative':
            # Limpiar campos cualitativos
            self.result_qualitative = False
            self.qualitative_unit_selection = False
            self.qualitative_custom_unit = False
            # Limpiar configuración de procesos cualitativos
            self.requires_pre_enrichment = False
            self.requires_selective_enrichment = False
            # Limpiar medios cualitativos
            self.pre_enrichment_media_ids = [(5, 0, 0)]
            self.selective_enrichment_media_ids = [(5, 0, 0)]
            self.qualitative_media_ids = [(5, 0, 0)]
            # Limpiar campos de ambiente cualitativo
            self.qualitative_environment = False
            self.qualitative_equipment_id = False
            self.qualitative_processing_date = False
            self.qualitative_processing_time = False
            # Limpiar campos de pre-enriquecimiento
            self.pre_enrichment_environment = False
            self.pre_enrichment_equipment_id = False
            self.pre_enrichment_processing_date = False
            self.pre_enrichment_processing_time = False
            # Limpiar campos de enriquecimiento selectivo
            self.selective_enrichment_environment = False
            self.selective_enrichment_equipment_id = False
            self.selective_enrichment_processing_date = False
            self.selective_enrichment_processing_time = False

    @api.onchange('qualitative_unit_selection')
    def _onchange_qualitative_unit_selection(self):
        """Limpiar unidad personalizada si no se selecciona 'custom'"""
        if self.qualitative_unit_selection != 'custom':
            self.qualitative_custom_unit = False
    
    # ===============================================
    # === MÉTODOS DE ACCIÓN ===
    # ===============================================
    def action_copy_qc_from_template(self):
        """Copiar controles de calidad desde la plantilla del parámetro"""
        if not self.parameter_id or not self.parameter_id.quality_control_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Controles en Plantilla',
                    'message': 'El parámetro no tiene controles de calidad definidos en su plantilla',
                    'type': 'warning',
                }
            }
        
        # Copiar controles desde la plantilla
        new_controls = 0
        for qc in self.parameter_id.quality_control_ids:
            # Verificar si ya existe
            existing = self.executed_qc_ids.filtered(
                lambda x: x.qc_type_id.id == qc.control_type_id.id
            )
            
            if not existing:
                self.env['lims.executed.quality.control.v2'].create({
                    'parameter_analysis_id': self.id,
                    'qc_type_id': qc.control_type_id.id,
                    'expected_result': qc.expected_result,
                    'control_status': 'pending',
                    'sequence': qc.sequence,
                    'notes': qc.notes or '',
                })
                new_controls += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Controles Copiados',
                'message': f'Se agregaron {new_controls} controles de calidad desde la plantilla',
                'type': 'success',
            }
        }
    
    @api.onchange('analysis_status_checkbox')
    def _onchange_analysis_status_checkbox(self):
        """Sincronizar con el campo analysis_status original si existe"""
        # Mapeo entre checkbox y estado original
        status_mapping = {
            'sin_procesar': 'draft',
            'en_proceso': 'in_progress', 
            'finalizado': 'completed'
        }
        
        if self.analysis_status_checkbox:
            mapped_status = status_mapping.get(self.analysis_status_checkbox)
            if mapped_status:
                self.analysis_status = mapped_status

    @api.onchange('result_value', 'analysis_status_checkbox')
    def _onchange_check_report_ready(self):
        """Detectar automáticamente cuando el parámetro está listo para reporte"""
        if (self.result_value and 
            self.result_value.strip() and 
            self.analysis_status_checkbox == 'finalizado'):
            # Cambiar a 'ready' si estaba en 'draft'
            if self.report_status == 'draft':
                self.report_status = 'ready'
        else:
            # Siempre volver a 'draft' si no cumple las condiciones
            self.report_status = 'draft'

    @api.model
    def _get_reception_date_default(self):
        """Obtener fecha de recepción como default"""
        # Si tenemos analysis_id en contexto
        if self.env.context.get('default_analysis_id'):
            analysis = self.env['lims.analysis.v2'].browse(
                self.env.context['default_analysis_id']
            )
            if analysis.reception_date:
                return analysis.reception_date
        return fields.Date.context_today(self)

    @api.onchange('analysis_id')
    def _onchange_analysis_id_reception_date(self):
        """Actualizar fecha de inicio cuando cambie el análisis"""
        if self.analysis_id and self.analysis_id.reception_date:
            self.analysis_start_date = self.analysis_id.reception_date

    def action_load_media_from_set(self, process_type):
        """Cargar medios desde un set específico"""
        # Buscar sets disponibles para este proceso
        available_sets = self.env['lims.media.set'].search([
            ('process_type', '=', process_type),
            ('active', '=', True)
        ])
        
        if not available_sets:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Sets Disponibles',
                    'message': f'No hay sets de medios configurados para {process_type}',
                    'type': 'warning',
                }
            }
        
        # Si solo hay un set, cargarlo directamente
        if len(available_sets) == 1:
            return self._load_media_set(available_sets[0])
        
        # Si hay múltiples sets, mostrar wizard de selección
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar Set de Medios',
            'res_model': 'lims.media.set.selector.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parameter_analysis_id': self.id,
                'default_process_type': process_type,
                'default_available_set_ids': available_sets.ids
            }
        }

    def _load_media_set(self, media_set):
        """Cargar medios desde un set específico"""
        new_media = 0
        
        for set_line in media_set.media_line_ids:
            # Verificar si ya existe este medio para este proceso
            existing = self.media_ids.filtered(
                lambda x: x.process_type == media_set.process_type and 
                        x.culture_media_name == set_line.culture_media_id.name
            )
            
            if not existing:
                self.env['lims.analysis.media.v2'].create({
                    'parameter_analysis_id': self.id,
                    'process_type': media_set.process_type,
                    'media_source': 'internal',
                    'culture_media_name': set_line.culture_media_id.name,
                    'media_usage': set_line.media_usage,
                    'requires_incubation': True,
                    'preparation_notes': set_line.notes or '',
                    'sequence': set_line.sequence,
                })
                new_media += 1
        
        # Incrementar contador de uso
        media_set.times_used += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Set Cargado',
                'message': f'Se cargaron {new_media} medios desde "{media_set.name}"',
                'type': 'success',
            }
        }

    # Métodos específicos para cada proceso
    def action_load_pre_enrichment_set(self):
        return self.action_load_media_from_set('pre_enrichment')

    def action_load_selective_enrichment_set(self):
        return self.action_load_media_from_set('selective_enrichment')

    def action_load_quantitative_set(self):
        return self.action_load_media_from_set('quantitative')

    def action_load_qualitative_set(self):
        return self.action_load_media_from_set('qualitative')

    def action_load_confirmation_set(self):
        return self.action_load_media_from_set('confirmation')
    
    # ===============================================
    # === ONCHANGE PARA SETS DE MEDIOS ===
    # ===============================================
    @api.onchange('pre_enrichment_set_id')
    def _onchange_pre_enrichment_set_id(self):
        if self.pre_enrichment_set_id:
            self._load_media_from_set('pre_enrichment', self.pre_enrichment_set_id, 'pre_enrichment_media_ids')

    @api.onchange('selective_enrichment_set_id')
    def _onchange_selective_enrichment_set_id(self):
        if self.selective_enrichment_set_id:
            self._load_media_from_set('selective_enrichment', self.selective_enrichment_set_id, 'selective_enrichment_media_ids')

    @api.onchange('quantitative_set_id')
    def _onchange_quantitative_set_id(self):
        if self.quantitative_set_id:
            self._load_media_from_set('quantitative', self.quantitative_set_id, 'quantitative_media_ids')

    @api.onchange('qualitative_set_id')
    def _onchange_qualitative_set_id(self):
        if self.qualitative_set_id:
            self._load_media_from_set('qualitative', self.qualitative_set_id, 'qualitative_media_ids')

    @api.onchange('confirmation_set_id')
    def _onchange_confirmation_set_id(self):
        if self.confirmation_set_id:
            self._load_media_from_set('confirmation', self.confirmation_set_id, 'confirmation_media_ids')

    def _load_media_from_set(self, process_type, media_set, field_name):
        """Método auxiliar para cargar medios desde un set"""
        # Limpiar medios actuales
        current_media = getattr(self, field_name)
        current_media.unlink()
        
        # Crear nuevos medios desde el set
        media_lines = []
        for set_line in media_set.media_line_ids:
            media_lines.append((0, 0, {
                'process_type': process_type,
                'media_source': 'internal',
                'culture_media_name': set_line.culture_media_id.name,
                'media_usage': set_line.media_usage,
                'preparation_notes': set_line.notes or '',
                'sequence': set_line.sequence,
                'requires_incubation': True,  # Por defecto activado
            }))
        
        if media_lines:
            setattr(self, field_name, media_lines)
            # Incrementar contador de uso
            media_set.sudo().write({'times_used': media_set.times_used + 1})