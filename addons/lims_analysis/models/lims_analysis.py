from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging
from . import lims_analysis_report

_logger = logging.getLogger(__name__)

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _rec_name = 'display_name'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia',
        related='sample_reception_id.sample_id.custody_chain_id',
        readonly=True,
        store=True
    )
    custody_chain_code = fields.Char(
        string='Código de Cadena',
        related='sample_reception_id.sample_id.custody_chain_id.custody_chain_code',
        readonly=True,
        store=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sample_reception_id.sample_id.custody_chain_id.cliente_id',
        readonly=True,
        store=True
    )
    reception_date = fields.Date(
        string='Fecha de Recepción',
        related='sample_reception_id.reception_date',  
        readonly=True,
        store=True
    )
    display_name = fields.Char(
        string='Nombre del Análisis',
        compute='_compute_display_name',
        store=True
    )
    report_status_summary = fields.Char(
        string='Estado de Reporte',
        compute='_compute_report_status_summary',
        help='Resumen del estado de reporte de los parámetros'
    )
    # Fechas
    analysis_start_date = fields.Date(
        string='Fecha de Inicio',
        default=fields.Date.context_today
    )
    analysis_end_date = fields.Date(
        string='Fecha de Finalización'
    )
    analysis_commitment_date = fields.Date(
        string='Fecha Compromiso',
        help='Fecha comprometida para entregar resultados'
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
    has_ready_parameters = fields.Boolean(
        string='Tiene Parámetros Listos',
        compute='_compute_report_readiness',
        store=True,
        help='Al menos un parámetro está listo para reporte preliminar'
    )
    all_parameters_ready = fields.Boolean(
        string='Todos los Parámetros Listos',
        compute='_compute_report_readiness',
        store=True,
        help='Todos los parámetros están listos para reporte final'
    )
    ready_parameters_count = fields.Integer(
        string='Parámetros Listos',
        compute='_compute_report_readiness',
        store=True,
        help='Cantidad de parámetros listos para reporte'
    )
    total_parameters_count = fields.Integer(
        string='Total Parámetros',
        compute='_compute_report_readiness',
        store=True,
        help='Cantidad total de parámetros en este análisis'
    )
    signature_state = fields.Selection([
        ('not_signed', 'Sin Firmar'),
        ('signed', 'Firmada'),
        ('cancelled', 'Firma Cancelada')
    ], string='Estado de Firma', default='not_signed', tracking=True)
    sample_signature_name = fields.Char(
        string='Firmado por',
        readonly=True,
        tracking=True
    )
    sample_signature_position = fields.Char(
        string='Cargo del Firmante',
        readonly=True
    )
    sample_signature_date = fields.Datetime(
        string='Fecha de Firma',
        readonly=True,
        tracking=True
    )
    # Campos de cancelación
    signature_cancelled_by = fields.Char(
        string='Firma Cancelada por',
        readonly=True,
        tracking=True
    )
    signature_cancelled_date = fields.Datetime(
        string='Fecha de Cancelación',
        readonly=True
    )
    signature_cancellation_reason = fields.Text(
        string='Motivo de Cancelación',
        readonly=True
    )
    can_cancel_signature = fields.Boolean(
        string='Puede Cancelar Firma',
        compute='_compute_can_cancel_signature'
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

    @api.depends('parameter_analysis_ids.report_status')
    def _compute_report_readiness(self):
        """Calcular disponibilidad para reportes usando ORM nativo"""
        for analysis in self:
            # Contar parámetros usando filtros nativos
            all_params = analysis.parameter_analysis_ids
            ready_params = all_params.filtered(lambda p: p.report_status == 'ready')
            
            analysis.total_parameters_count = len(all_params)
            analysis.ready_parameters_count = len(ready_params)
            analysis.has_ready_parameters = len(ready_params) > 0
            analysis.all_parameters_ready = (
                len(ready_params) == len(all_params) 
                if all_params else False
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para copiar parámetros y controles de calidad desde la muestra"""
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
                    
                    # Crear el parámetro de análisis
                    param_analysis = self.env['lims.parameter.analysis'].create({
                        'analysis_id': record.id,
                        'parameter_id': param.id,
                        'name': param.name or 'Sin nombre',
                        'method': param.method or '',
                        'microorganism': param.microorganism or '',
                        'unit': param.unit or '',
                        'category': param.category or 'other',
                        'sequence': param.id,  # Usar el ID como secuencia temporal
                    })
                    
                    # 🆕 COPIAR CONTROLES DE CALIDAD DEL PARÁMETRO PLANTILLA
                    if param.quality_control_ids:
                        print(f"DEBUG: Copiando {len(param.quality_control_ids)} controles de calidad")
                        
                        for qc in param.quality_control_ids:
                            self.env['lims.executed.quality.control'].create({
                                'parameter_analysis_id': param_analysis.id,
                                'qc_type_id': qc.control_type_id.id,
                                'expected_result': qc.expected_result,
                                'control_status': 'pending',
                                'sequence': qc.sequence,
                                'notes': qc.notes or '',
                            })
                    
            else:
                print(f"DEBUG: No se encontró muestra para el análisis {record.id}")
        
        return records
    
    def action_print_preliminary_report_for_chain_no_auto_mark(self):
        """Crear e imprimir reporte preliminar SIN marcar como reportado"""
        custody_chain = self.custody_chain_id
        
        # Buscar todos los análisis de la cadena con parámetros listos
        analyses = self.env['lims.analysis'].search([
            ('custody_chain_id', '=', custody_chain.id),
            ('has_ready_parameters', '=', True)
        ])
        
        if not analyses:
            raise UserError('No hay análisis con parámetros listos en esta cadena.')
        
        # Crear reporte preliminar
        report = self.env['lims.analysis.report'].create({
            'custody_chain_id': custody_chain.id,
            'analysis_ids': [(6, 0, analyses.ids)],
            'report_type': 'preliminary',
            'report_state': 'authorized',
            'quality_signature_name': self.env.user.name,
            'quality_signature_date': fields.Datetime.now(),
        })
        
        # NO MARCAR COMO REPORTADO - control manual
        
        # Generar PDF
        return self.env.ref('lims_analysis.action_report_analysis_results').report_action(report)
    
    def action_print_final_report_for_chain_no_auto_mark(self):
        """Crear e imprimir reporte final SIN marcar como reportado"""
        custody_chain = self.custody_chain_id
        
        # Buscar todos los análisis de la cadena completamente terminados
        analyses = self.env['lims.analysis'].search([
            ('custody_chain_id', '=', custody_chain.id),
            ('all_parameters_ready', '=', True)
        ])
        
        if not analyses:
            raise UserError('No hay análisis completamente terminados en esta cadena.')
        
        # Crear reporte final
        report = self.env['lims.analysis.report'].create({
            'custody_chain_id': custody_chain.id,
            'analysis_ids': [(6, 0, analyses.ids)],
            'report_type': 'final',
            'report_state': 'authorized',
            'quality_signature_name': self.env.user.name,
            'quality_signature_date': fields.Datetime.now(),
        })
        
        # NO MARCAR COMO REPORTADO - control manual
        
        # Generar PDF
        return self.env.ref('lims_analysis.action_report_analysis_results').report_action(report)
    
    @api.model
    def action_mass_print_preliminary_report(self, analysis_ids):
        """Acción masiva para reportes preliminares"""
        analyses = self.browse(analysis_ids)
        
        # Verificar que hay parámetros listos
        if not any(analysis.has_ready_parameters for analysis in analyses):
            raise UserError('Ningún análisis seleccionado tiene parámetros listos para reportar.')
        
        # Agrupar por cadena de custodia
        chains_processed = set()
        reports_generated = []
        
        for analysis in analyses:
            if analysis.custody_chain_id.id not in chains_processed and analysis.has_ready_parameters:
                # Crear reporte para esta cadena
                report = analysis.action_print_preliminary_report_for_chain_no_auto_mark()
                reports_generated.append(report)
                chains_processed.add(analysis.custody_chain_id.id)
        
        if len(reports_generated) == 1:
            return reports_generated[0]
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Reportes Generados',
                    'message': f'Se generaron {len(reports_generated)} reportes preliminares.',
                    'type': 'success',
                }
            }
        
    @api.model
    def action_mass_print_final_report(self, analysis_ids):
        """Acción masiva para reportes finales"""
        analyses = self.browse(analysis_ids)
        
        # Verificar que hay análisis completos
        if not any(analysis.all_parameters_ready for analysis in analyses):
            raise UserError('Ningún análisis seleccionado está completamente terminado.')
        
        # Agrupar por cadena de custodia
        chains_processed = set()
        reports_generated = []
        
        for analysis in analyses:
            if analysis.custody_chain_id.id not in chains_processed and analysis.all_parameters_ready:
                # Crear reporte para esta cadena
                report = analysis.action_print_final_report_for_chain_no_auto_mark()
                reports_generated.append(report)
                chains_processed.add(analysis.custody_chain_id.id)
        
        if len(reports_generated) == 1:
            return reports_generated[0]
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Reportes Generados',
                    'message': f'Se generaron {len(reports_generated)} reportes finales.',
                    'type': 'success',
                }
            }
        
    @api.model
    def action_mass_mark_as_reported(self, analysis_ids):
        """Acción masiva para marcar como reportado"""
        analyses = self.browse(analysis_ids)
        
        total_marked = 0
        for analysis in analyses:
            ready_params = analysis.parameter_analysis_ids.filtered(
                lambda p: p.report_status == 'ready'
            )
            if ready_params:
                ready_params.write({'report_status': 'reported'})
                total_marked += len(ready_params)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Parámetros Marcados',
                'message': f'Se marcaron {total_marked} parámetros como reportados.',
                'type': 'success',
            }
        }
    
    @api.depends('parameter_analysis_ids.report_status')
    def _compute_report_status_summary(self):
        """Calcular resumen del estado de reporte"""
        for analysis in self:
            params = analysis.parameter_analysis_ids
            if not params:
                analysis.report_status_summary = "Sin parámetros"
                continue
                
            ready_count = len(params.filtered(lambda p: p.report_status == 'ready'))
            reported_count = len(params.filtered(lambda p: p.report_status == 'reported'))
            draft_count = len(params.filtered(lambda p: p.report_status == 'draft'))
            
            status_parts = []
            if reported_count > 0:
                status_parts.append(f"✅ {reported_count} reportados")
            if ready_count > 0:
                status_parts.append(f"📋 {ready_count} listos")
            if draft_count > 0:
                status_parts.append(f"⏳ {draft_count} en proceso")
                
            analysis.report_status_summary = " | ".join(status_parts) if status_parts else "Todos en borrador"

    @api.depends('signature_state')
    def _compute_can_cancel_signature(self):
        """Por ahora todos pueden cancelar - cambiar cuando implementes grupos"""
        for record in self:
            # TODO: Cambiar por grupos cuando esté listo
            # can_cancel = self.env.user.has_group('lims_analysis.group_quality_manager')
            can_cancel = True  # Por ahora todos pueden cancelar
            record.can_cancel_signature = can_cancel and record.signature_state == 'signed'

    def action_sign_sample(self):
        """Firmar muestra - versión simple"""
        # Verificar que hay parámetros finalizados
        finalized_params = self.parameter_analysis_ids.filtered(
            lambda p: p.analysis_status_checkbox == 'finalizado'
        )
        
        if not finalized_params:
            raise UserError('No hay parámetros finalizados para firmar.')
        
        # Firmar directamente por ahora
        self.write({
            'signature_state': 'signed',
            'sample_signature_name': self.env.user.name,
            'sample_signature_position': 'Analista',  # Default por ahora
            'sample_signature_date': fields.Datetime.now(),
        })
        
        # Marcar parámetros como listos
        finalized_params.write({'report_status': 'ready'})
        
        _logger.info(f"Muestra {self.sample_code} firmada por {self.env.user.name}. "
                    f"{len(finalized_params)} parámetros marcados como listos para reporte.")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Muestra Firmada',
                'message': f'La muestra {self.sample_code} ha sido firmada exitosamente.',
                'type': 'success',
            }
        }
    
    def action_cancel_signature(self):
        """Cancelar firma - versión simple"""
        self.write({
            'signature_state': 'cancelled',
            'signature_cancelled_by': self.env.user.name,
            'signature_cancelled_date': fields.Datetime.now(),
            'signature_cancellation_reason': 'Cancelación manual'  # Default por ahora
        })
        
        # Volver parámetros a estado draft
        self.parameter_analysis_ids.filtered(
            lambda p: p.report_status == 'ready'
        ).write({'report_status': 'draft'})
        
        _logger.info(f"Firma de muestra {self.sample_code} cancelada por {self.env.user.name}.")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Firma Cancelada',
                'message': f'La firma de la muestra {self.sample_code} ha sido cancelada.',
                'type': 'warning',
            }
        }

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
    
    # 🆕 CAMPOS PARA PROCESOS ANALÍTICOS
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

    # 🆕 CAMPOS PARA PRE-ENRIQUECIMIENTO
    pre_enrichment_environment = fields.Selection([
        ('triangulo_esteril', 'Triángulo Estéril'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
    ], string='Ambiente de Procesamiento')

    pre_enrichment_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]",
        help='Equipo específico utilizado para el pre-enriquecimiento'
    )

    # Fechas de procesamiento
    pre_enrichment_processing_date = fields.Date(
        string='Fecha de Procesamiento'
    )

    pre_enrichment_processing_time = fields.Char(
        string='Hora de Procesamiento',
        help='Formato HH:MM'
    )

    # Medios y reactivos

    pre_enrichment_media_ids = fields.One2many(
        'lims.pre.enrichment.media',
        'parameter_analysis_id',
        string='Medios y Reactivos Utilizados'
    )

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
    
    # CAMPOS PARA ENRIQUECIMIENTO SELECTIVO
    selective_enrichment_environment = fields.Selection([
        ('triangulo_esteril', 'Triángulo Estéril'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
    ], string='Ambiente de Procesamiento Selectivo')

    selective_enrichment_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Selectivo',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]",
        help='Equipo específico utilizado para el enriquecimiento selectivo'
    )

    # Fechas de procesamiento selectivo
    selective_enrichment_processing_date = fields.Date(
        string='Fecha de Procesamiento Selectivo'
    )

    selective_enrichment_processing_time = fields.Char(
        string='Hora de Procesamiento Selectivo',
        help='Formato HH:MM'
    )

    # Medios selectivos
    selective_enrichment_media_ids = fields.One2many(
        'lims.selective.enrichment.media',
        'parameter_analysis_id',
        string='Medios Selectivos Utilizados'
    )

    quantitative_media_ids = fields.One2many(
        'lims.quantitative.media',
        'parameter_analysis_id',
        string='Medios Utilizados para Cuantitativos'
    )

    # 🆕 CAMPOS PARA CONFIRMACIÓN
    confirmation_environment = fields.Selection([
        ('triangulo_esteril', 'Triángulo Estéril'),
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('mesa_trabajo', 'Mesa de Trabajo'),
    ], string='Ambiente de Procesamiento de Confirmación')

    confirmation_equipment_id = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Específico para Confirmación',
        domain="['|', ('equipment_type', '=', 'campana_flujo'), ('equipment_type', '=', 'campana_bioseguridad')]",
        help='Equipo específico utilizado para la confirmación'
    )

    # Fechas de procesamiento de confirmación
    confirmation_processing_date = fields.Date(
        string='Fecha de Procesamiento de Confirmación'
    )

    confirmation_processing_time = fields.Char(
        string='Hora de Procesamiento de Confirmación',
        help='Formato HH:MM'
    )

    # Medios de confirmación
    confirmation_media_ids = fields.One2many(
        'lims.confirmation.media',
        'parameter_analysis_id',
        string='Medios Utilizados para Confirmación'
    )
    
    # Resultados de confirmación (generados automáticamente)
    confirmation_results_ids = fields.One2many(
        'lims.confirmation.result',
        'parameter_analysis_id',
        string='Resultados de Confirmación'
    )

    analysis_status_checkbox = fields.Selection([
        ('sin_procesar', 'Sin Procesar'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ], string='Estado del Análisis', default='sin_procesar', required=True)

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

    result_complete = fields.Char(
        string='Resultado Completo',
        compute='_compute_result_complete',
        store=True,
        help='Resultado con unidad incluida'
    )

    report_status = fields.Selection([
        ('draft', 'En Proceso'),
        ('ready', 'Listo para Reporte'),
        ('reported', 'Ya Reportado')
    ], string='Estado para Reporte', 
       default='draft',
       help='Indica si este parámetro está listo para incluir en reportes')

    executed_qc_ids = fields.One2many(
        'lims.executed.quality.control',
        'parameter_analysis_id',
        string='Controles de Calidad Ejecutados'
    )

    def sync_confirmation_results(self):
        """Botón para sincronizar resultados de confirmación manualmente"""
        for record in self:
            try:
                # Limpiar resultados existentes
                existing_results = self.env['lims.confirmation.result'].search([
                    ('parameter_analysis_id', '=', record.id)
                ])
                if existing_results:
                    existing_results.unlink()
                
                # Crear nuevos resultados para cada medio de confirmación
                for media in record.confirmation_media_ids:
                    if media.culture_media_batch_id:
                        batch_display = f"{media.culture_media_batch_id.culture_media_id.name} (Lote: {media.culture_media_batch_id.batch_code})"
                        
                        self.env['lims.confirmation.result'].create({
                            'parameter_analysis_id': record.id,
                            'confirmation_media_id': media.id,
                            'batch_display_name': batch_display,
                        })
                
                # Mostrar mensaje de éxito
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sincronización Completada',
                        'message': f'Se crearon {len(record.confirmation_media_ids)} resultados de confirmación',
                        'type': 'success',
                    }
                }
                
            except Exception as e:
                # Mostrar mensaje de error
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error en Sincronización',
                        'message': f'Error: {str(e)}',
                        'type': 'warning',
                    }
                }

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
    
    # 🆕 MÉTODO ONCHANGE PARA AMBIENTE DE PROCESAMIENTO
    @api.onchange('pre_enrichment_environment')
    def _onchange_pre_enrichment_environment(self):
        """Limpiar equipo cuando cambia el ambiente"""
        if self.pre_enrichment_environment not in ['campana_flujo', 'campana_bioseguridad']:
            self.pre_enrichment_equipment_id = False
        
        # Actualizar dominio del equipo según el ambiente
        if self.pre_enrichment_environment == 'campana_flujo':
            domain = [('equipment_type', '=', 'campana_flujo')]
        elif self.pre_enrichment_environment == 'campana_bioseguridad':
            domain = [('equipment_type', '=', 'campana_bioseguridad')]
        else:
            domain = []
        
        return {'domain': {'pre_enrichment_equipment_id': domain}}

    @api.onchange('selective_enrichment_environment')
    def _onchange_selective_enrichment_environment(self):
        """Limpiar equipo cuando cambia el ambiente selectivo"""
        if self.selective_enrichment_environment not in ['campana_flujo', 'campana_bioseguridad']:
            self.selective_enrichment_equipment_id = False
        
        # Actualizar dominio del equipo según el ambiente
        if self.selective_enrichment_environment == 'campana_flujo':
            domain = [('equipment_type', '=', 'campana_flujo')]
        elif self.selective_enrichment_environment == 'campana_bioseguridad':
            domain = [('equipment_type', '=', 'campana_bioseguridad')]
        else:
            domain = []
        
        return {'domain': {'selective_enrichment_equipment_id': domain}}
    
    @api.onchange('confirmation_environment')
    def _onchange_confirmation_environment(self):
        """Limpiar equipo cuando cambia el ambiente de confirmación"""
        if self.confirmation_environment not in ['campana_flujo', 'campana_bioseguridad']:
            self.confirmation_equipment_id = False
        
        # Actualizar dominio del equipo según el ambiente
        if self.confirmation_environment == 'campana_flujo':
            domain = [('equipment_type', '=', 'campana_flujo')]
        elif self.confirmation_environment == 'campana_bioseguridad':
            domain = [('equipment_type', '=', 'campana_bioseguridad')]
        else:
            domain = []
        
        return {'domain': {'confirmation_equipment_id': domain}}
    
    @api.depends('result_value', 'result_unit_selection', 'custom_unit', 'result_qualitative', 'qualitative_unit_selection', 'qualitative_custom_unit', 'result_type')
    def _compute_result_complete(self):
        """Calcular resultado completo (valor + unidad)"""
        for record in self:
            if record.result_type == 'qualitative':
                # Para cualitativos: resultado + unidad cualitativa
                if record.result_value and record.qualitative_unit_selection:
                    unit_translations = {
                        'ausencia_presencia_25g': 'en 25g',
                        'ausencia_presencia_100ml': 'en 100mL',
                        'ausencia_presencia_10g': 'en 10g',
                        'ausencia_presencia_1g': 'en 1g',
                        'detectado_no_detectado': '',
                        'positivo_negativo': '',
                        'custom': record.qualitative_custom_unit or ''
                    }
                    unit = unit_translations.get(record.qualitative_unit_selection, '')
                    if unit:
                        record.result_complete = f"{record.result_value} {unit}".strip()
                    else:
                        record.result_complete = record.result_value
                else:
                    record.result_complete = record.result_value or ''
                    
            elif record.result_type == 'quantitative':
                # Para cuantitativos: resultado + unidad cuantitativa
                if record.result_value:
                    if record.result_unit_selection and record.result_unit_selection != 'custom':
                        # Unidades predefinidas
                        unit_translations = {
                            'ufc_g': 'UFC/g',
                            'ufc_ml': 'UFC/mL',
                            'nmp_g': 'NMP/g',
                            'nmp_ml': 'NMP/mL',
                            'ufc_100ml': 'UFC/100mL',
                            'nmp_100ml': 'NMP/100mL',
                            'mg_kg': 'mg/kg',
                            'mg_l': 'mg/L'
                        }
                        unit = unit_translations.get(record.result_unit_selection, '')
                        record.result_complete = f"{record.result_value} {unit}".strip()
                    elif record.result_unit_selection == 'custom' and record.custom_unit:
                        # Unidad personalizada
                        record.result_complete = f"{record.result_value} {record.custom_unit}".strip()
                    else:
                        record.result_complete = record.result_value
                else:
                    record.result_complete = ''
            else:
                record.result_complete = record.result_value or ''
    
    @api.onchange('result_qualitative', 'qualitative_unit_selection', 'qualitative_custom_unit')
    def _onchange_qualitative_result_with_unit(self):
        """Auto-completar resultado principal con resultado cualitativo + unidad"""
        if self.result_qualitative and self.qualitative_unit_selection:
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
            
            result_text = qualitative_map.get(self.result_qualitative, self.result_qualitative)
            
            # Agregar unidad
            unit_translations = {
                'ausencia_presencia_25g': 'en 25g',
                'ausencia_presencia_100ml': 'en 100mL',
                'ausencia_presencia_10g': 'en 10g',
                'ausencia_presencia_1g': 'en 1g',
                'detectado_no_detectado': '',
                'positivo_negativo': '',
                'custom': self.qualitative_custom_unit or ''
            }
            
            unit = unit_translations.get(self.qualitative_unit_selection, '')
            
            if unit:
                self.result_value = f"{result_text} {unit}".strip()
            else:
                self.result_value = result_text
    
    @api.onchange('qualitative_unit_selection')
    def _onchange_qualitative_unit_selection(self):
        """Limpiar unidad personalizada si no se selecciona 'custom'"""
        if self.qualitative_unit_selection != 'custom':
            self.qualitative_custom_unit = False
    
    @api.onchange('analysis_status_checkbox')
    def _onchange_analysis_status_checkbox(self):
        """Sincronizar con el campo analysis_status original si existe"""
        # Mapeo entre checkbox y estado original
        status_mapping = {
            'sin_procesar': 'pending',
            'en_proceso': 'in_progress', 
            'finalizado': 'completed'
        }
        
        if hasattr(self, 'analysis_status') and self.analysis_status_checkbox:
            mapped_status = status_mapping.get(self.analysis_status_checkbox)
            if mapped_status:
                self.analysis_status = mapped_status

    @api.onchange('result_value', 'analysis_status_checkbox')
    def _onchange_check_report_ready(self):
        """Detectar automáticamente cuando el parámetro está listo para reporte"""
        if (self.result_value and 
            self.result_value.strip() and 
            self.analysis_status_checkbox == 'finalizado'):
            # Solo cambiar a 'ready' si estaba en 'draft'
            if self.report_status == 'draft':
                self.report_status = 'ready'
        else:
            # Solo volver a 'draft' si no está reportado
            if self.report_status != 'reported':
                self.report_status = 'draft'

    def action_add_missing_qc(self):
        """Botón para agregar control de calidad manual"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agregar Control de Calidad',
            'res_model': 'lims.executed.quality.control',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parameter_analysis_id': self.id,
                'default_control_status': 'pending'
            }
        }
    
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
                self.env['lims.executed.quality.control'].create({
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

    @api.depends('parameter_signature')
    def _compute_is_parameter_signed(self):
        """Verificar si el parámetro está firmado"""
        for param in self:
            param.is_parameter_signed = bool(param.parameter_signature)

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
    
    # 🆕 TIPO DE MÉTODO - SIN CUALITATIVO
    method_type = fields.Selection([
        ('ufc', 'Recuento en Placa (UFC)'),
        ('nmp', 'Número Más Probable (NMP)')
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
    
    # PARA RECUENTOS EN PLACA (UFC)
    ufc_count = fields.Integer(
        string='UFC Contadas',
        help='Número de colonias contadas en la placa'
    )
    
    # PARA MÉTODOS NMP
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
    
    # Observaciones específicas de esta dilución
    observations = fields.Text(
        string='Observaciones',
        help='Notas específicas sobre esta dilución',
        placeholder='Ej: Placas confluentes, Tubos con gas, etc...'
    )
    
    # CAMPO COMPUTADO SIMPLIFICADO
    calculated_result = fields.Char(
        string='Resultado Calculado',
        compute='_compute_calculated_result',
        store=True,
        help='Resultado según el tipo de método'
    )
    
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
    
    @api.onchange('method_type')
    def _onchange_method_type(self):
        """Limpiar campos no relevantes según el tipo de método"""
        if self.method_type == 'ufc':
            self.positive_tubes = False
            self.total_tubes = 3
            self.nmp_result = False
        elif self.method_type == 'nmp':
            self.ufc_count = False

# 🆕 MODELO EXTENDIDO PARA MEDIOS UTILIZADOS EN PRE-ENRIQUECIMIENTO
class LimsPreEnrichmentMedia(models.Model):
    _name = 'lims.pre.enrichment.media'
    _description = 'Medios Utilizados en Pre-enriquecimiento'
    _rec_name = 'display_name'
    _order = 'culture_media_batch_id, media_usage'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Lote del medio (siempre requerido)
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio',
        required=True,
        help='Lote específico del medio de cultivo utilizado'
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
    ], string='Uso del Medio', required=True, default='enriquecimiento')
    
    # CAMPOS DE INCUBACIÓN
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
    
    # NOTAS
    preparation_notes = fields.Text(
        string='Notas de Preparación',
        help='Instrucciones especiales, observaciones, etc.'
    )
    
    # CAMPOS CALCULADOS
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
    
    @api.depends('culture_media_batch_id', 'media_usage')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.culture_media_batch_id:
                media_name = record.culture_media_batch_id.culture_media_id.name
                batch_code = record.culture_media_batch_id.batch_code
                
                # Traducción del uso
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
                
                usage_display = usage_translations.get(record.media_usage, record.media_usage)
                name = f"{media_name} - {usage_display}"
                
                if batch_code:
                    name += f" (Lote: {batch_code})"
                    
                record.display_name = name
            else:
                record.display_name = "Medio sin especificar"
    
    @api.onchange('requires_incubation')
    def _onchange_requires_incubation(self):
        """Limpiar campos de incubación cuando no se requiere"""
        if not self.requires_incubation:
            self.incubation_equipment = False
            self.incubation_start_date = False
            self.incubation_start_time = False
            self.incubation_end_date = False
            self.incubation_end_time = False

class LimsSelectiveEnrichmentMedia(models.Model):
    _name = 'lims.selective.enrichment.media'
    _description = 'Medios Utilizados en Enriquecimiento Selectivo'
    _rec_name = 'display_name'
    _order = 'culture_media_batch_id, media_usage'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Lote del medio (siempre requerido)
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio',
        required=True,
        help='Lote específico del medio de cultivo utilizado'
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
    ], string='Uso del Medio', required=True, default='desarrollo_selectivo')
    
    # CAMPOS DE INCUBACIÓN
    requires_incubation = fields.Boolean(
        string='Requiere Incubación',
        default=True,  # Por defecto True para medios selectivos
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
    
    # NOTAS
    preparation_notes = fields.Text(
        string='Notas de Preparación',
        help='Instrucciones especiales, observaciones, etc.'
    )
    
    # CAMPOS CALCULADOS
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
    
    @api.depends('culture_media_batch_id', 'media_usage')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.culture_media_batch_id:
                media_name = record.culture_media_batch_id.culture_media_id.name
                batch_code = record.culture_media_batch_id.batch_code
                
                # Traducción del uso
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
                
                usage_display = usage_translations.get(record.media_usage, record.media_usage)
                name = f"{media_name} - {usage_display}"
                
                if batch_code:
                    name += f" (Lote: {batch_code})"
                    
                record.display_name = name
            else:
                record.display_name = "Medio sin especificar"
    
    @api.onchange('requires_incubation')
    def _onchange_requires_incubation(self):
        """Limpiar campos de incubación cuando no se requiere"""
        if not self.requires_incubation:
            self.incubation_equipment = False
            self.incubation_start_date = False
            self.incubation_start_time = False
            self.incubation_end_date = False
            self.incubation_end_time = False

class LimsQuantitativeMedia(models.Model):
    _name = 'lims.quantitative.media'
    _description = 'Medios Utilizados en Análisis Cuantitativos'
    _rec_name = 'display_name'
    _order = 'culture_media_batch_id, media_usage'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Lote del medio (siempre requerido)
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio',
        required=True,
        help='Lote específico del medio de cultivo utilizado'
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
    ], string='Uso del Medio', required=True, default='diluyente')
    
    # CAMPOS DE INCUBACIÓN
    requires_incubation = fields.Boolean(
        string='Requiere Incubación',
        default=True,  # Por defecto True para cuantitativos
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
    
    # NOTAS
    preparation_notes = fields.Text(
        string='Notas de Preparación',
        help='Instrucciones especiales, observaciones, etc.'
    )
    
    # CAMPOS CALCULADOS
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
    
    @api.depends('culture_media_batch_id', 'media_usage')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.culture_media_batch_id:
                media_name = record.culture_media_batch_id.culture_media_id.name
                batch_code = record.culture_media_batch_id.batch_code
                
                # Traducción del uso
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
                
                usage_display = usage_translations.get(record.media_usage, record.media_usage)
                name = f"{media_name} - {usage_display}"
                
                if batch_code:
                    name += f" (Lote: {batch_code})"
                    
                record.display_name = name
            else:
                record.display_name = "Medio sin especificar"
    
    @api.onchange('requires_incubation')
    def _onchange_requires_incubation(self):
        """Limpiar campos de incubación cuando no se requiere"""
        if not self.requires_incubation:
            self.incubation_equipment = False
            self.incubation_start_date = False
            self.incubation_start_time = False
            self.incubation_end_date = False
            self.incubation_end_time = False

class LimsConfirmationMedia(models.Model):
    _name = 'lims.confirmation.media'
    _description = 'Medios Utilizados en Confirmación'
    _rec_name = 'display_name'
    _order = 'culture_media_batch_id, media_usage'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Lote del medio (siempre requerido)
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio',
        required=True,
        help='Lote específico del medio de cultivo utilizado'
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
    ], string='Uso del Medio', required=True, default='pruebas_bioquimicas')
    
    # CAMPOS DE INCUBACIÓN
    requires_incubation = fields.Boolean(
        string='Requiere Incubación',
        default=True,  # Por defecto True para confirmación
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
    
    # NOTAS
    preparation_notes = fields.Text(
        string='Notas de Preparación',
        help='Instrucciones especiales, observaciones, etc.'
    )
    
    # CAMPOS CALCULADOS
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
    
    @api.depends('culture_media_batch_id', 'media_usage')
    def _compute_display_name(self):
        """Calcular nombre descriptivo"""
        for record in self:
            if record.culture_media_batch_id:
                media_name = record.culture_media_batch_id.culture_media_id.name
                batch_code = record.culture_media_batch_id.batch_code
                
                # Traducción del uso
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
                
                usage_display = usage_translations.get(record.media_usage, record.media_usage)
                name = f"{media_name} - {usage_display}"
                
                if batch_code:
                    name += f" (Lote: {batch_code})"
                    
                record.display_name = name
            else:
                record.display_name = "Medio sin especificar"
    
    @api.onchange('requires_incubation')
    def _onchange_requires_incubation(self):
        """Limpiar campos de incubación cuando no se requiere"""
        if not self.requires_incubation:
            self.incubation_equipment = False
            self.incubation_start_date = False
            self.incubation_start_time = False
            self.incubation_end_date = False
            self.incubation_end_time = False
    
    @api.onchange('culture_media_batch_id')
    def _onchange_culture_media_batch_id(self):
        """Actualizar resultados cuando cambia el lote"""
        if self.culture_media_batch_id and self.parameter_analysis_id:
            # Crear o actualizar resultado automáticamente
            self._sync_confirmation_result()
    
    def _sync_confirmation_result(self):
        """Sincronizar resultado de confirmación"""
        if not self.culture_media_batch_id or not self.parameter_analysis_id:
            return
            
        batch_display = f"{self.culture_media_batch_id.culture_media_id.name} (Lote: {self.culture_media_batch_id.batch_code})"
        
        # Buscar resultado existente
        existing_result = self.env['lims.confirmation.result'].search([
            ('confirmation_media_id', '=', self.id)
        ])
        
        if existing_result:
            # Actualizar existente
            existing_result.write({
                'batch_display_name': batch_display
            })
        else:
            # Crear nuevo si no existe
            if self.id:  # Solo si el registro ya está guardado
                self.env['lims.confirmation.result'].create({
                    'parameter_analysis_id': self.parameter_analysis_id.id,
                    'confirmation_media_id': self.id,
                    'batch_display_name': batch_display,
                })
    
    @api.model_create_multi
    def create(self, vals_list):
        """Crear registros de resultados automáticamente al crear medios"""
        records = super().create(vals_list)
        
        for record in records:
            try:
                # Verificar que tenemos el lote
                if record.culture_media_batch_id:
                    # Crear automáticamente un resultado para cada medio
                    batch_display = f"{record.culture_media_batch_id.culture_media_id.name} (Lote: {record.culture_media_batch_id.batch_code})"
                    
                    # Verificar si ya existe un resultado para este medio
                    existing_result = self.env['lims.confirmation.result'].search([
                        ('confirmation_media_id', '=', record.id)
                    ])
                    
                    if not existing_result:
                        result_vals = {
                            'parameter_analysis_id': record.parameter_analysis_id.id,
                            'confirmation_media_id': record.id,
                            'batch_display_name': batch_display,
                        }
                        
                        result = self.env['lims.confirmation.result'].create(result_vals)
                        print(f"DEBUG: Resultado creado: {result.id} - {batch_display}")
                    else:
                        print(f"DEBUG: Ya existe resultado para medio {record.id}")
                else:
                    print(f"DEBUG: No hay culture_media_batch_id para record {record.id}")
                    
            except Exception as e:
                print(f"DEBUG: Error creando resultado: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return records
    
    def write(self, vals):
        """Actualizar resultado cuando se modifica el medio"""
        result = super().write(vals)
        
        # Si se cambió el lote, actualizar el resultado
        if 'culture_media_batch_id' in vals:
            for record in self:
                try:
                    existing_result = self.env['lims.confirmation.result'].search([
                        ('confirmation_media_id', '=', record.id)
                    ])
                    
                    if existing_result and record.culture_media_batch_id:
                        batch_display = f"{record.culture_media_batch_id.culture_media_id.name} (Lote: {record.culture_media_batch_id.batch_code})"
                        existing_result.write({
                            'batch_display_name': batch_display
                        })
                        print(f"DEBUG: Resultado actualizado: {batch_display}")
                except Exception as e:
                    print(f"DEBUG: Error actualizando resultado: {str(e)}")
        
        return result
    
    def unlink(self):
        """Eliminar resultados asociados al eliminar medios"""
        try:
            # Eliminar resultados asociados
            results_to_delete = self.env['lims.confirmation.result'].search([
                ('confirmation_media_id', 'in', self.ids)
            ])
            
            if results_to_delete:
                print(f"DEBUG: Eliminando {len(results_to_delete)} resultados")
                results_to_delete.unlink()
        except Exception as e:
            print(f"DEBUG: Error eliminando resultados: {str(e)}")
        
        return super().unlink()


# 🆕 MODELO PARA RESULTADOS DE CONFIRMACIÓN - SIMPLIFICADO
class LimsConfirmationResult(models.Model):
    _name = 'lims.confirmation.result'
    _description = 'Resultados de Confirmación por Lote'
    _rec_name = 'batch_display_name'
    _order = 'batch_display_name'

    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    confirmation_media_id = fields.Many2one(
        'lims.confirmation.media',
        string='Medio de Confirmación',
        required=True,
        ondelete='cascade'
    )
    
    # Información del lote (copiada automáticamente)
    batch_display_name = fields.Char(
        string='Lote de Medio',
        required=True,
        readonly=True,
        help='Formato: "Nombre del Medio (Lote: Código)"'
    )
    
    # RESULTADO DEL CRECIMIENTO
    result = fields.Char(
        string='Resultado del Crecimiento',
        help='Resultado observado en este lote',
        placeholder='Ej: Positivo, Negativo, Crecimiento característico, cambio de color, etc.'
    )
    
    # Observaciones adicionales
    observations = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales sobre este resultado'
    )

class LimsExecutedQualityControl(models.Model):
    _name = 'lims.executed.quality.control'
    _description = 'Controles de Calidad Ejecutados en Análisis'
    _rec_name = 'display_name'
    _order = 'sequence, execution_date desc'

    # Relación con el parámetro de análisis
    parameter_analysis_id = fields.Many2one(
        'lims.parameter.analysis',
        string='Parámetro de Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Tipo de control de calidad (copiado desde la plantilla)
    qc_type_id = fields.Many2one(
        'lims.quality.control.type',
        string='Tipo de Control',
        required=True,
        help='Tipo de control de calidad a ejecutar'
    )
    
    # INFORMACIÓN DEL CONTROL (precargada desde plantilla)
    expected_result = fields.Char(
        string='Resultado Esperado',
        required=True,
        help='Resultado que debe obtenerse si el control es exitoso'
    )
    
    actual_result = fields.Char(
        string='Resultado Obtenido',
        help='Resultado real obtenido en el control'
    )
    
    # ESTADO DEL CONTROL
    control_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('passed', 'Exitoso'),
        ('failed', 'Falló'),
        ('not_applicable', 'No Aplica')
    ], string='Estado del Control', default='pending', required=True)
    
    # FECHAS Y SEGUIMIENTO
    execution_date = fields.Date(
        string='Fecha de Ejecución',
        help='Fecha en que se ejecutó el control'
    )
    
    execution_time = fields.Char(
        string='Hora de Ejecución',
        help='Formato HH:MM'
    )
    
    # RESPONSABLE
    executed_by = fields.Many2one(
        'res.users',
        string='Ejecutado por',
        help='Usuario que ejecutó el control de calidad'
    )
    
    # DETALLES TÉCNICOS
    method_used = fields.Char(
        string='Método Utilizado',
        help='Método o procedimiento específico utilizado'
    )
    
    equipment_used = fields.Many2one(
        'lims.lab.equipment',
        string='Equipo Utilizado',
        help='Equipo de laboratorio utilizado para el control'
    )
    
    # LOTE DE MEDIO UTILIZADO (si aplica)
    culture_media_batch_id = fields.Many2one(
        'lims.culture.media.batch',
        string='Lote de Medio Utilizado',
        help='Lote específico del medio utilizado en el control'
    )
    
    # OBSERVACIONES Y NOTAS
    notes = fields.Text(
        string='Notas y Observaciones',
        help='Observaciones adicionales sobre la ejecución del control'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de ejecución del control'
    )
    
    # CAMPOS COMPUTADOS
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
    
    # MÉTODOS DE ACCIÓN
    def action_start_control(self):
        """Iniciar el control de calidad"""
        self.write({
            'control_status': 'in_progress',
            'execution_date': fields.Date.context_today(self),
            'execution_time': fields.Datetime.now().strftime('%H:%M'),
            'executed_by': self.env.user.id
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Control Iniciado',
                'message': f'Control "{self.qc_type_id.name}" marcado como en proceso',
                'type': 'info',
            }
        }
    
    def action_mark_passed(self):
        """Marcar control como exitoso"""
        self.write({
            'control_status': 'passed',
            'execution_date': fields.Date.context_today(self),
            'execution_time': fields.Datetime.now().strftime('%H:%M'),
            'executed_by': self.env.user.id
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Control Exitoso',
                'message': f'Control "{self.qc_type_id.name}" marcado como exitoso ✅',
                'type': 'success',
            }
        }
    
    def action_mark_failed(self):
        """Marcar control como fallido"""
        self.write({
            'control_status': 'failed',
            'execution_date': fields.Date.context_today(self),
            'execution_time': fields.Datetime.now().strftime('%H:%M'),
            'executed_by': self.env.user.id
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Control Fallido',
                'message': f'Control "{self.qc_type_id.name}" marcado como fallido ❌',
                'type': 'warning',
            }
        }
    
    def action_reset_control(self):
        """Restablecer control a estado pendiente"""
        self.write({
            'control_status': 'pending',
            'actual_result': False,
            'execution_date': False,
            'execution_time': False,
            'executed_by': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Control Restablecido',
                'message': f'Control "{self.qc_type_id.name}" restablecido a pendiente',
                'type': 'info',
            }
        }
    
    @api.onchange('control_status')
    def _onchange_control_status(self):
        """Auto-llenar campos cuando cambia el estado"""
        if self.control_status in ['passed', 'failed'] and not self.execution_date:
            self.execution_date = fields.Date.context_today(self)
            self.execution_time = fields.Datetime.now().strftime('%H:%M')
            self.executed_by = self.env.user
    
    @api.onchange('qc_type_id')
    def _onchange_qc_type_id(self):
        """Auto-llenar resultado esperado desde el tipo de control"""
        if self.qc_type_id and self.qc_type_id.default_expected_result:
            self.expected_result = self.qc_type_id.default_expected_result