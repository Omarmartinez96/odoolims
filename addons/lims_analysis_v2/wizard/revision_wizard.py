from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LimsRevisionRequestWizardV2(models.TransientModel):
    _name = 'lims.revision.request.wizard.v2'
    _description = 'Wizard para Solicitar Revisión v2'

    # ===============================================
    # === INFORMACIÓN DEL ANÁLISIS ===
    # ===============================================
    analysis_id = fields.Many2one(
        'lims.analysis.v2',
        string='Análisis',
        required=True
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        readonly=True
    )
    
    sample_identifier = fields.Char(
        string='Identificación de Muestra',
        readonly=True
    )
    
    current_revision = fields.Integer(
        string='Revisión Actual',
        readonly=True
    )
    
    next_revision = fields.Integer(
        string='Nueva Revisión',
        compute='_compute_next_revision',
        help='Número que tendrá la nueva revisión'
    )
    
    # ===============================================
    # === INFORMACIÓN DE LA REVISIÓN ===
    # ===============================================
    requested_by = fields.Char(
        string='Solicitado por',
        required=True,
        help='Nombre del cliente o persona que solicita la revisión',
        default=lambda self: self.env.user.name
    )
    
    reason = fields.Text(
        string='Motivo de la Revisión',
        required=True,
        help='Describa detalladamente por qué se solicita la revisión'
    )
    
    urgency = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], string='Urgencia', default='medium', required=True,
       help='Nivel de urgencia de la revisión')
    
    revision_type = fields.Selection([
        ('correction', 'Corrección de Resultados'),
        ('addition', 'Adición de Parámetros'),
        ('method_change', 'Cambio de Método'),
        ('client_request', 'Solicitud del Cliente'),
        ('quality_issue', 'Problema de Calidad'),
        ('other', 'Otro')
    ], string='Tipo de Revisión', required=True,
       help='Categoría del motivo de revisión')
    
    # ===============================================
    # === INFORMACIÓN ADICIONAL ===
    # ===============================================
    client_reference = fields.Char(
        string='Referencia del Cliente',
        help='Número de referencia o ticket del cliente'
    )
    
    expected_delivery = fields.Date(
        string='Entrega Esperada',
        help='Fecha esperada para la entrega de la revisión'
    )
    
    internal_notes = fields.Text(
        string='Notas Internas',
        help='Notas internas del laboratorio (no visibles en reportes)'
    )
    
    # ===============================================
    # === CAMPOS COMPUTADOS INFORMATIVOS ===
    # ===============================================
    analysis_info = fields.Html(
        string='Información del Análisis',
        compute='_compute_analysis_info',
        help='Resumen del análisis a revisar'
    )
    
    current_parameters_info = fields.Text(
        string='Parámetros Actuales',
        compute='_compute_current_parameters_info',
        help='Lista de parámetros actuales con sus resultados'
    )
    
    can_create_revision = fields.Boolean(
        string='Puede Crear Revisión',
        compute='_compute_can_create_revision',
        help='Indica si se puede proceder con la revisión'
    )
    
    validation_message = fields.Text(
        string='Mensaje de Validación',
        compute='_compute_can_create_revision',
        help='Mensajes de validación o advertencias'
    )
    
    impact_warning = fields.Html(
        string='Advertencia de Impacto',
        compute='_compute_impact_warning',
        help='Advertencias sobre el impacto de crear la revisión'
    )

    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('current_revision')
    def _compute_next_revision(self):
        """Calcular número de la siguiente revisión"""
        for wizard in self:
            wizard.next_revision = wizard.current_revision + 1
    
    @api.depends('analysis_id')
    def _compute_analysis_info(self):
        """Generar información HTML del análisis"""
        for wizard in self:
            if wizard.analysis_id:
                analysis = wizard.analysis_id
                
                # Determinar estado de firma
                if analysis.signature_state == 'signed':
                    signature_status = '<span style="color: #28a745;">✅ Firmado</span>'
                elif analysis.signature_state == 'cancelled':
                    signature_status = '<span style="color: #dc3545;">❌ Cancelado</span>'
                else:
                    signature_status = '<span style="color: #6c757d;">⏳ Sin Firmar</span>'
                
                # Crear HTML informativo
                html_content = f"""
                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin: 10px 0;">
                    <h4 style="color: #2c5aa0; margin-top: 0;">📋 Análisis Actual</h4>
                    <table style="width: 100%; font-size: 12px;">
                        <tr>
                            <td style="padding: 3px; width: 30%;"><strong>Muestra:</strong></td>
                            <td style="padding: 3px;">{analysis.sample_code} - {analysis.sample_identifier}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Cliente:</strong></td>
                            <td style="padding: 3px;">{analysis.customer_id.name if analysis.customer_id else 'No especificado'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Cadena:</strong></td>
                            <td style="padding: 3px;">{analysis.custody_chain_code}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Estado de Firma:</strong></td>
                            <td style="padding: 3px;">{signature_status}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Parámetros:</strong></td>
                            <td style="padding: 3px;">{analysis.ready_parameters_count} listos de {analysis.total_parameters_count} total</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Revisión Actual:</strong></td>
                            <td style="padding: 3px;">N° {analysis.revision_number}</td>
                        </tr>
                    </table>
                </div>
                """
                
                wizard.analysis_info = html_content
            else:
                wizard.analysis_info = "<p>No hay análisis seleccionado</p>"
    
    @api.depends('analysis_id')
    def _compute_current_parameters_info(self):
        """Mostrar información de parámetros actuales"""
        for wizard in self:
            if wizard.analysis_id:
                params = wizard.analysis_id.parameter_analysis_ids
                
                if params:
                    param_list = []
                    for param in params:
                        status_map = {
                            'draft': '⏳ Borrador',
                            'in_progress': '🔄 En Proceso', 
                            'completed': '✅ Completado'
                        }
                        
                        report_map = {
                            'draft': '📝 En Proceso',
                            'ready': '📋 Listo',
                            'reported': '✅ Reportado'
                        }
                        
                        status = status_map.get(param.analysis_status, param.analysis_status)
                        report_status = report_map.get(param.report_status, param.report_status)
                        result = param.result_value or 'Sin resultado'
                        
                        param_list.append(f"• {param.name}: {result} [{status}] [{report_status}]")
                    
                    wizard.current_parameters_info = "\n".join(param_list)
                else:
                    wizard.current_parameters_info = "No hay parámetros en este análisis."
            else:
                wizard.current_parameters_info = ""
    
    @api.depends('analysis_id', 'requested_by', 'reason')
    def _compute_can_create_revision(self):
        """Validar si se puede crear la revisión"""
        for wizard in self:
            messages = []
            can_create = True
            
            # Validar análisis
            if not wizard.analysis_id:
                messages.append("❌ No hay análisis seleccionado")
                can_create = False
            else:
                # Validar estado de firma
                if wizard.analysis_id.signature_state != 'signed':
                    messages.append("❌ Solo se pueden revisar análisis firmados")
                    can_create = False
                else:
                    messages.append("✅ Análisis firmado - puede revisarse")
                
                # Información sobre parámetros
                ready_count = wizard.analysis_id.ready_parameters_count
                total_count = wizard.analysis_id.total_parameters_count
                
                if ready_count > 0:
                    messages.append(f"ℹ️ {ready_count} de {total_count} parámetros serán copiados")
                else:
                    messages.append("⚠️ No hay parámetros listos - se copiarán todos los datos")
            
            # Validar campos requeridos
            if not wizard.requested_by or len(wizard.requested_by.strip()) < 3:
                messages.append("❌ Debe especificar quién solicita la revisión")
                can_create = False
            
            if not wizard.reason or len(wizard.reason.strip()) < 10:
                messages.append("❌ El motivo debe tener al menos 10 caracteres")
                can_create = False
            
            if can_create:
                messages.append("🎯 Todo listo para crear la revisión")
            
            wizard.can_create_revision = can_create
            wizard.validation_message = "\n".join(messages)
    
    @api.depends('analysis_id', 'revision_type', 'urgency')
    def _compute_impact_warning(self):
        """Mostrar advertencias sobre el impacto de la revisión"""
        for wizard in self:
            if wizard.analysis_id:
                warnings = []
                
                # Advertencia general
                warnings.append("⚠️ <strong>IMPACTO DE LA REVISIÓN:</strong>")
                warnings.append("• Se cancelará la firma actual del análisis")
                warnings.append("• Los parámetros volverán a estado 'borrador'")
                warnings.append("• Se creará una nueva versión editable")
                warnings.append("• Se generará el número de revisión consecutivo")
                
                # Advertencias específicas por tipo
                if wizard.revision_type == 'correction':
                    warnings.append("• <span style='color: #dc3545;'>Los resultados actuales serán modificables</span>")
                elif wizard.revision_type == 'addition':
                    warnings.append("• <span style='color: #ffc107;'>Se podrán agregar nuevos parámetros</span>")
                elif wizard.revision_type == 'method_change':
                    warnings.append("• <span style='color: #17a2b8;'>Los métodos y procedimientos podrán cambiarse</span>")
                
                # Advertencias por urgencia
                if wizard.urgency == 'critical':
                    warnings.append("• <span style='color: #dc3545;'><strong>CRÍTICO:</strong> Requiere atención inmediata</span>")
                elif wizard.urgency == 'high':
                    warnings.append("• <span style='color: #ffc107;'><strong>ALTA:</strong> Prioridad elevada</span>")
                
                # Información sobre historial
                if wizard.analysis_id.revision_count > 0:
                    warnings.append(f"• Este análisis ya tiene {wizard.analysis_id.revision_count} revisión(es) previa(s)")
                
                html_content = f"""
                <div style="padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; margin: 10px 0;">
                    {"<br/>".join(warnings)}
                </div>
                """
                
                wizard.impact_warning = html_content
            else:
                wizard.impact_warning = ""

    # ===============================================
    # === MÉTODOS DE ACCIÓN ===
    # ===============================================
    def action_create_revision(self):
        """Crear la revisión"""
        self.ensure_one()
        
        # Validación final
        if not self.can_create_revision:
            raise UserError(f'No se puede crear la revisión:\n{self.validation_message}')
        
        if not self.reason or len(self.reason.strip()) < 10:
            raise UserError('El motivo de la revisión debe tener al menos 10 caracteres.')
        
        if not self.requested_by or len(self.requested_by.strip()) < 3:
            raise UserError('Debe especificar quién solicita la revisión.')
        
        # Preparar datos de revisión
        revision_data = {
            'requested_by': self.requested_by,
            'reason': self.reason,
            'urgency': self.urgency,
            'revision_type': self.revision_type,
            'client_reference': self.client_reference,
            'expected_delivery': self.expected_delivery,
            'internal_notes': self.internal_notes,
        }
        
        try:
            # Crear revisión
            revision = self.analysis_id.create_revision(revision_data)
            
            if revision:
                _logger.info(f"Revisión {revision.revision_number} creada para muestra {self.sample_code} "
                           f"solicitada por {self.requested_by}")
                
                # Abrir la nueva revisión
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'lims.analysis.v2',
                    'res_id': revision.id,
                    'view_mode': 'form',
                    'target': 'current',
                    'context': {
                        'form_view_initial_mode': 'edit'
                    },
                    'flags': {
                        'mode': 'edit'
                    }
                }
            else:
                raise UserError('Error al crear la revisión. Intente nuevamente.')
                
        except Exception as e:
            _logger.error(f"Error al crear revisión para muestra {self.sample_code}: {str(e)}")
            raise UserError(f'Error al crear la revisión: {str(e)}')
    
    def action_cancel(self):
        """Cancelar el wizard"""
        return {
            'type': 'ir.actions.act_window_close',
        }
    
    # ===============================================
    # === MÉTODOS DE INICIALIZACIÓN ===
    # ===============================================
    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto desde contexto"""
        defaults = super().default_get(fields_list)
        
        # Obtener ID del análisis desde contexto
        analysis_id = self.env.context.get('default_analysis_id')
        
        if analysis_id:
            analysis = self.env['lims.analysis.v2'].browse(analysis_id)
            
            if analysis.exists():
                defaults.update({
                    'analysis_id': analysis.id,
                    'sample_code': analysis.sample_code,
                    'sample_identifier': analysis.sample_identifier,
                    'current_revision': analysis.revision_number,
                })
        
        return defaults
    
    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('revision_type')
    def _onchange_revision_type(self):
        """Auto-completar campos según el tipo de revisión"""
        if self.revision_type:
            type_templates = {
                'correction': 'Corrección de resultados debido a ',
                'addition': 'Solicitud de análisis adicionales para ',
                'method_change': 'Cambio de método analítico para ',
                'client_request': 'Solicitud específica del cliente para ',
                'quality_issue': 'Problema de calidad identificado en ',
                'other': 'Revisión solicitada para ',
            }
            
            template = type_templates.get(self.revision_type, '')
            if template and not self.reason:
                self.reason = template + (self.sample_code or 'la muestra')
    
    @api.onchange('urgency')
    def _onchange_urgency(self):
        """Ajustar fecha esperada según urgencia"""
        if self.urgency and not self.expected_delivery:
            today = fields.Date.context_today(self)
            
            if self.urgency == 'critical':
                # 1 día para crítico
                self.expected_delivery = fields.Date.add(today, days=1)
            elif self.urgency == 'high':
                # 3 días para alta
                self.expected_delivery = fields.Date.add(today, days=3)
            elif self.urgency == 'medium':
                # 5 días para media
                self.expected_delivery = fields.Date.add(today, days=5)
            else:
                # 7 días para baja
                self.expected_delivery = fields.Date.add(today, days=7)
    
    @api.onchange('analysis_id')
    def _onchange_analysis_id(self):
        """Actualizar información cuando cambia el análisis"""
        if self.analysis_id:
            self.sample_code = self.analysis_id.sample_code
            self.sample_identifier = self.analysis_id.sample_identifier
            self.current_revision = self.analysis_id.revision_number
        else:
            self.sample_code = False
            self.sample_identifier = False
            self.current_revision = 0
    
    # ===============================================
    # === MÉTODOS DE VALIDACIÓN ===
    # ===============================================
    @api.constrains('reason')
    def _check_reason_length(self):
        """Validar longitud del motivo"""
        for wizard in self:
            if wizard.reason and len(wizard.reason.strip()) < 10:
                raise UserError('El motivo de la revisión debe tener al menos 10 caracteres.')
    
    @api.constrains('requested_by')
    def _check_requested_by(self):
        """Validar solicitante"""
        for wizard in self:
            if wizard.requested_by and len(wizard.requested_by.strip()) < 3:
                raise UserError('El nombre del solicitante debe tener al menos 3 caracteres.')
    
    # ===============================================
    # === MÉTODOS AUXILIARES ===
    # ===============================================
    def _get_revision_summary(self):
        """Obtener resumen de la revisión a crear"""
        self.ensure_one()
        
        return {
            'sample_code': self.sample_code,
            'current_revision': self.current_revision,
            'next_revision': self.next_revision,
            'requested_by': self.requested_by,
            'reason': self.reason,
            'urgency': self.urgency,
            'revision_type': self.revision_type,
            'expected_delivery': self.expected_delivery,
        }