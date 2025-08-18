from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LimsAnalysisV2(models.Model):
    _name = 'lims.analysis.v2'
    _description = 'Análisis de Muestra v2'
    _rec_name = 'display_name'
    _order = 'custody_chain_code desc, reception_date desc, create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ===============================================
    # === RELACIONES PRINCIPALES ===
    # ===============================================
    sample_reception_id = fields.Many2one(
        'lims.sample.reception',
        string='Muestra Recibida',
        required=True,
        ondelete='cascade',
        domain=[('reception_state', '=', 'recibida')]
    )

    # ===============================================
    # === CAMPOS RELACIONADOS (INFORMACIÓN DE LA MUESTRA) ===
    # ===============================================
    sample_code = fields.Char(
        string='Código de Muestra',
        related='sample_reception_id.sample_code',
        readonly=True,
        store=True
    )
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

    # ===============================================
    # === INFORMACIÓN BÁSICA DEL ANÁLISIS ===
    # ===============================================
    display_name = fields.Char(
        string='Nombre del Análisis',
        compute='_compute_display_name',
        store=True
    )
    analysis_state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('validated', 'Validado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    # ===============================================
    # === FECHAS ===
    # ===============================================
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

    # ===============================================
    # === RELACIÓN CON PARÁMETROS DE ANÁLISIS ===
    # ===============================================
    parameter_analysis_ids = fields.One2many(
        'lims.parameter.analysis.v2',
        'analysis_id',
        string='Parámetros de Análisis'
    )

    # ===============================================
    # === ESTADÍSTICAS DE PARÁMETROS ===
    # ===============================================
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
    report_status_summary = fields.Char(
        string='Estado de Reporte',
        compute='_compute_report_status_summary',
        help='Resumen del estado de reporte de los parámetros'
    )

    # ===============================================
    # === SISTEMA DE FIRMAS ===
    # ===============================================
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
    sample_digital_signature = fields.Binary(
        string='Firma Digital de la Muestra',
        help='Firma digital capturada al firmar la muestra'
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

    # ===============================================
    # === SISTEMA DE REVISIONES ===
    # ===============================================
    revision_number = fields.Integer(
        string='Número de Revisión',
        default=0,
        help='Número de revisión del informe'
    )
    revision_reason = fields.Text(
        string='Motivo de Revisión',
        help='Razón por la cual se solicita la revisión'
    )
    revision_requested_by = fields.Char(
        string='Revisión Solicitada por',
        help='Persona o entidad que solicita la revisión'
    )
    revision_date = fields.Datetime(
        string='Fecha de Solicitud de Revisión'
    )
    is_revision = fields.Boolean(
        string='Es Revisión',
        default=False,
        help='Indica si este análisis es una revisión'
    )
    original_analysis_id = fields.Many2one(
        'lims.analysis.v2',
        string='Análisis Original',
        help='Referencia al análisis original si es revisión'
    )
    revision_ids = fields.One2many(
        'lims.analysis.v2',
        'original_analysis_id',
        string='Revisiones',
        help='Revisiones de este análisis'
    )
    revision_count = fields.Integer(
        string='Total Revisiones',
        compute='_compute_revision_count',
        help='Número total de revisiones'
    )

    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('sample_reception_id')
    def _compute_display_name(self):
        """Calcular nombre del análisis"""
        for analysis in self:
            if analysis.sample_code:
                analysis.display_name = f"Análisis - {analysis.sample_code}"
            else:
                analysis.display_name = "Análisis"

    @api.depends('parameter_analysis_ids.report_status')
    def _compute_report_readiness(self):
        """Calcular disponibilidad para reportes"""
        for analysis in self:
            all_params = analysis.parameter_analysis_ids
            ready_params = all_params.filtered(lambda p: p.report_status == 'ready')
            
            analysis.total_parameters_count = len(all_params)
            analysis.ready_parameters_count = len(ready_params)
            analysis.has_ready_parameters = len(ready_params) > 0
            analysis.all_parameters_ready = (
                len(ready_params) == len(all_params) 
                if all_params else False
            )

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
        """Determinar si se puede cancelar la firma"""
        for record in self:
            # TODO: Implementar grupos de seguridad cuando esté listo
            can_cancel = True  # Por ahora todos pueden cancelar
            record.can_cancel_signature = can_cancel and record.signature_state == 'signed'

    @api.depends('revision_ids')
    def _compute_revision_count(self):
        """Calcular número de revisiones"""
        for analysis in self:
            analysis.revision_count = len(analysis.revision_ids)

    # ===============================================
    # === MÉTODOS DE CREACIÓN ===
    # ===============================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create para copiar parámetros desde la muestra"""
        records = super().create(vals_list)
        
        for record in records:
            # Saltar creación automática si está en contexto especial
            if self.env.context.get('skip_auto_params'):
                continue
                
            # Obtener parámetros de la muestra
            if record.sample_reception_id and record.sample_reception_id.sample_id:
                sample = record.sample_reception_id.sample_id
                sample_parameters = sample.parameter_ids
                
                _logger.info(f"Creando parámetros para análisis {record.display_name}: {len(sample_parameters)} parámetros")
                
                # Crear parámetros de análisis
                for param in sample_parameters:
                    param_analysis = self.env['lims.parameter.analysis.v2'].create({
                        'analysis_id': record.id,
                        'parameter_id': param.id,
                        'name': param.name or 'Sin nombre',
                        'method': param.method or '',
                        'microorganism': param.microorganism or '',
                        'unit': param.unit or '',
                        'category': param.category or 'other',
                        'sequence': param.id,
                    })
                    
                    # Copiar controles de calidad
                    if param.quality_control_ids:
                        for qc in param.quality_control_ids:
                            self.env['lims.executed.quality.control.v2'].create({
                                'parameter_analysis_id': param_analysis.id,
                                'qc_type_id': qc.control_type_id.id,
                                'expected_result': qc.expected_result,
                                'control_status': 'pending',
                                'sequence': qc.sequence,
                                'notes': qc.notes or '',
                            })
        
        return records

    # ===============================================
    # === ACCIONES DEL ANÁLISIS ===
    # ===============================================
    def action_complete_analysis(self):
        """Completar análisis"""
        self.analysis_state = 'completed'
        self.analysis_end_date = fields.Date.context_today(self)
        return True

    # ===============================================
    # === SISTEMA DE FIRMAS ===
    # ===============================================
    def action_sign_sample(self):
        """Abrir wizard de firma"""
        finalized_params = self.parameter_analysis_ids.filtered(
            lambda p: p.analysis_status_checkbox == 'finalizado'
        )
        
        if not finalized_params:
            raise UserError('No hay parámetros finalizados para firmar.')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Firmar Muestra',
            'res_model': 'lims.sample.signature.wizard.v2',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_analysis_id': self.id,
                'default_sample_code': self.sample_code,
                'default_parameters_count': len(finalized_params),
            }
        }

    def confirm_sample_signature(self, signature_data):
        """Confirmar la firma (llamado desde wizard)"""
        finalized_params = self.parameter_analysis_ids.filtered(
            lambda p: p.analysis_status == 'completed'
        )
        
        self.write({
            'signature_state': 'signed',
            'sample_signature_name': signature_data.get('signature_name'),
            'sample_signature_position': signature_data.get('signature_position'),
            'sample_signature_date': fields.Datetime.now(),
            'sample_digital_signature': signature_data.get('digital_signature'),
        })
        
        # Marcar parámetros como listos
        finalized_params.write({'report_status': 'ready'})
        
        _logger.info(f"Muestra {self.sample_code} firmada por {signature_data.get('signature_name')}. "
                     f"{len(finalized_params)} parámetros marcados como listos para reporte.")
        
        return True

    def action_cancel_signature(self):
        """Cancelar firma"""
        self.write({
            'signature_state': 'cancelled',
            'signature_cancelled_by': self.env.user.name,
            'signature_cancelled_date': fields.Datetime.now(),
            'signature_cancellation_reason': 'Cancelación manual'
        })
        
        # Volver parámetros a estado draft
        self.parameter_analysis_ids.filtered(
            lambda p: p.report_status == 'ready'
        ).write({'report_status': 'draft'})
        
        _logger.info(f"Firma de muestra {self.sample_code} cancelada por {self.env.user.name}.")
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_undo_cancellation(self):
        """Deshacer cancelación de firma"""
        if self.signature_state != 'cancelled':
            raise UserError('Solo se puede deshacer la cancelación de firmas canceladas.')
        
        self.write({
            'signature_state': 'not_signed',
            'signature_cancelled_by': False,
            'signature_cancelled_date': False,
            'signature_cancellation_reason': False,
            'sample_signature_name': False,
            'sample_signature_position': False,
            'sample_signature_date': False,
            'sample_digital_signature': False,
        })
        
        _logger.info(f"Cancelación deshecha para muestra {self.sample_code}. Lista para firmar nuevamente.")
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # ===============================================
    # === SISTEMA DE REVISIONES ===
    # ===============================================
    def action_request_revision(self):
        """Solicitar revisión del informe"""
        if self.signature_state != 'signed':
            raise UserError('Solo se pueden revisar informes firmados.')
        
        return {
            'name': 'Solicitar Revisión de Informe',
            'type': 'ir.actions.act_window',
            'res_model': 'lims.revision.request.wizard.v2',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_analysis_id': self.id,
                'default_sample_code': self.sample_code,
                'default_current_revision': self.revision_number
            }
        }

    def create_revision(self, revision_data):
        """Crear revisión del análisis"""
        # Cancelar firma del análisis actual
        self.write({
            'signature_state': 'cancelled',
            'signature_cancelled_by': self.env.user.name,
            'signature_cancelled_date': fields.Datetime.now(),
            'signature_cancellation_reason': f"Revisión solicitada: {revision_data.get('reason', '')}"
        })
        
        # Volver parámetros a draft
        self.parameter_analysis_ids.write({'report_status': 'draft'})
        
        # Crear nueva revisión
        new_revision_number = self.revision_number + 1
        
        revision_vals = {
            'sample_reception_id': self.sample_reception_id.id,
            'is_revision': True,
            'revision_number': new_revision_number,
            'original_analysis_id': self.id,
            'revision_reason': revision_data.get('reason'),
            'revision_requested_by': revision_data.get('requested_by'),
            'revision_date': fields.Datetime.now(),
            'analysis_state': 'draft',
            'signature_state': 'not_signed',
            'analysis_start_date': self.analysis_start_date,
            'analysis_end_date': self.analysis_end_date,
        }
        
        revision = self.with_context(skip_auto_params=True).create(revision_vals)
        
        # Copiar todos los parámetros
        for param in self.parameter_analysis_ids:
            param_vals = param.copy_data()[0]
            param_vals.update({
                'analysis_id': revision.id,
                'report_status': 'draft',
            })
            self.env['lims.parameter.analysis.v2'].create(param_vals)

        _logger.info(f"Revisión {new_revision_number} creada para muestra {self.sample_code}")
        
        return revision

    # ===============================================
    # === REPORTES DINÁMICOS ===
    # ===============================================
    def generate_preliminary_report(self):
        """Generar reporte preliminar dinámico"""
        if not self.has_ready_parameters:
            raise UserError('No hay parámetros listos para reporte preliminar.')
        
        return self.env.ref('lims_analysis_v2.action_report_analysis_preliminary').report_action(self)

    def generate_final_report(self):
        """Generar reporte final dinámico"""
        if not self.all_parameters_ready:
            raise UserError('No todos los parámetros están listos para reporte final.')
        
        return self.env.ref('lims_analysis_v2.action_report_analysis_final').report_action(self)

    def generate_signing_report(self):
        """Generar reporte para firma manual"""
        if self.signature_state != 'signed':
            raise UserError('Solo se pueden generar reportes para firma manual de muestras ya firmadas digitalmente.')
        
        return self.env.ref('lims_analysis_v2.action_report_analysis_signing').report_action(self)

    # ===============================================
    # === ACCIONES MASIVAS ===
    # ===============================================
    @api.model
    def action_mass_print_preliminary_report(self, analysis_ids):
        """Acción masiva para reportes preliminares"""
        analyses = self.browse(analysis_ids)
        
        if not any(analysis.has_ready_parameters for analysis in analyses):
            raise UserError('Ningún análisis seleccionado tiene parámetros listos para reportar.')
        
        # Filtrar solo análisis con parámetros listos
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if len(ready_analyses) == 1:
            return ready_analyses.generate_preliminary_report()
        else:
            # Para múltiples análisis, generar reporte combinado
            return self.env.ref('lims_analysis_v2.action_report_analysis_preliminary').report_action(ready_analyses)

    @api.model
    def action_mass_print_final_report(self, analysis_ids):
        """Acción masiva para reportes finales"""
        analyses = self.browse(analysis_ids)
        
        if not any(analysis.all_parameters_ready for analysis in analyses):
            raise UserError('Ningún análisis seleccionado está completamente terminado.')
        
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if len(ready_analyses) == 1:
            return ready_analyses.generate_final_report()
        else:
            return self.env.ref('lims_analysis_v2.action_report_analysis_final').report_action(ready_analyses)

    @api.model
    def action_mass_print_report_for_signing(self, analysis_ids):
        """Acción masiva para reportes de firma manual"""
        analyses = self.browse(analysis_ids)
        
        signed_analyses = analyses.filtered(lambda a: a.signature_state == 'signed')
        if not signed_analyses:
            raise UserError('Solo se pueden imprimir reportes de muestras ya firmadas digitalmente.')
        
        if len(signed_analyses) == 1:
            return signed_analyses.generate_signing_report()
        else:
            return self.env.ref('lims_analysis_v2.action_report_analysis_signing').report_action(signed_analyses)

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

    # ===============================================
    # === LIMPIEZA DE REGISTROS ===
    # ===============================================
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

    def action_clean_orphan_records(self):
        """Acción manual para limpiar registros huérfanos"""
        all_analyses = self.search([])
        orphan_count = 0
        
        for analysis in all_analyses:
            try:
                if analysis.sample_reception_id:
                    reception_exists = analysis.sample_reception_id.exists()
                    if not reception_exists:
                        analysis.unlink()
                        orphan_count += 1
            except:
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
    
    # ===============================================
    # === NUEVO MÉTODO BASE PARA REPORTES PERSONALIZADOS ===
    # ===============================================
    @api.model
    def generate_custom_report(self, analysis_ids, report_config):
        """Generar reporte personalizado según configuración"""
        analyses = self.browse(analysis_ids)
        
        report_type = report_config.get('report_type', 'general_ilac')
        language = report_config.get('language', 'es')
        status = report_config.get('status', 'final')
        
        # Determinar templates específicos para cada tipo
        report_templates = {
            'bioburden': 'lims_analysis_v2.action_report_bioburden',
            'viable_particles': 'lims_analysis_v2.action_report_viable_particles',
            'endotoxin': 'lims_analysis_v2.action_report_endotoxin',
            'general_ilac': 'lims_analysis_v2.action_report_general_ilac',
            'general_no_ilac': 'lims_analysis_v2.action_report_general_no_ilac',
        }
        
        # Si no existe template específico, usar uno por defecto según el estado
        template_ref = report_templates.get(report_type)
        
        if not template_ref:
            if status == 'preliminary':
                template_ref = 'lims_analysis_v2.action_report_analysis_preliminary'
            else:
                template_ref = 'lims_analysis_v2.action_report_analysis_final'
        
        # Agregar contexto para el template
        context = {
            'report_type': report_type,
            'language': language,
            'status': status,
            'custom_report_config': report_config
        }
        
        return self.env.ref(template_ref).with_context(context).report_action(analyses)
    # ===============================================
    # === MÉTODOS ESPECÍFICOS PARA BIOBURDEN ===
    # ===============================================
    @api.model
    def action_mass_print_bioburden_final(self, analysis_ids):
        """Acción específica para Bioburden Final español"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if not ready_analyses:
            raise UserError('No hay análisis completados para reporte de Bioburden.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'final',
            'language': 'es',
            'report_type': 'bioburden'
        })

    @api.model  
    def action_mass_print_bioburden_preliminary(self, analysis_ids):
        """Acción específica para Bioburden Preliminar español"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if not ready_analyses:
            raise UserError('No hay análisis con parámetros listos para reporte preliminar de Bioburden.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'preliminary',
            'language': 'es',
            'report_type': 'bioburden'
        })
    
    # ===============================================
    # === MÉTODOS PARA PARTÍCULAS VIABLES ===
    # ===============================================
    @api.model
    def action_mass_print_viable_particles_final(self, analysis_ids):
        """Acción específica para Partículas Viables Final"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if not ready_analyses:
            raise UserError('No hay análisis completados para reporte de Partículas Viables.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'final',
            'language': 'es',
            'report_type': 'viable_particles'
        })

    @api.model  
    def action_mass_print_viable_particles_preliminary(self, analysis_ids):
        """Acción específica para Partículas Viables Preliminar"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if not ready_analyses:
            raise UserError('No hay análisis con parámetros listos para reporte preliminar de Partículas Viables.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'preliminary',
            'language': 'es',
            'report_type': 'viable_particles'
        })

    # ===============================================
    # === MÉTODOS PARA ENDOTOXINAS ===
    # ===============================================
    @api.model
    def action_mass_print_endotoxin_final(self, analysis_ids):
        """Acción específica para Endotoxinas Final"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if not ready_analyses:
            raise UserError('No hay análisis completados para reporte de Endotoxinas.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'final',
            'language': 'es',
            'report_type': 'endotoxin'
        })

    @api.model  
    def action_mass_print_endotoxin_preliminary(self, analysis_ids):
        """Acción específica para Endotoxinas Preliminar"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if not ready_analyses:
            raise UserError('No hay análisis con parámetros listos para reporte preliminar de Endotoxinas.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'preliminary',
            'language': 'es',
            'report_type': 'endotoxin'
        })

    # ===============================================
    # === MÉTODOS PARA GENERAL ILAC ===
    # ===============================================
    @api.model
    def action_mass_print_general_ilac_final(self, analysis_ids):
        """Acción específica para General ILAC Final"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if not ready_analyses:
            raise UserError('No hay análisis completados para reporte General ILAC.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'final',
            'language': 'es',
            'report_type': 'general_ilac'
        })

    @api.model  
    def action_mass_print_general_ilac_preliminary(self, analysis_ids):
        """Acción específica para General ILAC Preliminar"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if not ready_analyses:
            raise UserError('No hay análisis con parámetros listos para reporte preliminar General ILAC.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'preliminary',
            'language': 'es',
            'report_type': 'general_ilac'
        })

    # ===============================================
    # === MÉTODOS PARA GENERAL SIN ILAC ===
    # ===============================================
    @api.model
    def action_mass_print_general_no_ilac_final(self, analysis_ids):
        """Acción específica para General sin ILAC Final"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('all_parameters_ready')
        
        if not ready_analyses:
            raise UserError('No hay análisis completados para reporte General sin ILAC.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'final',
            'language': 'es',
            'report_type': 'general_no_ilac'
        })

    @api.model  
    def action_mass_print_general_no_ilac_preliminary(self, analysis_ids):
        """Acción específica para General sin ILAC Preliminar"""
        analyses = self.browse(analysis_ids)
        ready_analyses = analyses.filtered('has_ready_parameters')
        
        if not ready_analyses:
            raise UserError('No hay análisis con parámetros listos para reporte preliminar General sin ILAC.')
        
        return self.generate_custom_report(ready_analyses.ids, {
            'status': 'preliminary',
            'language': 'es',
            'report_type': 'general_no_ilac'
        })
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """Override search para forzar orden correcto"""
        if not order:
            order = 'custody_chain_code desc, reception_date desc, create_date desc'
        if not limit:
            limit = 30
        return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)