from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LimsSampleSignatureWizardV2(models.TransientModel):
    _name = 'lims.sample.signature.wizard.v2'
    _description = 'Wizard para Firmar Muestra v2'

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
    
    parameters_count = fields.Integer(
        string='Parámetros a Marcar',
        readonly=True
    )
    
    # ===============================================
    # === INFORMACIÓN DEL FIRMANTE ===
    # ===============================================
    signature_name = fields.Char(
        string='Nombre del Firmante',
        required=True,
        default=lambda self: self.env.user.name,
        help='Nombre completo de la persona que firma'
    )
    
    signature_position = fields.Char(
        string='Cargo',
        required=True,
        default='Analista',
        help='Cargo o posición en el laboratorio'
    )
    
    # ===============================================
    # === FIRMA DIGITAL ===
    # ===============================================
    digital_signature = fields.Binary(
        string='Firma Digital',
        required=True,
        help='Captura de la firma digital'
    )
    
    # ===============================================
    # === INFORMACIÓN ADICIONAL ===
    # ===============================================
    signature_notes = fields.Text(
        string='Notas de Firma',
        help='Observaciones adicionales sobre la firma'
    )
    
    # ===============================================
    # === CAMPOS COMPUTADOS PARA MOSTRAR INFO ===
    # ===============================================
    analysis_info = fields.Html(
        string='Información del Análisis',
        compute='_compute_analysis_info',
        help='Resumen del análisis a firmar'
    )
    
    finalized_parameters = fields.Text(
        string='Parámetros Finalizados',
        compute='_compute_finalized_parameters',
        help='Lista de parámetros que serán marcados como listos'
    )
    
    # ===============================================
    # === VALIDACIONES ===
    # ===============================================
    can_sign = fields.Boolean(
        string='Puede Firmar',
        compute='_compute_can_sign',
        help='Indica si se puede proceder con la firma'
    )
    
    validation_message = fields.Text(
        string='Mensaje de Validación',
        compute='_compute_can_sign',
        help='Mensajes de validación o advertencias'
    )

    # ===============================================
    # === MÉTODOS COMPUTADOS ===
    # ===============================================
    @api.depends('analysis_id')
    def _compute_analysis_info(self):
        """Generar información HTML del análisis"""
        for wizard in self:
            if wizard.analysis_id:
                analysis = wizard.analysis_id
                
                # Crear HTML informativo
                html_content = f"""
                <div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin: 10px 0;">
                    <h4 style="color: #2c5aa0; margin-top: 0;">📋 Información del Análisis</h4>
                    <table style="width: 100%; font-size: 12px;">
                        <tr>
                            <td style="padding: 3px;"><strong>Muestra:</strong></td>
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
                            <td style="padding: 3px;"><strong>Total Parámetros:</strong></td>
                            <td style="padding: 3px;">{analysis.total_parameters_count}</td>
                        </tr>
                        <tr>
                            <td style="padding: 3px;"><strong>Estado Actual:</strong></td>
                            <td style="padding: 3px;">{dict(analysis._fields['analysis_state'].selection).get(analysis.analysis_state, analysis.analysis_state)}</td>
                        </tr>
                    </table>
                </div>
                """
                
                wizard.analysis_info = html_content
            else:
                wizard.analysis_info = "<p>No hay análisis seleccionado</p>"
    
    @api.depends('analysis_id')
    def _compute_finalized_parameters(self):
        """Mostrar lista de parámetros finalizados"""
        for wizard in self:
            if wizard.analysis_id:
                finalized_params = wizard.analysis_id.parameter_analysis_ids.filtered(
                    lambda p: p.analysis_status == 'completed'
                )
                
                if finalized_params:
                    param_list = []
                    for param in finalized_params:
                        result = param.result_value or 'Sin resultado'
                        param_list.append(f"• {param.name}: {result}")
                    
                    wizard.finalized_parameters = "\n".join(param_list)
                else:
                    wizard.finalized_parameters = "No hay parámetros finalizados para firmar."
            else:
                wizard.finalized_parameters = ""
    
    @api.depends('analysis_id', 'signature_name', 'digital_signature')
    def _compute_can_sign(self):
        """Validar si se puede proceder con la firma"""
        for wizard in self:
            messages = []
            can_sign = True
            
            # Validar análisis
            if not wizard.analysis_id:
                messages.append("❌ No hay análisis seleccionado")
                can_sign = False
            else:
                # Validar que hay parámetros finalizados
                finalized_params = wizard.analysis_id.parameter_analysis_ids.filtered(
                    lambda p: p.analysis_status == 'completed'
                )
                
                if not finalized_params:
                    messages.append("❌ No hay parámetros finalizados para firmar")
                    can_sign = False
                else:
                    messages.append(f"✅ {len(finalized_params)} parámetros listos para firmar")
                
                # Validar estado de firma
                if wizard.analysis_id.signature_state != 'not_signed':
                    messages.append("❌ Esta muestra ya está firmada o cancelada")
                    can_sign = False
                else:
                    messages.append("✅ Muestra lista para firmar")
            
            # Validar campos requeridos
            if not wizard.signature_name:
                messages.append("❌ Falta nombre del firmante")
                can_sign = False
            
            if not wizard.digital_signature:
                messages.append("❌ Falta firma digital")
                can_sign = False
            
            if can_sign:
                messages.append("🎯 Todo listo para proceder con la firma")
            
            wizard.can_sign = can_sign
            wizard.validation_message = "\n".join(messages)

    # ===============================================
    # === MÉTODOS DE ACCIÓN ===
    # ===============================================
    def action_confirm_signature(self):
        """Confirmar la firma"""
        self.ensure_one()
        
        # Validación final
        if not self.can_sign:
            raise UserError(f'No se puede proceder con la firma:\n{self.validation_message}')
        
        if not self.digital_signature:
            raise UserError('Debe proporcionar una firma digital.')
        
        if not self.signature_name or not self.signature_position:
            raise UserError('Debe completar el nombre y cargo del firmante.')
        
        # Preparar datos de firma
        signature_data = {
            'signature_name': self.signature_name,
            'signature_position': self.signature_position,
            'digital_signature': self.digital_signature,
            'signature_notes': self.signature_notes or '',
        }
        
        try:
            # Ejecutar firma en el análisis
            result = self.analysis_id.confirm_sample_signature(signature_data)
            
            if result:
                _logger.info(f"Firma exitosa para muestra {self.sample_code} por {self.signature_name}")
                
                # Mostrar notificación de éxito
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ Firma Exitosa',
                        'message': f'La muestra {self.sample_code} ha sido firmada exitosamente. '
                                 f'{self.parameters_count} parámetros marcados como listos para reporte.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError('Error al confirmar la firma. Intente nuevamente.')
                
        except Exception as e:
            _logger.error(f"Error al firmar muestra {self.sample_code}: {str(e)}")
            raise UserError(f'Error al procesar la firma: {str(e)}')
    
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
                # Contar parámetros finalizados
                finalized_params = analysis.parameter_analysis_ids.filtered(
                    lambda p: p.analysis_status == 'completed'
                )
                
                defaults.update({
                    'analysis_id': analysis.id,
                    'sample_code': analysis.sample_code,
                    'sample_identifier': analysis.sample_identifier,
                    'parameters_count': len(finalized_params),
                })
        
        return defaults
    
    # ===============================================
    # === MÉTODOS ONCHANGE ===
    # ===============================================
    @api.onchange('signature_name')
    def _onchange_signature_name(self):
        """Auto-completar información cuando cambia el nombre"""
        if self.signature_name:
            # Buscar usuario con ese nombre para auto-completar cargo
            user = self.env['res.users'].search([
                ('name', 'ilike', self.signature_name)
            ], limit=1)
            
            if user and not self.signature_position:
                # Intentar obtener cargo desde el usuario
                if user.function:
                    self.signature_position = user.function
                else:
                    self.signature_position = 'Analista'  # Valor por defecto
    
    @api.onchange('analysis_id')
    def _onchange_analysis_id(self):
        """Actualizar información cuando cambia el análisis"""
        if self.analysis_id:
            finalized_params = self.analysis_id.parameter_analysis_ids.filtered(
                lambda p: p.analysis_status == 'completed'
            )
            
            self.sample_code = self.analysis_id.sample_code
            self.sample_identifier = self.analysis_id.sample_identifier
            self.parameters_count = len(finalized_params)
        else:
            self.sample_code = False
            self.sample_identifier = False
            self.parameters_count = 0
    
    # ===============================================
    # === MÉTODOS DE VALIDACIÓN ===
    # ===============================================
    @api.constrains('signature_name', 'signature_position')
    def _check_signature_data(self):
        """Validar datos de firma"""
        for wizard in self:
            if wizard.signature_name and len(wizard.signature_name.strip()) < 3:
                raise UserError('El nombre del firmante debe tener al menos 3 caracteres.')
            
            if wizard.signature_position and len(wizard.signature_position.strip()) < 3:
                raise UserError('El cargo debe tener al menos 3 caracteres.')
    
    # ===============================================
    # === MÉTODOS AUXILIARES ===
    # ===============================================
    def _get_finalized_parameters_info(self):
        """Obtener información detallada de parámetros finalizados"""
        self.ensure_one()
        
        if not self.analysis_id:
            return []
        
        finalized_params = self.analysis_id.parameter_analysis_ids.filtered(
            lambda p: p.analysis_status == 'completed'
        )
        
        params_info = []
        for param in finalized_params:
            params_info.append({
                'name': param.name,
                'microorganism': param.microorganism,
                'result': param.result_value or 'Sin resultado',
                'method': param.method,
                'analyst': param.analyst_names,
            })
        
        return params_info