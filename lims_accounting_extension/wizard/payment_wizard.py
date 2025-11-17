from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PaymentWizard(models.TransientModel):
    _name = 'payment.wizard'
    _description = 'Asistente de Complementos PPD'

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura PPD',
        required=True,
        domain=[
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('l10n_mx_edi_payment_method_id', '=', 'PPD'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]
    )
    amount = fields.Float(
        string='Monto Recibido',
        required=True
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        required=True,
        default=fields.Date.context_today
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Forma de Pago',
        required=True,
        domain=[('type', 'in', ['bank', 'cash'])]
    )
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método',
        required=True
    )
    
    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            return {
                'domain': {
                    'payment_method_line_id': [('journal_id', '=', self.journal_id.id)]
                }
            }
        return {'domain': {'payment_method_line_id': []}}
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_residual

    def action_register_payment(self):
        """Registrar pago y generar complemento PPD automáticamente"""
        self.ensure_one()
        
        try:
            # Validaciones previas según manual (Sección 5.2)
            if not self.invoice_id.partner_id.vat:
                raise UserError(_('Error: El cliente debe tener RFC configurado para generar complementos CFDI'))
            
            if not self.invoice_id.partner_id.zip:
                raise UserError(_('Error: El cliente debe tener código postal configurado'))
                
            if not self.invoice_id.partner_id.country_id:
                raise UserError(_('Error: El cliente debe tener país configurado'))
                
            if self.amount <= 0:
                raise UserError(_('Error: El monto debe ser mayor a cero'))
                
            if self.amount > self.invoice_id.amount_residual:
                raise UserError(_('Error: El monto ($%s) no puede ser mayor al saldo pendiente ($%s)') % 
                              (self.amount, self.invoice_id.amount_residual))
            
            # Verificar que sea factura PPD
            payment_method = self.invoice_id.l10n_mx_edi_payment_method_id
            if not payment_method or payment_method.code not in ['PPD', '02']:
                current_method = payment_method.code if payment_method else 'Sin definir'
                raise UserError(_('Error: Solo se pueden generar complementos para facturas PPD. Método actual: %s') % current_method)
            
            # Paso 1: Crear contexto para wizard nativo
            ctx = {
                'active_model': 'account.move',
                'active_ids': [self.invoice_id.id],
                'active_id': self.invoice_id.id,
            }
            
            # Paso 2: Crear wizard de registro de pago nativo
            payment_register = self.env['account.payment.register'].with_context(ctx).create({
                'amount': self.amount,
                'payment_date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
            })
            
            # Paso 3: Ejecutar registro de pago (genera PPAGO automáticamente)
            result = payment_register.action_create_payments()
            
            # Paso 4: Forzar actualización de documentos EDI si es necesario
            self.invoice_id.flush()
            
            # Buscar si se generó el documento PPAGO (sin filtro de tiempo)
            ppago_docs = self.env['l10n_mx_edi.document'].search([
                ('move_id.ref', 'like', self.invoice_id.name),
                ('document_type', '=', 'payment')
            ], limit=1, order='create_date desc')
            
            # Paso 5: Si no se generó automáticamente, forzar actualización
            if not ppago_docs:
                try:
                    self.invoice_id.l10n_mx_edi_update_sat_status()
                except Exception as e:
                    # No fallar si hay error en la actualización, solo advertir
                    pass
            
            # Paso 6: Mensaje de éxito con instrucciones
            message = _(
                'Pago registrado exitosamente para factura %s.\n\n'
                'Para verificar el complemento CFDI:\n'
                '• Ir a Contabilidad → Configuración → Documentos EDI\n'
                '• Buscar documentos tipo "payment" recientes\n'
                '• O revisar la pestaña CFDI en la factura'
            ) % self.invoice_id.name
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Complemento PPD Procesado'),
                    'message': message,
                    'type': 'success',
                    'sticky': True,
                }
            }
            
        except UserError:
            # Re-lanzar errores de validación tal como están
            raise
            
        except Exception as e:
            # Capturar otros errores y dar mensaje más claro
            error_msg = str(e)
            if 'RPC_ERROR' in error_msg:
                error_msg = _('Error de comunicación. Intente refrescar la página (Ctrl+F5) y volver a intentar.')
            elif 'timeout' in error_msg.lower():
                error_msg = _('Tiempo de espera agotado. El pago puede haberse registrado. Verifique en Documentos EDI.')
            
            raise UserError(_('Error procesando complemento: %s') % error_msg)