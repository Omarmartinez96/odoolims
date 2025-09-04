from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PaymentComplementWizard(models.TransientModel):
    _name = 'payment.complement.wizard'
    _description = 'Asistente de Complementos de Pago'

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        domain=[
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]
    )
    amount = fields.Float(
        string='Monto del Pago',
        required=True,
        digits='Product Price'
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        required=True,
        default=fields.Date.context_today
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario de Pago',
        required=True,
        domain=[('type', 'in', ('bank', 'cash'))]
    )
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método de Pago',
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='invoice_id.currency_id',
        readonly=True
    )
    amount_residual = fields.Monetary(
        string='Saldo Pendiente',
        related='invoice_id.amount_residual',
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Si viene del contexto de una factura específica
        if self.env.context.get('active_model') == 'account.move':
            invoice_id = self.env.context.get('active_id')
            if invoice_id:
                res['invoice_id'] = invoice_id
        return res

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            return {
                'domain': {
                    'payment_method_line_id': [('journal_id', '=', self.journal_id.id)]
                }
            }
        return {'domain': {'payment_method_line_id': []}}

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("El monto del pago debe ser positivo"))
            if rec.amount > rec.amount_residual:
                raise ValidationError(_("El monto del pago no puede exceder el saldo de la factura"))

    def action_generate_complement(self):
        """Genera pago y complemento en una sola acción"""
        self.ensure_one()
        
        try:
            # Paso 1: Crear pago usando API nativa
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.invoice_id.partner_id.id,
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
                'ref': _('Pago para %s') % self.invoice_id.name,
            }
            
            payment = self.env['account.payment'].create(payment_vals)
            
            # Paso 2: Procesar pago usando método nativo
            payment.action_post()
            
            # Paso 3: Conciliar con factura usando reconciliación nativa
            self._reconcile_payment_with_invoice(payment)
            
            # Paso 4: Generar complemento CFDI usando localización mexicana
            self._generate_cfdi_complement(payment)
            
            # Paso 5: Mostrar mensaje de éxito y cerrar asistente
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('¡Éxito!'),
                    'message': _('Complemento de pago generado exitosamente para la factura %s') % self.invoice_id.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error("Error generando complemento de pago: %s", str(e))
            raise UserError(_('Error generando complemento de pago: %s') % str(e))

    def _reconcile_payment_with_invoice(self, payment):
        """Conciliar pago con factura usando métodos nativos de Odoo"""
        # Obtener líneas por cobrar de la factura
        invoice_lines = self.invoice_id.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        # Obtener líneas del pago
        payment_lines = payment.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        # Conciliar usando método nativo
        lines_to_reconcile = invoice_lines + payment_lines
        lines_to_reconcile.reconcile()

    def _generate_cfdi_complement(self, payment):
        """Generar complemento CFDI usando localización mexicana"""
        # Esto usa los métodos nativos de l10n_mx_edi
        if hasattr(payment, '_l10n_mx_edi_cfdi_payment_complement'):
            payment._l10n_mx_edi_cfdi_payment_complement()
        else:
            # Método alternativo para generación CFDI
            payment.l10n_mx_edi_update_sat_status()