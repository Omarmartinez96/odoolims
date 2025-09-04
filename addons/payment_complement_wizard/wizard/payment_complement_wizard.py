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
            # Limpiar método de pago previo
            self.payment_method_line_id = False
            
            # Filtrar solo métodos de pago inbound disponibles para este journal
            domain = [
                ('journal_id', '=', self.journal_id.id),
                ('payment_type', '=', 'inbound')
            ]
            return {
                'domain': {
                    'payment_method_line_id': domain
                }
            }
        return {
            'domain': {'payment_method_line_id': []},
            'value': {'payment_method_line_id': False}
        }

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("El monto del pago debe ser positivo"))
            if rec.amount > rec.amount_residual:
                raise ValidationError(_("El monto del pago no puede exceder el saldo de la factura"))

    def action_generate_complement(self):
        """Genera pago usando el wizard nativo de Odoo"""
        self.ensure_one()
        
        try:
            # Usar el wizard nativo de register payment
            ctx = {
                'active_model': 'account.move',
                'active_ids': [self.invoice_id.id],
                'active_id': self.invoice_id.id,
            }
            
            # Crear el wizard de registro de pago nativo
            payment_register = self.env['account.payment.register'].with_context(ctx).create({
                'amount': self.amount,
                'payment_date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
            })
            
            # Ejecutar el registro de pago (esto hace toda la reconciliación automática)
            result = payment_register.action_create_payments()
            
            # Opcional: Obtener el pago creado para futuras operaciones
            # payment_id = result.get('res_id') if result else None
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('¡Éxito!'),
                    'message': _('Pago registrado y reconciliado exitosamente para la factura %s') % self.invoice_id.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error("Error generando pago con wizard nativo: %s", str(e))
            raise UserError(_('Error generando pago: %s') % str(e))