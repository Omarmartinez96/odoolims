from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PaymentComplementWizard(models.TransientModel):
    _name = 'payment.complement.wizard'
    _description = 'Payment Complement Wizard'

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        domain=[('move_type', '=', 'out_invoice'), ('payment_state', '!=', 'paid')]
    )
    amount = fields.Float(
        string='Payment Amount',
        required=True,
        digits='Product Price'
    )
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        required=True,
        domain=[('type', 'in', ('bank', 'cash'))]
    )
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Payment Method',
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='invoice_id.currency_id',
        readonly=True
    )
    amount_residual = fields.Monetary(
        string='Amount Due',
        related='invoice_id.amount_residual',
        readonly=True
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

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Payment amount must be positive"))
            if rec.amount > rec.amount_residual:
                raise ValidationError(_("Payment amount cannot exceed the invoice balance"))
            
    def action_generate_complement(self):
        """Generate payment and complement in one action"""
        self.ensure_one()
        
        try:
            # Step 1: Create payment using native API
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.invoice_id.partner_id.id,
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
                'ref': _('Payment for %s') % self.invoice_id.name,
            }
            
            payment = self.env['account.payment'].create(payment_vals)
            
            # Step 2: Post payment using native method
            payment.action_post()
            
            # Step 3: Reconcile with invoice using native reconciliation
            self._reconcile_payment_with_invoice(payment)
            
            # Step 4: Generate CFDI complement using Mexican localization
            self._generate_cfdi_complement(payment)
            
            # Step 5: Show success message and close wizard
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('Payment complement generated successfully for invoice %s') % self.invoice_id.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error("Error generating payment complement: %s", str(e))
            raise UserError(_('Error generating payment complement: %s') % str(e))

    def _reconcile_payment_with_invoice(self, payment):
        """Reconcile payment with invoice using native Odoo methods"""
        # Get invoice receivable lines
        invoice_lines = self.invoice_id.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        # Get payment lines  
        payment_lines = payment.line_ids.filtered(
            lambda line: line.account_id.account_type == 'asset_receivable'
        )
        
        # Reconcile using native method
        lines_to_reconcile = invoice_lines + payment_lines
        lines_to_reconcile.reconcile()

    def _generate_cfdi_complement(self, payment):
        """Generate CFDI complement using Mexican localization"""
        # This uses the native l10n_mx_edi methods
        if hasattr(payment, '_l10n_mx_edi_cfdi_payment_complement'):
            payment._l10n_mx_edi_cfdi_payment_complement()
        else:
            # Alternative method for CFDI generation
            payment.l10n_mx_edi_update_sat_status()